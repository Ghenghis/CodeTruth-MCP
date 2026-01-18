"""
Secret Scanner

Detects leaked secrets, API keys, and credentials using gitleaks/trufflehog.
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


class SecretScanner(BaseAnalyzer):
    """Secret scanning with gitleaks and trufflehog."""

    name = "secrets"
    description = "Scan for leaked secrets and credentials"

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

        tools = options.get("tools", ["gitleaks"])

        try:
            if "gitleaks" in tools:
                await self._run_gitleaks(repo_path, result, evidence_vault)

            if "trufflehog" in tools:
                verify = options.get("verify", False)
                await self._run_trufflehog(repo_path, verify, result, evidence_vault)

            result.success = True
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int((result.completed_at - result.started_at).total_seconds() * 1000)
        result.findings_count = len(result.findings)

        return result

    async def _run_gitleaks(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run gitleaks scanner."""
        try:
            process = await asyncio.create_subprocess_exec(
                "gitleaks", "detect",
                "--source", str(repo_path),
                "--report-format", "json",
                "--report-path", "/dev/stdout",
                "--no-git",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            result.commands_run.append("gitleaks detect")

            if stdout:
                findings = json.loads(stdout.decode())

                for finding in findings:
                    finding_dict = {
                        "type": "secret_leak",
                        "severity": "critical",
                        "message": f"Potential {finding.get('RuleID', 'secret')} detected",
                        "file": finding.get("File", ""),
                        "line": finding.get("StartLine"),
                        "end_line": finding.get("EndLine"),
                        "rule_id": finding.get("RuleID"),
                        "tool": "gitleaks",
                        "secret_type": finding.get("RuleID"),
                        "match": finding.get("Match", "")[:50] + "..." if finding.get("Match") else None,
                    }
                    result.findings.append(finding_dict)

                    if evidence_vault:
                        evidence = Evidence(
                            evidence_type=EvidenceType.SECRET_LEAK,
                            severity=Severity.CRITICAL,
                            message=finding_dict["message"],
                            location=EvidenceLocation(
                                file_path=finding_dict["file"],
                                start_line=finding_dict["line"],
                                end_line=finding_dict.get("end_line"),
                            ),
                            tool_name="gitleaks",
                            rule_id=finding_dict["rule_id"],
                            repo_path=str(repo_path),
                        )
                        evidence_id = await evidence_vault.store_evidence(evidence)
                        result.evidence_ids.append(evidence_id)

        except FileNotFoundError:
            result.findings.append({
                "type": "scanner_error",
                "severity": "note",
                "message": "gitleaks not installed - run: brew install gitleaks",
                "tool": "gitleaks",
            })
        except json.JSONDecodeError:
            pass  # No findings
        except Exception as e:
            result.findings.append({
                "type": "scanner_error",
                "severity": "warning",
                "message": f"gitleaks failed: {str(e)}",
                "tool": "gitleaks",
            })

    async def _run_trufflehog(
        self,
        repo_path: Path,
        verify: bool,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run trufflehog scanner."""
        try:
            cmd = [
                "trufflehog", "filesystem",
                str(repo_path),
                "--json",
            ]
            if verify:
                cmd.append("--only-verified")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            result.commands_run.append(" ".join(cmd))

            for line in stdout.decode().split("\n"):
                if not line.strip():
                    continue
                try:
                    finding = json.loads(line)

                    finding_dict = {
                        "type": "secret_leak",
                        "severity": "critical" if finding.get("Verified") else "error",
                        "message": f"Potential {finding.get('DetectorName', 'secret')} detected",
                        "file": finding.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("file", ""),
                        "line": finding.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("line"),
                        "rule_id": finding.get("DetectorName"),
                        "tool": "trufflehog",
                        "verified": finding.get("Verified", False),
                    }
                    result.findings.append(finding_dict)

                except json.JSONDecodeError:
                    continue

        except FileNotFoundError:
            result.findings.append({
                "type": "scanner_error",
                "severity": "note",
                "message": "trufflehog not installed - run: brew install trufflehog",
                "tool": "trufflehog",
            })
        except Exception as e:
            result.findings.append({
                "type": "scanner_error",
                "severity": "warning",
                "message": f"trufflehog failed: {str(e)}",
                "tool": "trufflehog",
            })
