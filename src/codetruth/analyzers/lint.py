"""
Multi-Language Lint Analyzer

Orchestrates linting across Tier 1-3 languages.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from codetruth.analyzers.base import BaseAnalyzer, AnalysisResult
from codetruth.core.evidence import Evidence, EvidenceType, Severity, EvidenceLocation

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class LintAnalyzer(BaseAnalyzer):
    """Multi-language lint orchestrator."""

    name = "lint"
    description = "Multi-language linting"

    LINTERS = {
        # Tier 1 - Critical Core
        "typescript": {"cmd": ["npx", "eslint", "--ext", ".ts,.tsx", "--format", "json"], "parser": "_parse_eslint"},
        "javascript": {"cmd": ["npx", "eslint", "--ext", ".js,.jsx", "--format", "json"], "parser": "_parse_eslint"},
        "python": {"cmd": ["ruff", "check", "--output-format", "json"], "parser": "_parse_ruff"},
        "css": {"cmd": ["npx", "stylelint", "**/*.css", "--formatter", "json"], "parser": "_parse_stylelint"},

        # Tier 2 - Infra
        "dockerfile": {"cmd": ["hadolint", "--format", "json"], "parser": "_parse_hadolint"},
        "yaml": {"cmd": ["yamllint", "-f", "parsable"], "parser": "_parse_yamllint"},
        "shell": {"cmd": ["shellcheck", "-f", "json"], "parser": "_parse_shellcheck"},

        # Tier 3 - Native
        "rust": {"cmd": ["cargo", "clippy", "--message-format=json"], "parser": "_parse_clippy"},
        "go": {"cmd": ["golangci-lint", "run", "--out-format", "json"], "parser": "_parse_golangci"},
    }

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

        # Detect which linters to run
        linters_to_run = await self._detect_linters(repo_path)

        # Run linters in parallel
        tasks = []
        for linter_name in linters_to_run:
            if linter_name in self.LINTERS:
                tasks.append(self._run_linter(linter_name, repo_path, result, evidence_vault))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int((result.completed_at - result.started_at).total_seconds() * 1000)
        result.findings_count = len(result.findings)
        result.success = True

        return result

    async def _detect_linters(self, repo_path: Path) -> list[str]:
        """Detect which linters should run."""
        linters = []

        # TypeScript/JavaScript
        if (repo_path / "package.json").exists():
            if list(repo_path.rglob("*.ts")) or list(repo_path.rglob("*.tsx")):
                linters.append("typescript")
            if list(repo_path.rglob("*.js")) or list(repo_path.rglob("*.jsx")):
                linters.append("javascript")
            if list(repo_path.rglob("*.css")):
                linters.append("css")

        # Python
        if list(repo_path.rglob("*.py")):
            linters.append("python")

        # Docker
        if (repo_path / "Dockerfile").exists():
            linters.append("dockerfile")

        # YAML
        if list(repo_path.rglob("*.yml")) or list(repo_path.rglob("*.yaml")):
            linters.append("yaml")

        # Shell
        if list(repo_path.rglob("*.sh")):
            linters.append("shell")

        # Rust
        if (repo_path / "Cargo.toml").exists():
            linters.append("rust")

        # Go
        if (repo_path / "go.mod").exists():
            linters.append("go")

        return linters

    async def _run_linter(
        self,
        linter_name: str,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Run a single linter."""
        config = self.LINTERS[linter_name]
        cmd = config["cmd"]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                ".",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            result.commands_run.append(" ".join(cmd))

            # Parse output
            parser = getattr(self, config["parser"], None)
            if parser:
                findings = parser(stdout.decode(), str(repo_path))
                for finding in findings:
                    finding["tool"] = linter_name
                    result.findings.append(finding)

                    if evidence_vault:
                        evidence = Evidence(
                            evidence_type=EvidenceType.LINT_ERROR,
                            severity=Severity(finding.get("severity", "warning")),
                            message=finding.get("message", ""),
                            location=EvidenceLocation(
                                file_path=finding.get("file", ""),
                                start_line=finding.get("line"),
                            ),
                            tool_name=linter_name,
                            rule_id=finding.get("rule_id"),
                            repo_path=str(repo_path),
                        )
                        evidence_id = await evidence_vault.store_evidence(evidence)
                        result.evidence_ids.append(evidence_id)

        except asyncio.TimeoutError:
            result.findings.append({
                "type": "linter_timeout",
                "severity": "warning",
                "message": f"Linter {linter_name} timed out",
                "tool": linter_name,
            })
        except FileNotFoundError:
            pass  # Linter not installed
        except Exception as e:
            result.findings.append({
                "type": "linter_error",
                "severity": "warning",
                "message": f"Linter {linter_name} failed: {str(e)}",
                "tool": linter_name,
            })

    def _parse_eslint(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse ESLint JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for file_result in data:
                for msg in file_result.get("messages", []):
                    findings.append({
                        "type": "lint_error",
                        "severity": "error" if msg.get("severity") == 2 else "warning",
                        "message": msg.get("message", ""),
                        "file": file_result.get("filePath", "").replace(repo_path + "/", ""),
                        "line": msg.get("line"),
                        "rule_id": msg.get("ruleId"),
                    })
        except json.JSONDecodeError:
            pass
        return findings

    def _parse_ruff(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse Ruff JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for issue in data:
                findings.append({
                    "type": "lint_error",
                    "severity": "warning",
                    "message": issue.get("message", ""),
                    "file": issue.get("filename", "").replace(repo_path + "/", ""),
                    "line": issue.get("location", {}).get("row"),
                    "rule_id": issue.get("code"),
                })
        except json.JSONDecodeError:
            pass
        return findings

    def _parse_shellcheck(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse ShellCheck JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for issue in data:
                severity_map = {"error": "error", "warning": "warning", "info": "note", "style": "note"}
                findings.append({
                    "type": "lint_error",
                    "severity": severity_map.get(issue.get("level"), "warning"),
                    "message": issue.get("message", ""),
                    "file": issue.get("file", "").replace(repo_path + "/", ""),
                    "line": issue.get("line"),
                    "rule_id": f"SC{issue.get('code')}",
                })
        except json.JSONDecodeError:
            pass
        return findings

    def _parse_hadolint(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse Hadolint JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for issue in data:
                findings.append({
                    "type": "lint_error",
                    "severity": "warning",
                    "message": issue.get("message", ""),
                    "file": issue.get("file", "Dockerfile"),
                    "line": issue.get("line"),
                    "rule_id": issue.get("code"),
                })
        except json.JSONDecodeError:
            pass
        return findings

    def _parse_stylelint(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse Stylelint JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for file_result in data:
                for warn in file_result.get("warnings", []):
                    findings.append({
                        "type": "lint_error",
                        "severity": warn.get("severity", "warning"),
                        "message": warn.get("text", ""),
                        "file": file_result.get("source", "").replace(repo_path + "/", ""),
                        "line": warn.get("line"),
                        "rule_id": warn.get("rule"),
                    })
        except json.JSONDecodeError:
            pass
        return findings

    def _parse_clippy(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse Cargo Clippy JSON output."""
        findings = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get("reason") == "compiler-message":
                    msg = data.get("message", {})
                    level = msg.get("level", "warning")
                    if level in ["error", "warning"]:
                        spans = msg.get("spans", [{}])
                        span = spans[0] if spans else {}
                        findings.append({
                            "type": "lint_error",
                            "severity": level,
                            "message": msg.get("message", ""),
                            "file": span.get("file_name", "").replace(repo_path + "/", ""),
                            "line": span.get("line_start"),
                            "rule_id": msg.get("code", {}).get("code"),
                        })
            except json.JSONDecodeError:
                continue
        return findings

    def _parse_golangci(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse golangci-lint JSON output."""
        findings = []
        try:
            data = json.loads(output)
            for issue in data.get("Issues", []):
                findings.append({
                    "type": "lint_error",
                    "severity": issue.get("Severity", "warning"),
                    "message": issue.get("Text", ""),
                    "file": issue.get("Pos", {}).get("Filename", "").replace(repo_path + "/", ""),
                    "line": issue.get("Pos", {}).get("Line"),
                    "rule_id": issue.get("FromLinter"),
                })
        except json.JSONDecodeError:
            pass
        return findings

    def _parse_yamllint(self, output: str, repo_path: str) -> list[dict[str, Any]]:
        """Parse yamllint parsable output."""
        findings = []
        import re
        for line in output.split("\n"):
            match = re.match(r"(.+):(\d+):(\d+): \[(\w+)\] (.+)", line)
            if match:
                findings.append({
                    "type": "lint_error",
                    "severity": match.group(4),
                    "message": match.group(5),
                    "file": match.group(1).replace(repo_path + "/", ""),
                    "line": int(match.group(2)),
                })
        return findings
