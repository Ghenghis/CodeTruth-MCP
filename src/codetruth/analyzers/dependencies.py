"""
Dependency Auditor

Scans dependencies for known vulnerabilities using npm audit, pip-audit, trivy, osv-scanner.
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


class DependencyAuditor(BaseAnalyzer):
    """Dependency vulnerability scanner."""

    name = "dependencies"
    description = "Scan dependencies for vulnerabilities"

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

        tools = options.get("tools", ["osv"])

        try:
            # Auto-detect and run appropriate scanners
            if (repo_path / "package.json").exists():
                if "npm_audit" in tools:
                    await self._run_npm_audit(repo_path, result, evidence_vault)

            if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
                if "pip_audit" in tools:
                    await self._run_pip_audit(repo_path, result, evidence_vault)

            # OSV-Scanner works for multiple ecosystems
            if "osv" in tools:
                await self._run_osv_scanner(repo_path, result, evidence_vault)

            # Trivy for containers
            if "trivy" in tools and (repo_path / "Dockerfile").exists():
                await self._run_trivy(repo_path, result, evidence_vault)

            result.success = True
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int((result.completed_at - result.started_at).total_seconds() * 1000)
        result.findings_count = len(result.findings)

        return result

    async def _run_npm_audit(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run npm audit."""
        try:
            process = await asyncio.create_subprocess_exec(
                "npm", "audit", "--json",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            result.commands_run.append("npm audit")

            data = json.loads(stdout.decode())

            for vuln_id, vuln in data.get("vulnerabilities", {}).items():
                severity = self._map_npm_severity(vuln.get("severity", "low"))

                finding = {
                    "type": "dependency_vuln",
                    "severity": severity,
                    "message": f"{vuln_id}: {vuln.get('title', 'Vulnerability')}",
                    "file": "package.json",
                    "tool": "npm_audit",
                    "package": vuln_id,
                    "cve_id": vuln.get("cves", [None])[0] if vuln.get("cves") else None,
                    "vulnerable_versions": vuln.get("range"),
                    "fix_available": vuln.get("fixAvailable", False),
                }
                result.findings.append(finding)

                if evidence_vault:
                    evidence = Evidence(
                        evidence_type=EvidenceType.DEPENDENCY_VULN,
                        severity=Severity(severity),
                        message=finding["message"],
                        location=EvidenceLocation(file_path="package.json"),
                        tool_name="npm_audit",
                        cve_id=finding.get("cve_id"),
                        repo_path=str(repo_path),
                    )
                    await evidence_vault.store_evidence(evidence)

        except FileNotFoundError:
            pass  # npm not installed
        except json.JSONDecodeError:
            pass
        except Exception as e:
            result.findings.append({
                "type": "audit_error",
                "severity": "warning",
                "message": f"npm audit failed: {str(e)}",
                "tool": "npm_audit",
            })

    async def _run_pip_audit(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run pip-audit."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pip-audit", "--format", "json",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            result.commands_run.append("pip-audit")

            data = json.loads(stdout.decode())

            for vuln in data:
                finding = {
                    "type": "dependency_vuln",
                    "severity": "error",
                    "message": f"{vuln.get('name')}: {vuln.get('vulns', [{}])[0].get('id', 'Vulnerability')}",
                    "file": "requirements.txt",
                    "tool": "pip_audit",
                    "package": vuln.get("name"),
                    "version": vuln.get("version"),
                    "cve_id": vuln.get("vulns", [{}])[0].get("id"),
                }
                result.findings.append(finding)

        except FileNotFoundError:
            result.findings.append({
                "type": "audit_error",
                "severity": "note",
                "message": "pip-audit not installed - run: pip install pip-audit",
                "tool": "pip_audit",
            })
        except json.JSONDecodeError:
            pass
        except Exception as e:
            result.findings.append({
                "type": "audit_error",
                "severity": "warning",
                "message": f"pip-audit failed: {str(e)}",
                "tool": "pip_audit",
            })

    async def _run_osv_scanner(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run osv-scanner."""
        try:
            process = await asyncio.create_subprocess_exec(
                "osv-scanner", "--format", "json", "-r", str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            result.commands_run.append("osv-scanner")

            data = json.loads(stdout.decode())

            for vuln_result in data.get("results", []):
                source = vuln_result.get("source", {})
                for pkg in vuln_result.get("packages", []):
                    for vuln in pkg.get("vulnerabilities", []):
                        severity = self._get_osv_severity(vuln)

                        finding = {
                            "type": "dependency_vuln",
                            "severity": severity,
                            "message": f"{pkg.get('package', {}).get('name')}: {vuln.get('summary', vuln.get('id'))}",
                            "file": source.get("path", ""),
                            "tool": "osv_scanner",
                            "package": pkg.get("package", {}).get("name"),
                            "version": pkg.get("package", {}).get("version"),
                            "cve_id": vuln.get("aliases", [None])[0] if vuln.get("aliases") else vuln.get("id"),
                        }
                        result.findings.append(finding)

        except FileNotFoundError:
            result.findings.append({
                "type": "audit_error",
                "severity": "note",
                "message": "osv-scanner not installed - see: https://google.github.io/osv-scanner/",
                "tool": "osv_scanner",
            })
        except json.JSONDecodeError:
            pass
        except Exception as e:
            result.findings.append({
                "type": "audit_error",
                "severity": "warning",
                "message": f"osv-scanner failed: {str(e)}",
                "tool": "osv_scanner",
            })

    async def _run_trivy(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run trivy for container scanning."""
        try:
            process = await asyncio.create_subprocess_exec(
                "trivy", "fs", "--format", "json", str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            result.commands_run.append("trivy fs")

            data = json.loads(stdout.decode())

            for target_result in data.get("Results", []):
                for vuln in target_result.get("Vulnerabilities", []):
                    finding = {
                        "type": "dependency_vuln",
                        "severity": vuln.get("Severity", "UNKNOWN").lower(),
                        "message": f"{vuln.get('PkgName')}: {vuln.get('Title', vuln.get('VulnerabilityID'))}",
                        "file": target_result.get("Target", ""),
                        "tool": "trivy",
                        "package": vuln.get("PkgName"),
                        "version": vuln.get("InstalledVersion"),
                        "cve_id": vuln.get("VulnerabilityID"),
                        "fixed_version": vuln.get("FixedVersion"),
                    }
                    result.findings.append(finding)

        except FileNotFoundError:
            result.findings.append({
                "type": "audit_error",
                "severity": "note",
                "message": "trivy not installed - run: brew install trivy",
                "tool": "trivy",
            })
        except json.JSONDecodeError:
            pass
        except Exception as e:
            result.findings.append({
                "type": "audit_error",
                "severity": "warning",
                "message": f"trivy failed: {str(e)}",
                "tool": "trivy",
            })

    def _map_npm_severity(self, severity: str) -> str:
        """Map npm severity to our severity levels."""
        mapping = {
            "critical": "critical",
            "high": "error",
            "moderate": "warning",
            "low": "note",
        }
        return mapping.get(severity.lower(), "warning")

    def _get_osv_severity(self, vuln: dict[str, Any]) -> str:
        """Get severity from OSV vulnerability."""
        severity = vuln.get("database_specific", {}).get("severity")
        if severity:
            return self._map_npm_severity(severity)

        # Check CVSS
        for severity_item in vuln.get("severity", []):
            score = severity_item.get("score")
            if score:
                try:
                    score_num = float(score.split("/")[0]) if "/" in str(score) else float(score)
                    if score_num >= 9.0:
                        return "critical"
                    elif score_num >= 7.0:
                        return "error"
                    elif score_num >= 4.0:
                        return "warning"
                    else:
                        return "note"
                except:
                    pass

        return "warning"
