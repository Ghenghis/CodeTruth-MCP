"""
Type Checking Analyzer

Verifies type safety across Tier 1-3 languages.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from codetruth.analyzers.base import BaseAnalyzer, AnalysisResult
from codetruth.core.evidence import Evidence, EvidenceType, Severity, EvidenceLocation

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class TypeCheckAnalyzer(BaseAnalyzer):
    """Type checking orchestrator."""

    name = "type_check"
    description = "Multi-language type checking"

    async def run(
        self,
        repo_path: Path,
        options: dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        result = AnalysisResult(
            analyzer_name=self.name,
            started_at=datetime.utcnow(),
        )

        tasks = []

        # TypeScript
        if (repo_path / "tsconfig.json").exists():
            tasks.append(self._run_tsc(repo_path, result, evidence_vault))

        # Python
        if list(repo_path.rglob("*.py")):
            tasks.append(self._run_mypy(repo_path, result, evidence_vault))

        # Rust (type checking is part of cargo check)
        if (repo_path / "Cargo.toml").exists():
            tasks.append(self._run_cargo_check(repo_path, result, evidence_vault))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int((result.completed_at - result.started_at).total_seconds() * 1000)
        result.findings_count = len(result.findings)
        result.success = True

        return result

    async def _run_tsc(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run TypeScript compiler."""
        try:
            process = await asyncio.create_subprocess_exec(
                "npx", "tsc", "--noEmit", "--pretty", "false",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            result.commands_run.append("npx tsc --noEmit")

            output = stdout.decode() + stderr.decode()

            # Parse TypeScript errors
            # Format: file(line,col): error TSxxxx: message
            for line in output.split("\n"):
                match = re.match(r"(.+)\((\d+),(\d+)\): error (TS\d+): (.+)", line)
                if match:
                    file_path, line_num, col, code, message = match.groups()

                    finding = {
                        "type": "type_error",
                        "severity": "error",
                        "message": message,
                        "file": file_path,
                        "line": int(line_num),
                        "column": int(col),
                        "rule_id": code,
                        "tool": "tsc",
                    }
                    result.findings.append(finding)

                    if evidence_vault:
                        evidence = Evidence(
                            evidence_type=EvidenceType.TYPE_ERROR,
                            severity=Severity.ERROR,
                            message=message,
                            location=EvidenceLocation(
                                file_path=file_path,
                                start_line=int(line_num),
                                start_column=int(col),
                            ),
                            tool_name="tsc",
                            rule_id=code,
                            repo_path=str(repo_path),
                        )
                        await evidence_vault.store_evidence(evidence)

        except Exception as e:
            result.findings.append({
                "type": "type_check_error",
                "severity": "warning",
                "message": f"TypeScript check failed: {str(e)}",
                "tool": "tsc",
            })

    async def _run_mypy(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run MyPy type checker."""
        try:
            process = await asyncio.create_subprocess_exec(
                "mypy", ".", "--ignore-missing-imports", "--no-error-summary",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            result.commands_run.append("mypy . --ignore-missing-imports")

            output = stdout.decode()

            # Parse MyPy errors
            # Format: file:line: error: message
            for line in output.split("\n"):
                match = re.match(r"(.+):(\d+): (error|warning|note): (.+)", line)
                if match:
                    file_path, line_num, level, message = match.groups()

                    finding = {
                        "type": "type_error",
                        "severity": level,
                        "message": message,
                        "file": file_path,
                        "line": int(line_num),
                        "tool": "mypy",
                    }
                    result.findings.append(finding)

                    if evidence_vault and level == "error":
                        evidence = Evidence(
                            evidence_type=EvidenceType.TYPE_ERROR,
                            severity=Severity.ERROR,
                            message=message,
                            location=EvidenceLocation(
                                file_path=file_path,
                                start_line=int(line_num),
                            ),
                            tool_name="mypy",
                            repo_path=str(repo_path),
                        )
                        await evidence_vault.store_evidence(evidence)

        except Exception as e:
            result.findings.append({
                "type": "type_check_error",
                "severity": "warning",
                "message": f"MyPy check failed: {str(e)}",
                "tool": "mypy",
            })

    async def _run_cargo_check(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run Cargo check for Rust."""
        try:
            process = await asyncio.create_subprocess_exec(
                "cargo", "check", "--message-format=json",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            result.commands_run.append("cargo check")

            for line in stdout.decode().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("reason") == "compiler-message":
                        msg = data.get("message", {})
                        level = msg.get("level")
                        if level in ["error", "warning"]:
                            spans = msg.get("spans", [{}])
                            span = spans[0] if spans else {}

                            finding = {
                                "type": "type_error" if level == "error" else "lint_error",
                                "severity": level,
                                "message": msg.get("message", ""),
                                "file": span.get("file_name", ""),
                                "line": span.get("line_start"),
                                "tool": "cargo",
                            }
                            result.findings.append(finding)
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            result.findings.append({
                "type": "type_check_error",
                "severity": "warning",
                "message": f"Cargo check failed: {str(e)}",
                "tool": "cargo",
            })
