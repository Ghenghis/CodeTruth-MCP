"""
Milestone 2: Evidence Vault with SQLite + SARIF Storage

The Evidence Vault is the core storage system for all audit findings.
Every finding must have verifiable evidence - no claims without proof.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of evidence that can be stored."""

    # Static Analysis
    LINT_ERROR = "lint_error"
    TYPE_ERROR = "type_error"
    SECURITY_VULN = "security_vuln"
    DEAD_CODE = "dead_code"
    UNWIRED_UI = "unwired_ui"
    CONTRACT_MISMATCH = "contract_mismatch"

    # Runtime Evidence
    TEST_FAILURE = "test_failure"
    COVERAGE_GAP = "coverage_gap"
    E2E_FAILURE = "e2e_failure"
    VISUAL_REGRESSION = "visual_regression"

    # Security
    SECRET_LEAK = "secret_leak"
    DEPENDENCY_VULN = "dependency_vuln"

    # Structural
    UNREACHABLE_CODE = "unreachable_code"
    ORPHAN_COMPONENT = "orphan_component"
    MISSING_ROUTE = "missing_route"
    UNBOUND_HANDLER = "unbound_handler"

    # Quality
    GATE_FAILURE = "gate_failure"
    BUILD_FAILURE = "build_failure"


class Severity(str, Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    INFO = "info"


class EvidenceLocation(BaseModel):
    """Location information for evidence."""

    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    start_column: int | None = None
    end_column: int | None = None
    snippet: str | None = None

    def to_sarif(self) -> dict[str, Any]:
        """Convert to SARIF location format."""
        location: dict[str, Any] = {
            "physicalLocation": {
                "artifactLocation": {"uri": self.file_path},
            }
        }

        if self.start_line is not None:
            region: dict[str, Any] = {"startLine": self.start_line}
            if self.end_line is not None:
                region["endLine"] = self.end_line
            if self.start_column is not None:
                region["startColumn"] = self.start_column
            if self.end_column is not None:
                region["endColumn"] = self.end_column
            if self.snippet:
                region["snippet"] = {"text": self.snippet}
            location["physicalLocation"]["region"] = region

        return location


class Evidence(BaseModel):
    """
    A single piece of evidence for an audit finding.

    Core principle: Every finding must have reproducible proof.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType
    severity: Severity
    message: str
    description: str | None = None

    # Location
    location: EvidenceLocation | None = None
    related_locations: list[EvidenceLocation] = Field(default_factory=list)

    # Proof artifacts
    tool_name: str  # Tool that produced this evidence
    tool_version: str | None = None
    rule_id: str | None = None  # Rule/check that triggered
    rule_name: str | None = None

    # Raw proof
    raw_output: str | None = None  # Original tool output
    command: str | None = None  # Command that was run
    exit_code: int | None = None

    # Trace artifacts
    trace_file: str | None = None  # Path to Playwright trace
    screenshot_file: str | None = None
    video_file: str | None = None
    har_file: str | None = None  # Network capture

    # Reachability proof
    call_path: list[str] | None = None  # Function call path
    entry_point: str | None = None  # How this code is reached

    # Metadata
    repo_path: str | None = None
    commit_sha: str | None = None
    branch: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Classification
    cwe_id: str | None = None  # CWE reference for security issues
    cve_id: str | None = None  # CVE reference
    owasp_category: str | None = None

    # Fix information
    suggested_fix: str | None = None
    fix_difficulty: str | None = None  # easy, medium, hard

    def content_hash(self) -> str:
        """Generate a hash of the evidence content for deduplication."""
        content = f"{self.evidence_type}:{self.location}:{self.message}:{self.rule_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_sarif_result(self) -> dict[str, Any]:
        """Convert to SARIF result format."""
        result: dict[str, Any] = {
            "ruleId": self.rule_id or self.evidence_type.value,
            "level": self._severity_to_sarif_level(),
            "message": {"text": self.message},
        }

        if self.location:
            result["locations"] = [self.location.to_sarif()]

        if self.related_locations:
            result["relatedLocations"] = [loc.to_sarif() for loc in self.related_locations]

        if self.suggested_fix:
            result["fixes"] = [
                {
                    "description": {"text": self.suggested_fix},
                }
            ]

        return result

    def _severity_to_sarif_level(self) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.ERROR: "error",
            Severity.WARNING: "warning",
            Severity.NOTE: "note",
            Severity.INFO: "none",
        }
        return mapping.get(self.severity, "warning")


class EvidenceVault:
    """
    SQLite-based storage for all audit evidence.

    Features:
    - SARIF-compatible storage
    - Full-text search
    - Evidence deduplication
    - Audit trail
    """

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize the database schema."""
        self._connection = await aiosqlite.connect(str(self.db_path))

        await self._connection.executescript(
            """
            -- Main evidence table
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                evidence_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                description TEXT,

                -- Location
                file_path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                start_column INTEGER,
                end_column INTEGER,
                snippet TEXT,

                -- Tool info
                tool_name TEXT NOT NULL,
                tool_version TEXT,
                rule_id TEXT,
                rule_name TEXT,

                -- Raw proof
                raw_output TEXT,
                command TEXT,
                exit_code INTEGER,

                -- Artifacts
                trace_file TEXT,
                screenshot_file TEXT,
                video_file TEXT,
                har_file TEXT,

                -- Reachability
                call_path TEXT,  -- JSON array
                entry_point TEXT,

                -- Repo info
                repo_path TEXT,
                commit_sha TEXT,
                branch TEXT,
                timestamp TEXT NOT NULL,

                -- Classification
                cwe_id TEXT,
                cve_id TEXT,
                owasp_category TEXT,

                -- Fix
                suggested_fix TEXT,
                fix_difficulty TEXT,

                -- Deduplication
                content_hash TEXT NOT NULL,

                -- Indexes
                UNIQUE(content_hash, repo_path, commit_sha)
            );

            CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);
            CREATE INDEX IF NOT EXISTS idx_evidence_severity ON evidence(severity);
            CREATE INDEX IF NOT EXISTS idx_evidence_repo ON evidence(repo_path);
            CREATE INDEX IF NOT EXISTS idx_evidence_file ON evidence(file_path);
            CREATE INDEX IF NOT EXISTS idx_evidence_rule ON evidence(rule_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence(timestamp);

            -- Audit runs table
            CREATE TABLE IF NOT EXISTS audit_runs (
                id TEXT PRIMARY KEY,
                repo_path TEXT NOT NULL,
                commit_sha TEXT,
                branch TEXT,
                profile TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,  -- running, completed, failed
                summary TEXT,  -- JSON summary
                gates_passed TEXT,  -- JSON array of passed gates
                total_findings INTEGER DEFAULT 0,
                critical_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_runs_repo ON audit_runs(repo_path);
            CREATE INDEX IF NOT EXISTS idx_runs_started ON audit_runs(started_at);

            -- Evidence to run mapping
            CREATE TABLE IF NOT EXISTS run_evidence (
                run_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                PRIMARY KEY (run_id, evidence_id),
                FOREIGN KEY (run_id) REFERENCES audit_runs(id),
                FOREIGN KEY (evidence_id) REFERENCES evidence(id)
            );

            -- Feature registry for truth table
            CREATE TABLE IF NOT EXISTS features (
                id TEXT PRIMARY KEY,
                repo_path TEXT NOT NULL,
                name TEXT NOT NULL,
                spec_source TEXT,  -- Where feature is defined
                feature_type TEXT,  -- ui, api, service, job, etc.
                status TEXT NOT NULL,  -- working, partial, stubbed, unwired, dead, broken
                execution_path TEXT,  -- JSON: UI -> API -> Service -> DB
                is_reachable BOOLEAN,
                is_observable BOOLEAN,
                test_name TEXT,
                test_assertions TEXT,
                blockers TEXT,  -- JSON array of blockers
                last_verified TEXT,
                UNIQUE(repo_path, name)
            );

            CREATE INDEX IF NOT EXISTS idx_features_repo ON features(repo_path);
            CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);

            -- Full-text search
            CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(
                message, description, snippet, suggested_fix,
                content=evidence, content_rowid=rowid
            );

            -- Triggers for FTS
            CREATE TRIGGER IF NOT EXISTS evidence_ai AFTER INSERT ON evidence BEGIN
                INSERT INTO evidence_fts(rowid, message, description, snippet, suggested_fix)
                VALUES (NEW.rowid, NEW.message, NEW.description, NEW.snippet, NEW.suggested_fix);
            END;
            """
        )

        await self._connection.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def store_evidence(self, evidence: Evidence) -> str:
        """Store evidence in the vault."""
        if not self._connection:
            await self.initialize()

        content_hash = evidence.content_hash()

        await self._connection.execute(
            """
            INSERT OR REPLACE INTO evidence (
                id, evidence_type, severity, message, description,
                file_path, start_line, end_line, start_column, end_column, snippet,
                tool_name, tool_version, rule_id, rule_name,
                raw_output, command, exit_code,
                trace_file, screenshot_file, video_file, har_file,
                call_path, entry_point,
                repo_path, commit_sha, branch, timestamp,
                cwe_id, cve_id, owasp_category,
                suggested_fix, fix_difficulty,
                content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence.id,
                evidence.evidence_type.value,
                evidence.severity.value,
                evidence.message,
                evidence.description,
                evidence.location.file_path if evidence.location else None,
                evidence.location.start_line if evidence.location else None,
                evidence.location.end_line if evidence.location else None,
                evidence.location.start_column if evidence.location else None,
                evidence.location.end_column if evidence.location else None,
                evidence.location.snippet if evidence.location else None,
                evidence.tool_name,
                evidence.tool_version,
                evidence.rule_id,
                evidence.rule_name,
                evidence.raw_output,
                evidence.command,
                evidence.exit_code,
                evidence.trace_file,
                evidence.screenshot_file,
                evidence.video_file,
                evidence.har_file,
                json.dumps(evidence.call_path) if evidence.call_path else None,
                evidence.entry_point,
                evidence.repo_path,
                evidence.commit_sha,
                evidence.branch,
                evidence.timestamp.isoformat(),
                evidence.cwe_id,
                evidence.cve_id,
                evidence.owasp_category,
                evidence.suggested_fix,
                evidence.fix_difficulty,
                content_hash,
            ),
        )

        await self._connection.commit()
        return evidence.id

    async def store_many(self, evidences: list[Evidence]) -> list[str]:
        """Store multiple evidence records."""
        ids = []
        for evidence in evidences:
            evidence_id = await self.store_evidence(evidence)
            ids.append(evidence_id)
        return ids

    async def get_evidence(self, evidence_id: str) -> Evidence | None:
        """Retrieve evidence by ID."""
        if not self._connection:
            await self.initialize()

        cursor = await self._connection.execute(
            "SELECT * FROM evidence WHERE id = ?", (evidence_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_evidence(row, cursor.description)

    async def search(
        self,
        repo_path: str | None = None,
        evidence_type: EvidenceType | None = None,
        severity: Severity | None = None,
        file_path: str | None = None,
        rule_id: str | None = None,
        text_query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Evidence]:
        """Search for evidence with filters."""
        if not self._connection:
            await self.initialize()

        conditions = []
        params: list[Any] = []

        if repo_path:
            conditions.append("repo_path = ?")
            params.append(repo_path)

        if evidence_type:
            conditions.append("evidence_type = ?")
            params.append(evidence_type.value)

        if severity:
            conditions.append("severity = ?")
            params.append(severity.value)

        if file_path:
            conditions.append("file_path LIKE ?")
            params.append(f"%{file_path}%")

        if rule_id:
            conditions.append("rule_id = ?")
            params.append(rule_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        if text_query:
            # Use FTS for text search
            query = f"""
                SELECT e.* FROM evidence e
                JOIN evidence_fts fts ON e.rowid = fts.rowid
                WHERE {where_clause} AND evidence_fts MATCH ?
                ORDER BY e.timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([text_query, limit, offset])
        else:
            query = f"""
                SELECT * FROM evidence
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_evidence(row, cursor.description) for row in rows]

    async def get_summary(self, repo_path: str) -> dict[str, Any]:
        """Get a summary of evidence for a repository."""
        if not self._connection:
            await self.initialize()

        cursor = await self._connection.execute(
            """
            SELECT
                evidence_type,
                severity,
                COUNT(*) as count
            FROM evidence
            WHERE repo_path = ?
            GROUP BY evidence_type, severity
            ORDER BY severity, evidence_type
            """,
            (repo_path,),
        )

        rows = await cursor.fetchall()

        summary: dict[str, Any] = {
            "total": 0,
            "by_severity": {"critical": 0, "error": 0, "warning": 0, "note": 0, "info": 0},
            "by_type": {},
        }

        for row in rows:
            evidence_type, severity, count = row
            summary["total"] += count
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + count

            if evidence_type not in summary["by_type"]:
                summary["by_type"][evidence_type] = {}
            summary["by_type"][evidence_type][severity] = count

        return summary

    async def export_sarif(self, repo_path: str, output_path: Path) -> None:
        """Export evidence as SARIF format."""
        evidences = await self.search(repo_path=repo_path, limit=10000)

        # Group by tool
        by_tool: dict[str, list[Evidence]] = {}
        for e in evidences:
            if e.tool_name not in by_tool:
                by_tool[e.tool_name] = []
            by_tool[e.tool_name].append(e)

        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [],
        }

        for tool_name, tool_evidences in by_tool.items():
            # Collect unique rules
            rules = {}
            for e in tool_evidences:
                rule_id = e.rule_id or e.evidence_type.value
                if rule_id not in rules:
                    rules[rule_id] = {
                        "id": rule_id,
                        "name": e.rule_name or rule_id,
                        "shortDescription": {"text": e.rule_name or rule_id},
                    }

            run = {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_evidences[0].tool_version or "unknown",
                        "rules": list(rules.values()),
                    }
                },
                "results": [e.to_sarif_result() for e in tool_evidences],
            }

            sarif["runs"].append(run)

        with open(output_path, "w") as f:
            json.dump(sarif, f, indent=2)

    def _row_to_evidence(self, row: tuple[Any, ...], description: Any) -> Evidence:
        """Convert a database row to an Evidence object."""
        columns = [d[0] for d in description]
        data = dict(zip(columns, row))

        location = None
        if data.get("file_path"):
            location = EvidenceLocation(
                file_path=data["file_path"],
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
                start_column=data.get("start_column"),
                end_column=data.get("end_column"),
                snippet=data.get("snippet"),
            )

        call_path = None
        if data.get("call_path"):
            call_path = json.loads(data["call_path"])

        return Evidence(
            id=data["id"],
            evidence_type=EvidenceType(data["evidence_type"]),
            severity=Severity(data["severity"]),
            message=data["message"],
            description=data.get("description"),
            location=location,
            tool_name=data["tool_name"],
            tool_version=data.get("tool_version"),
            rule_id=data.get("rule_id"),
            rule_name=data.get("rule_name"),
            raw_output=data.get("raw_output"),
            command=data.get("command"),
            exit_code=data.get("exit_code"),
            trace_file=data.get("trace_file"),
            screenshot_file=data.get("screenshot_file"),
            video_file=data.get("video_file"),
            har_file=data.get("har_file"),
            call_path=call_path,
            entry_point=data.get("entry_point"),
            repo_path=data.get("repo_path"),
            commit_sha=data.get("commit_sha"),
            branch=data.get("branch"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            cwe_id=data.get("cwe_id"),
            cve_id=data.get("cve_id"),
            owasp_category=data.get("owasp_category"),
            suggested_fix=data.get("suggested_fix"),
            fix_difficulty=data.get("fix_difficulty"),
        )
