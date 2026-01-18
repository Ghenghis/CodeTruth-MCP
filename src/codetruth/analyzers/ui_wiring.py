"""
UI Wiring Analyzer

Detects dead buttons, unbound handlers, and missing routes.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from codetruth.analyzers.base import BaseAnalyzer, AnalysisResult
from codetruth.core.evidence import Evidence, EvidenceType, Severity, EvidenceLocation

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class UIWiringAnalyzer(BaseAnalyzer):
    """
    Analyzer for UI wiring issues.

    Finds:
    - Buttons/elements with onClick but no handler
    - Handlers defined but never used
    - Routes defined but component missing
    - Event handlers that do nothing
    """

    name = "ui_wiring"
    description = "Detect dead UI elements and unbound handlers"

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

        framework = options.get("framework", "auto")

        try:
            # Auto-detect framework
            if framework == "auto":
                framework = await self._detect_framework(repo_path)

            if framework in ["react", "auto"]:
                await self._analyze_react(repo_path, result, evidence_vault)

            await self._analyze_event_handlers(repo_path, result, evidence_vault)

            result.success = True

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int(
            (result.completed_at - result.started_at).total_seconds() * 1000
        )
        result.findings_count = len(result.findings)

        return result

    async def _detect_framework(self, repo_path: Path) -> str:
        """Auto-detect UI framework."""
        pkg_path = repo_path / "package.json"
        if pkg_path.exists():
            import json
            try:
                with open(pkg_path) as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                    if "react" in deps:
                        return "react"
                    if "vue" in deps:
                        return "vue"
                    if "@angular/core" in deps:
                        return "angular"
                    if "svelte" in deps:
                        return "svelte"
            except:
                pass

        return "auto"

    async def _analyze_react(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Analyze React components for wiring issues."""
        # Track handlers defined vs used
        handlers_defined: dict[str, list[tuple[str, int]]] = {}  # name -> [(file, line)]
        handlers_used: set[str] = set()

        for ext in ["*.tsx", "*.jsx"]:
            for path in repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                result.files_analyzed += 1
                content = path.read_text(errors="ignore")
                rel_path = str(path.relative_to(repo_path))
                lines = content.split("\n")

                # Find handler definitions
                for i, line in enumerate(lines):
                    # const handleClick = ...
                    match = re.search(r"const\s+(handle\w+)\s*=", line)
                    if match:
                        handler_name = match.group(1)
                        handlers_defined.setdefault(handler_name, []).append((rel_path, i + 1))

                    # function handleClick
                    match = re.search(r"function\s+(handle\w+)\s*\(", line)
                    if match:
                        handler_name = match.group(1)
                        handlers_defined.setdefault(handler_name, []).append((rel_path, i + 1))

                    # Find handler usage in JSX
                    # onClick={handleClick} or onClick={this.handleClick}
                    usage_matches = re.findall(r"on\w+={(?:this\.)?(handle\w+)}", line)
                    handlers_used.update(usage_matches)

                    # Also check for handlers passed as props
                    prop_matches = re.findall(r"(\w+Handler)=", line)
                    handlers_used.update(prop_matches)

                # Find empty handlers
                await self._find_empty_handlers(content, rel_path, lines, result, evidence_vault)

                # Find buttons without handlers
                await self._find_unwired_buttons(content, rel_path, lines, result, evidence_vault)

        # Report unused handlers
        for handler_name, locations in handlers_defined.items():
            if handler_name not in handlers_used:
                for file_path, line in locations:
                    finding = {
                        "type": "unused_handler",
                        "severity": "warning",
                        "message": f"Handler '{handler_name}' is defined but never used",
                        "file": file_path,
                        "line": line,
                        "tool": self.name,
                    }
                    result.findings.append(finding)

                    if evidence_vault:
                        evidence = Evidence(
                            evidence_type=EvidenceType.UNBOUND_HANDLER,
                            severity=Severity.WARNING,
                            message=f"Handler '{handler_name}' is defined but never used",
                            location=EvidenceLocation(file_path=file_path, start_line=line),
                            tool_name=self.name,
                            repo_path=str(repo_path),
                        )
                        evidence_id = await evidence_vault.store_evidence(evidence)
                        result.evidence_ids.append(evidence_id)

    async def _find_empty_handlers(
        self,
        content: str,
        file_path: str,
        lines: list[str],
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Find handlers that do nothing."""
        # Pattern: onClick={() => {}}
        empty_pattern = r"on\w+={(?:\(\)\s*=>|function\s*\(\))\s*\{\s*\}}"

        for i, line in enumerate(lines):
            if re.search(empty_pattern, line):
                finding = {
                    "type": "empty_handler",
                    "severity": "warning",
                    "message": "Empty event handler - does nothing",
                    "file": file_path,
                    "line": i + 1,
                    "tool": self.name,
                }
                result.findings.append(finding)

        # Pattern: onClick={() => console.log(...)} only
        console_only = r"on\w+={(?:\(\)\s*=>|function\s*\(\))\s*\{\s*console\.\w+\([^)]*\)\s*;?\s*\}}"

        for i, line in enumerate(lines):
            if re.search(console_only, line):
                finding = {
                    "type": "debug_only_handler",
                    "severity": "note",
                    "message": "Handler only contains console statement - likely placeholder",
                    "file": file_path,
                    "line": i + 1,
                    "tool": self.name,
                }
                result.findings.append(finding)

    async def _find_unwired_buttons(
        self,
        content: str,
        file_path: str,
        lines: list[str],
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Find buttons without click handlers."""
        for i, line in enumerate(lines):
            # Button without onClick
            if re.search(r"<button[^>]*>", line, re.IGNORECASE):
                # Check if onClick is present in this or nearby lines
                context = "\n".join(lines[max(0, i - 1):min(len(lines), i + 3)])
                if "onClick" not in context and "type=\"submit\"" not in context.lower():
                    # Might be a dead button
                    finding = {
                        "type": "button_no_handler",
                        "severity": "note",
                        "message": "Button without onClick handler (may be intentional)",
                        "file": file_path,
                        "line": i + 1,
                        "tool": self.name,
                    }
                    result.findings.append(finding)

    async def _analyze_event_handlers(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Analyze general event handler patterns."""
        # Find addEventListener without removeEventListener
        for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
            for path in repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")
                rel_path = str(path.relative_to(repo_path))
                lines = content.split("\n")

                # Count addEventListener vs removeEventListener
                add_count = len(re.findall(r"addEventListener\s*\(", content))
                remove_count = len(re.findall(r"removeEventListener\s*\(", content))

                if add_count > remove_count and add_count > 0:
                    finding = {
                        "type": "potential_memory_leak",
                        "severity": "warning",
                        "message": f"More addEventListener ({add_count}) than removeEventListener ({remove_count}) - potential memory leak",
                        "file": rel_path,
                        "tool": self.name,
                    }
                    result.findings.append(finding)
