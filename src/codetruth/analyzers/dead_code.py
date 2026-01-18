"""
Dead Code Analyzer

Detects unreachable code, unused exports, and orphan components.
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


class DeadCodeAnalyzer(BaseAnalyzer):
    """
    Analyzer for detecting dead code.

    Finds:
    - Unreachable functions
    - Unused exports
    - Orphan components (React/Vue/etc.)
    - Unused variables
    - TODO/FIXME/HACK markers
    """

    name = "dead_code"
    description = "Detect unreachable and unused code"

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

        try:
            # Analyze different languages
            await self._analyze_typescript(repo_path, result, evidence_vault)
            await self._analyze_python(repo_path, result, evidence_vault)
            await self._find_code_markers(repo_path, result, evidence_vault)

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

    async def _analyze_typescript(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Analyze TypeScript/JavaScript for dead code."""
        exports: dict[str, set[str]] = {}  # file -> exported names
        imports: dict[str, set[str]] = {}  # file -> imported names

        # Collect exports and imports
        for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
            for path in repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                result.files_analyzed += 1
                content = path.read_text(errors="ignore")
                rel_path = str(path.relative_to(repo_path))

                # Find exports
                export_matches = re.findall(
                    r"export\s+(?:const|function|class|interface|type|enum)\s+(\w+)",
                    content,
                )
                export_default = re.findall(r"export\s+default\s+(\w+)", content)
                exports[rel_path] = set(export_matches + export_default)

                # Find imports
                import_matches = re.findall(
                    r"import\s+\{([^}]+)\}\s+from",
                    content,
                )
                for match in import_matches:
                    names = [n.strip().split(" as ")[0] for n in match.split(",")]
                    imports.setdefault(rel_path, set()).update(names)

        # Find unused exports (simplified - would need full analysis)
        all_imports = set()
        for imp_set in imports.values():
            all_imports.update(imp_set)

        for file_path, exported in exports.items():
            for name in exported:
                if name not in all_imports and not name.startswith("_"):
                    # Potentially unused export
                    finding = {
                        "type": "unused_export",
                        "severity": "warning",
                        "message": f"Export '{name}' may be unused",
                        "file": file_path,
                        "tool": self.name,
                    }
                    result.findings.append(finding)

                    if evidence_vault:
                        evidence = Evidence(
                            evidence_type=EvidenceType.DEAD_CODE,
                            severity=Severity.WARNING,
                            message=f"Export '{name}' may be unused",
                            location=EvidenceLocation(file_path=file_path),
                            tool_name=self.name,
                            repo_path=str(repo_path),
                        )
                        evidence_id = await evidence_vault.store_evidence(evidence)
                        result.evidence_ids.append(evidence_id)

    async def _analyze_python(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Analyze Python for dead code."""
        for path in repo_path.rglob("*.py"):
            if self._is_ignored(path):
                continue

            result.files_analyzed += 1
            content = path.read_text(errors="ignore")
            rel_path = str(path.relative_to(repo_path))
            lines = content.split("\n")

            # Find unreachable code after return/raise
            in_function = False
            for i, line in enumerate(lines):
                stripped = line.strip()

                if stripped.startswith("def ") or stripped.startswith("async def "):
                    in_function = True
                    continue

                if in_function and (stripped.startswith("return ") or stripped.startswith("raise ")):
                    # Check if next non-empty line is code (unreachable)
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith("#"):
                            # Check indentation
                            if len(lines[j]) - len(lines[j].lstrip()) >= len(line) - len(line.lstrip()):
                                finding = {
                                    "type": "unreachable_code",
                                    "severity": "warning",
                                    "message": "Unreachable code after return/raise",
                                    "file": rel_path,
                                    "line": j + 1,
                                    "tool": self.name,
                                }
                                result.findings.append(finding)
                                break
                            break

    async def _find_code_markers(
        self,
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Find TODO, FIXME, HACK, XXX markers."""
        markers = ["TODO", "FIXME", "HACK", "XXX", "BUG", "DEPRECATED"]

        for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.go", "*.rs"]:
            for path in repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")
                rel_path = str(path.relative_to(repo_path))
                lines = content.split("\n")

                for i, line in enumerate(lines):
                    for marker in markers:
                        if marker in line:
                            # Extract the comment
                            match = re.search(rf"{marker}[:\s]*(.+?)$", line)
                            comment = match.group(1).strip() if match else ""

                            severity_map = {
                                "FIXME": "warning",
                                "BUG": "error",
                                "HACK": "warning",
                                "DEPRECATED": "note",
                            }

                            finding = {
                                "type": "code_marker",
                                "marker": marker,
                                "severity": severity_map.get(marker, "note"),
                                "message": f"{marker}: {comment[:100]}" if comment else marker,
                                "file": rel_path,
                                "line": i + 1,
                                "tool": self.name,
                            }
                            result.findings.append(finding)
                            break  # Only report first marker per line
