"""
SAST (Static Application Security Testing) Analyzer

Security scanning with Semgrep and other SAST tools.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from codetruth.analyzers.base import BaseAnalyzer, AnalysisResult
from codetruth.core.evidence import Evidence, EvidenceType, Severity, EvidenceLocation

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class SASTAnalyzer(BaseAnalyzer):
    """SAST security analyzer using Semgrep."""

    name = "sast"
    description = "Static application security testing"

    DEFAULT_RULESETS = [
        "p/default",
        "p/owasp-top-ten",
        "p/security-audit",
    ]

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

        rulesets = options.get("rulesets", self.DEFAULT_RULESETS)

        try:
            await self._run_semgrep(repo_path, rulesets, result, evidence_vault)
            result.success = True
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int((result.completed_at - result.started_at).total_seconds() * 1000)
        result.findings_count = len(result.findings)

        return result

    async def _run_semgrep(
        self,
        repo_path: Path,
        rulesets: list[str],
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run Semgrep with specified rulesets."""
        config_args = []
        for ruleset in rulesets:
            config_args.extend(["--config", ruleset])

        try:
            process = await asyncio.create_subprocess_exec(
                "semgrep", "scan",
                *config_args,
                "--json",
                "--no-git-ignore",
                str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            result.commands_run.append(f"semgrep scan {' '.join(config_args)}")

            data = json.loads(stdout.decode())

            for finding in data.get("results", []):
                severity = self._map_severity(finding.get("extra", {}).get("severity", "WARNING"))

                finding_dict = {
                    "type": "security_vuln",
                    "severity": severity,
                    "message": finding.get("extra", {}).get("message", "Security issue"),
                    "file": finding.get("path", ""),
                    "line": finding.get("start", {}).get("line"),
                    "end_line": finding.get("end", {}).get("line"),
                    "rule_id": finding.get("check_id"),
                    "tool": "semgrep",
                    "cwe_id": finding.get("extra", {}).get("metadata", {}).get("cwe"),
                    "owasp": finding.get("extra", {}).get("metadata", {}).get("owasp"),
                }
                result.findings.append(finding_dict)

                if evidence_vault:
                    evidence = Evidence(
                        evidence_type=EvidenceType.SECURITY_VULN,
                        severity=Severity(severity),
                        message=finding_dict["message"],
                        location=EvidenceLocation(
                            file_path=finding_dict["file"],
                            start_line=finding_dict["line"],
                            end_line=finding_dict.get("end_line"),
                        ),
                        tool_name="semgrep",
                        rule_id=finding_dict["rule_id"],
                        cwe_id=str(finding_dict.get("cwe_id")) if finding_dict.get("cwe_id") else None,
                        owasp_category=str(finding_dict.get("owasp")) if finding_dict.get("owasp") else None,
                        repo_path=str(repo_path),
                    )
                    evidence_id = await evidence_vault.store_evidence(evidence)
                    result.evidence_ids.append(evidence_id)

            # Add errors
            for error in data.get("errors", []):
                result.findings.append({
                    "type": "sast_error",
                    "severity": "warning",
                    "message": error.get("message", "Semgrep error"),
                    "tool": "semgrep",
                })

        except FileNotFoundError:
            result.findings.append({
                "type": "sast_error",
                "severity": "warning",
                "message": "Semgrep not installed - run: pip install semgrep",
                "tool": "semgrep",
            })
        except json.JSONDecodeError:
            result.findings.append({
                "type": "sast_error",
                "severity": "warning",
                "message": "Failed to parse Semgrep output",
                "tool": "semgrep",
            })
        except Exception as e:
            result.findings.append({
                "type": "sast_error",
                "severity": "warning",
                "message": f"Semgrep failed: {str(e)}",
                "tool": "semgrep",
            })

    def _map_severity(self, semgrep_severity: str) -> str:
        """Map Semgrep severity to our severity levels."""
        mapping = {
            "ERROR": "critical",
            "WARNING": "warning",
            "INFO": "note",
        }
        return mapping.get(semgrep_severity.upper(), "warning")
