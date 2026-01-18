"""
Markdown Report Generator

Generates markdown reports for audit findings.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class MarkdownReportGenerator:
    """Generates markdown reports."""

    def generate_truth_table(self, truth_table: dict[str, Any]) -> str:
        """Generate markdown truth table."""
        features = truth_table.get("features", [])

        content = f"""# Feature Truth Table

**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

## Summary

| Status | Count |
|--------|-------|
| Working | {truth_table.get('working_count', 0)} |
| Partial | {truth_table.get('partial_count', 0)} |
| Stubbed | {truth_table.get('stubbed_count', 0)} |
| Unwired | {truth_table.get('unwired_count', 0)} |
| Dead | {truth_table.get('dead_count', 0)} |
| Broken | {truth_table.get('broken_count', 0)} |
| Unknown | {truth_table.get('unknown_count', 0)} |
| **Total** | **{truth_table.get('total_features', 0)}** |

## Feature Status

| Feature | Type | Status | Reachable | Wired | Tested | Blockers |
|---------|------|--------|-----------|-------|--------|----------|
"""

        for feature in features:
            blockers = "; ".join(feature.get("blockers", [])[:2]) or "-"
            status_emoji = self._status_emoji(feature.get("status", "unknown"))

            content += f"| {feature.get('name', 'Unknown')} "
            content += f"| {feature.get('feature_type', 'unknown')} "
            content += f"| {status_emoji} {feature.get('status', 'unknown')} "
            content += f"| {self._bool_str(feature.get('is_reachable'))} "
            content += f"| {self._bool_str(feature.get('is_wired'))} "
            content += f"| {self._bool_str(feature.get('is_tested'))} "
            content += f"| {blockers} |\n"

        return content

    def generate_category_report(
        self,
        category: str,
        findings: list[dict[str, Any]],
    ) -> str:
        """Generate a category-specific report."""
        content = f"""# {category} Report

**Total Findings:** {len(findings)}

"""

        if not findings:
            content += "*No issues found in this category.*\n"
            return content

        # Group by severity
        by_severity: dict[str, list[dict[str, Any]]] = {}
        for finding in findings:
            severity = finding.get("severity", "info")
            by_severity.setdefault(severity, []).append(finding)

        for severity in ["critical", "error", "warning", "note", "info"]:
            items = by_severity.get(severity, [])
            if not items:
                continue

            content += f"## {self._severity_emoji(severity)} {severity.upper()} ({len(items)})\n\n"

            for finding in items:
                content += f"### {finding.get('message', 'No message')}\n\n"

                if finding.get("file"):
                    loc = f"`{finding['file']}`"
                    if finding.get("line"):
                        loc += f":{finding['line']}"
                    content += f"**Location:** {loc}\n\n"

                if finding.get("rule_id"):
                    content += f"**Rule:** `{finding['rule_id']}`\n\n"

                if finding.get("description"):
                    content += f"{finding['description']}\n\n"

                if finding.get("suggested_fix"):
                    content += f"**Suggested Fix:** {finding['suggested_fix']}\n\n"

                content += "---\n\n"

        return content

    def _status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        return {
            "working": "✅",
            "partial": "🟡",
            "stubbed": "⬜",
            "unwired": "🔌",
            "dead": "💀",
            "broken": "❌",
            "unknown": "❓",
        }.get(status, "•")

    def _severity_emoji(self, severity: str) -> str:
        """Get emoji for severity."""
        return {
            "critical": "🔴",
            "error": "🟠",
            "warning": "🟡",
            "note": "🔵",
            "info": "⚪",
        }.get(severity, "•")

    def _bool_str(self, value: bool | None) -> str:
        """Convert boolean to string."""
        if value is None:
            return "?"
        return "✓" if value else "✗"
