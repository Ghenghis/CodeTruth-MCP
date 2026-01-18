"""
Audit Folder Generator

Creates a comprehensive audit folder structure in the project directory
with markdown reports, SVG diagrams, and detailed findings.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from codetruth.reports.svg_diagrams import SVGDiagramGenerator
from codetruth.reports.markdown import MarkdownReportGenerator


class AuditFolderGenerator:
    """
    Generates a structured audit folder in the project directory.

    Structure:
    .codetruth/
    ├── audit-YYYYMMDD-HHMMSS/
    │   ├── README.md                 # Executive summary
    │   ├── FINDINGS.md               # All findings with evidence
    │   ├── TRUTH_TABLE.md            # Feature truth table
    │   ├── FIX_PLAN.md               # Prioritized fix plan
    │   ├── diagrams/
    │   │   ├── architecture.svg      # Codebase architecture
    │   │   ├── call-graph.svg        # Function call graph
    │   │   ├── dependency-graph.svg  # Package dependencies
    │   │   ├── ui-flow.svg           # UI component flow
    │   │   └── coverage-map.svg      # Test coverage visualization
    │   ├── reports/
    │   │   ├── security.md           # Security findings
    │   │   ├── dead-code.md          # Dead code report
    │   │   ├── type-errors.md        # Type checking results
    │   │   ├── lint-errors.md        # Linting results
    │   │   └── contracts.md          # API contract validation
    │   ├── evidence/
    │   │   ├── traces/               # Playwright traces
    │   │   ├── screenshots/          # Visual regression screenshots
    │   │   └── logs/                 # Command outputs
    │   └── data/
    │       ├── inventory.json        # Full inventory
    │       ├── findings.json         # All findings as JSON
    │       ├── truth-table.json      # Truth table data
    │       └── sarif/                # SARIF format reports
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        self.audit_dir = repo_path / ".codetruth" / f"audit-{self.timestamp}"

        self.svg_generator = SVGDiagramGenerator()
        self.markdown_generator = MarkdownReportGenerator()

    async def generate(
        self,
        audit_results: dict[str, Any],
        include_diagrams: bool = True,
        include_evidence: bool = True,
    ) -> Path:
        """
        Generate the complete audit folder.

        Args:
            audit_results: Complete audit results from the analyzer
            include_diagrams: Whether to generate SVG diagrams
            include_evidence: Whether to include evidence artifacts

        Returns:
            Path to the generated audit folder
        """
        # Create directory structure
        self._create_directories()

        # Generate main reports
        await self._generate_readme(audit_results)
        await self._generate_findings(audit_results)
        await self._generate_truth_table(audit_results)
        await self._generate_fix_plan(audit_results)

        # Generate category reports
        await self._generate_category_reports(audit_results)

        # Generate diagrams
        if include_diagrams:
            await self._generate_diagrams(audit_results)

        # Save raw data
        await self._save_data(audit_results)

        # Copy evidence artifacts
        if include_evidence:
            await self._copy_evidence(audit_results)

        return self.audit_dir

    def _create_directories(self) -> None:
        """Create the audit folder structure."""
        directories = [
            self.audit_dir,
            self.audit_dir / "diagrams",
            self.audit_dir / "reports",
            self.audit_dir / "evidence" / "traces",
            self.audit_dir / "evidence" / "screenshots",
            self.audit_dir / "evidence" / "logs",
            self.audit_dir / "data" / "sarif",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def _generate_readme(self, results: dict[str, Any]) -> None:
        """Generate the executive summary README."""
        summary = results.get("summary", {})
        gates = results.get("gates", {})

        content = f"""# CodeTruth Audit Report

**Repository:** {self.repo_path.name}
**Audit Date:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
**Profile:** {results.get("profile", "standard")}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Findings | {summary.get("total_findings", 0)} |
| Critical | {summary.get("critical", 0)} |
| Errors | {summary.get("errors", 0)} |
| Warnings | {summary.get("warnings", 0)} |
| Gates Passed | {gates.get("passed", 0)}/{gates.get("total", 0)} |

## Quality Gate Results

| Gate | Status |
|------|--------|
| Gate 0: Build & Boot | {self._gate_status(gates, 0)} |
| Gate 1: Lint & Type | {self._gate_status(gates, 1)} |
| Gate 2: Unit Tests | {self._gate_status(gates, 2)} |
| Gate 3: Contract Tests | {self._gate_status(gates, 3)} |
| Gate 4: Integration/E2E | {self._gate_status(gates, 4)} |
| Gate 5: Security | {self._gate_status(gates, 5)} |
| Gate 6: Release Ready | {self._gate_status(gates, 6)} |

## Key Findings

"""
        # Add top critical findings
        findings = results.get("findings", [])
        critical = [f for f in findings if f.get("severity") == "critical"][:5]

        if critical:
            content += "### Critical Issues\n\n"
            for finding in critical:
                content += f"- **{finding.get('type', 'Unknown')}**: {finding.get('message', 'No message')}\n"
                if finding.get("file"):
                    content += f"  - Location: `{finding['file']}`"
                    if finding.get("line"):
                        content += f":{finding['line']}"
                    content += "\n"
        else:
            content += "*No critical issues found!*\n"

        content += """
## Reports

- [All Findings](FINDINGS.md)
- [Feature Truth Table](TRUTH_TABLE.md)
- [Fix Plan](FIX_PLAN.md)

### Category Reports

- [Security Report](reports/security.md)
- [Dead Code Report](reports/dead-code.md)
- [Type Errors](reports/type-errors.md)
- [Lint Errors](reports/lint-errors.md)
- [API Contracts](reports/contracts.md)

## Diagrams

- [Architecture](diagrams/architecture.svg)
- [Call Graph](diagrams/call-graph.svg)
- [Dependency Graph](diagrams/dependency-graph.svg)
- [UI Flow](diagrams/ui-flow.svg)
- [Coverage Map](diagrams/coverage-map.svg)

---

*Generated by [CodeTruth-MCP](https://github.com/yourusername/CodeTruth-MCP)*
"""

        (self.audit_dir / "README.md").write_text(content)

    def _gate_status(self, gates: dict[str, Any], level: int) -> str:
        """Get gate status emoji."""
        results = gates.get("results", [])
        for result in results:
            if result.get("gate") == level:
                status = result.get("status", "unknown")
                return {
                    "passed": "✅ Passed",
                    "failed": "❌ Failed",
                    "warning": "⚠️ Warning",
                    "skipped": "⏭️ Skipped",
                }.get(status, "❓ Unknown")
        return "⏭️ Not Run"

    async def _generate_findings(self, results: dict[str, Any]) -> None:
        """Generate the detailed findings report."""
        findings = results.get("findings", [])

        content = """# Audit Findings

All findings from the CodeTruth audit, organized by severity and type.

"""
        # Group by severity
        by_severity: dict[str, list[dict[str, Any]]] = {
            "critical": [],
            "error": [],
            "warning": [],
            "note": [],
            "info": [],
        }

        for finding in findings:
            severity = finding.get("severity", "info")
            by_severity.setdefault(severity, []).append(finding)

        severity_emoji = {
            "critical": "🔴",
            "error": "🟠",
            "warning": "🟡",
            "note": "🔵",
            "info": "⚪",
        }

        for severity in ["critical", "error", "warning", "note", "info"]:
            items = by_severity.get(severity, [])
            if not items:
                continue

            emoji = severity_emoji.get(severity, "•")
            content += f"## {emoji} {severity.upper()} ({len(items)})\n\n"

            for finding in items:
                content += f"### {finding.get('type', 'Unknown')}\n\n"
                content += f"**Message:** {finding.get('message', 'No message')}\n\n"

                if finding.get("file"):
                    loc = f"`{finding['file']}`"
                    if finding.get("line"):
                        loc += f":{finding['line']}"
                    content += f"**Location:** {loc}\n\n"

                if finding.get("rule_id"):
                    content += f"**Rule:** `{finding['rule_id']}`\n\n"

                if finding.get("evidence"):
                    content += f"**Evidence:**\n```\n{finding['evidence'][:500]}\n```\n\n"

                if finding.get("suggested_fix"):
                    content += f"**Suggested Fix:** {finding['suggested_fix']}\n\n"

                content += "---\n\n"

        (self.audit_dir / "FINDINGS.md").write_text(content)

    async def _generate_truth_table(self, results: dict[str, Any]) -> None:
        """Generate the Feature Truth Table."""
        truth_table = results.get("truth_table", {})

        if truth_table.get("markdown"):
            content = truth_table["markdown"]
        else:
            content = self.markdown_generator.generate_truth_table(truth_table)

        (self.audit_dir / "TRUTH_TABLE.md").write_text(content)

    async def _generate_fix_plan(self, results: dict[str, Any]) -> None:
        """Generate the prioritized fix plan."""
        findings = results.get("findings", [])

        content = """# Fix Plan

Prioritized remediation plan based on audit findings.

## Priority Order

1. **Critical Security Issues** - Must fix immediately
2. **Build/Type Errors** - Blocking issues
3. **Dead Code & Unwired UI** - Technical debt
4. **Warnings & Notes** - Code quality improvements

"""
        # Group findings by priority
        critical = [f for f in findings if f.get("severity") == "critical"]
        errors = [f for f in findings if f.get("severity") == "error"]
        warnings = [f for f in findings if f.get("severity") == "warning"]

        if critical:
            content += "## 🔴 Critical (Fix Immediately)\n\n"
            for i, finding in enumerate(critical, 1):
                content += f"### {i}. {finding.get('type', 'Unknown')}\n\n"
                content += f"**File:** `{finding.get('file', 'unknown')}`\n\n"
                content += f"**Issue:** {finding.get('message', 'No message')}\n\n"
                if finding.get("suggested_fix"):
                    content += f"**Fix:** {finding['suggested_fix']}\n\n"
                content += "**Acceptance Test:**\n"
                content += "- [ ] Issue no longer appears in scan\n"
                content += "- [ ] No regression in related functionality\n\n"

        if errors:
            content += "## 🟠 Errors (Fix This Sprint)\n\n"
            for i, finding in enumerate(errors, 1):
                content += f"### {i}. {finding.get('type', 'Unknown')}\n\n"
                content += f"**File:** `{finding.get('file', 'unknown')}`\n\n"
                content += f"**Issue:** {finding.get('message', 'No message')}\n\n"

        if warnings:
            content += f"## 🟡 Warnings ({len(warnings)} items)\n\n"
            content += "See [FINDINGS.md](FINDINGS.md) for complete list.\n\n"

        content += """
## Verification Steps

After implementing fixes:

1. Run `codetruth audit .` to verify issues are resolved
2. Check that no new issues were introduced
3. Ensure all quality gates pass
4. Update documentation if needed

---

*Generated by CodeTruth-MCP*
"""

        (self.audit_dir / "FIX_PLAN.md").write_text(content)

    async def _generate_category_reports(self, results: dict[str, Any]) -> None:
        """Generate category-specific reports."""
        findings = results.get("findings", [])
        reports_dir = self.audit_dir / "reports"

        # Security report
        security_findings = [
            f for f in findings
            if f.get("type") in ["security_vuln", "secret_leak", "dependency_vuln"]
        ]
        content = self.markdown_generator.generate_category_report(
            "Security", security_findings
        )
        (reports_dir / "security.md").write_text(content)

        # Dead code report
        dead_code = [
            f for f in findings
            if f.get("type") in ["dead_code", "unreachable_code", "orphan_component"]
        ]
        content = self.markdown_generator.generate_category_report(
            "Dead Code", dead_code
        )
        (reports_dir / "dead-code.md").write_text(content)

        # Type errors
        type_errors = [f for f in findings if f.get("type") == "type_error"]
        content = self.markdown_generator.generate_category_report(
            "Type Errors", type_errors
        )
        (reports_dir / "type-errors.md").write_text(content)

        # Lint errors
        lint_errors = [f for f in findings if f.get("type") == "lint_error"]
        content = self.markdown_generator.generate_category_report(
            "Lint Errors", lint_errors
        )
        (reports_dir / "lint-errors.md").write_text(content)

        # Contract issues
        contracts = [
            f for f in findings if f.get("type") == "contract_mismatch"
        ]
        content = self.markdown_generator.generate_category_report(
            "API Contracts", contracts
        )
        (reports_dir / "contracts.md").write_text(content)

    async def _generate_diagrams(self, results: dict[str, Any]) -> None:
        """Generate SVG diagrams."""
        diagrams_dir = self.audit_dir / "diagrams"
        inventory = results.get("inventory", {})

        # Architecture diagram
        svg = self.svg_generator.generate_architecture_diagram(inventory)
        (diagrams_dir / "architecture.svg").write_text(svg)

        # Call graph
        call_graph = results.get("call_graph", {})
        svg = self.svg_generator.generate_call_graph(call_graph)
        (diagrams_dir / "call-graph.svg").write_text(svg)

        # Dependency graph
        svg = self.svg_generator.generate_dependency_graph(inventory)
        (diagrams_dir / "dependency-graph.svg").write_text(svg)

        # UI flow
        ui_components = inventory.get("ui_components", [])
        ui_routes = inventory.get("ui_routes", [])
        svg = self.svg_generator.generate_ui_flow(ui_components, ui_routes)
        (diagrams_dir / "ui-flow.svg").write_text(svg)

        # Coverage map
        coverage = results.get("coverage", {})
        svg = self.svg_generator.generate_coverage_map(coverage)
        (diagrams_dir / "coverage-map.svg").write_text(svg)

    async def _save_data(self, results: dict[str, Any]) -> None:
        """Save raw data as JSON."""
        data_dir = self.audit_dir / "data"

        # Inventory
        inventory = results.get("inventory", {})
        with open(data_dir / "inventory.json", "w") as f:
            json.dump(inventory, f, indent=2, default=str)

        # Findings
        findings = results.get("findings", [])
        with open(data_dir / "findings.json", "w") as f:
            json.dump(findings, f, indent=2, default=str)

        # Truth table
        truth_table = results.get("truth_table", {})
        with open(data_dir / "truth-table.json", "w") as f:
            json.dump(truth_table, f, indent=2, default=str)

        # Full results
        with open(data_dir / "full-results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

    async def _copy_evidence(self, results: dict[str, Any]) -> None:
        """Copy evidence artifacts."""
        # This would copy traces, screenshots, logs from the audit
        # For now, create placeholder
        evidence_dir = self.audit_dir / "evidence"

        # Create index of evidence
        evidence_index = {
            "traces": [],
            "screenshots": [],
            "logs": [],
        }

        with open(evidence_dir / "index.json", "w") as f:
            json.dump(evidence_index, f, indent=2)
