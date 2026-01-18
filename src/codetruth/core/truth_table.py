"""
Milestone 20: Feature Truth Table Generator

Creates a comprehensive truth table for every feature in the codebase.
Each feature is verified against multiple criteria to determine its true status.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from codetruth.core.evidence import EvidenceVault, Evidence, EvidenceType, Severity


class FeatureStatus(str, Enum):
    """Status of a feature based on evidence."""

    WORKING = "working"  # Fully functional, tested, gates pass
    PARTIAL = "partial"  # Some steps work, others fail
    STUBBED = "stubbed"  # Placeholder/TODO/mock return
    UNWIRED = "unwired"  # UI exists but no handler/route not registered
    DEAD = "dead"  # Unreachable code
    BROKEN = "broken"  # Throws/fails tests
    UNKNOWN = "unknown"  # Not enough evidence to determine


class FeatureType(str, Enum):
    """Types of features."""

    UI_PAGE = "ui_page"
    UI_COMPONENT = "ui_component"
    UI_FLOW = "ui_flow"
    API_ENDPOINT = "api_endpoint"
    SERVICE = "service"
    BACKGROUND_JOB = "background_job"
    CLI_COMMAND = "cli_command"
    WEBHOOK = "webhook"
    INTEGRATION = "integration"


class ExecutionStep(BaseModel):
    """A step in the feature execution path."""

    layer: str  # ui, api, service, db, external
    component: str
    file_path: str | None = None
    function: str | None = None
    is_verified: bool = False
    evidence_id: str | None = None


class FeatureEntry(BaseModel):
    """A single feature in the truth table."""

    id: str
    name: str
    feature_type: FeatureType
    description: str | None = None

    # Spec source
    spec_source: str | None = None  # Where it's defined (README, ticket, etc.)
    spec_reference: str | None = None  # Link or reference

    # Execution path: UI -> API -> Service -> DB
    execution_path: list[ExecutionStep] = Field(default_factory=list)

    # Verification checks
    is_reachable: bool | None = None  # Can code path be reached?
    is_wired: bool | None = None  # Are handlers bound?
    is_observable: bool | None = None  # Network/state/DB effects?
    is_tested: bool | None = None  # Has test coverage?
    gates_pass: bool | None = None  # Quality gates pass?

    # Test information
    test_name: str | None = None
    test_file: str | None = None
    test_assertions: list[str] = Field(default_factory=list)

    # Status
    status: FeatureStatus = FeatureStatus.UNKNOWN
    confidence: float = 0.0  # 0-1 confidence in status

    # Blockers and issues
    blockers: list[str] = Field(default_factory=list)
    related_evidence: list[str] = Field(default_factory=list)

    # Metadata
    last_verified: datetime | None = None
    verified_commit: str | None = None


class TruthTable(BaseModel):
    """The complete Feature Truth Table."""

    repo_path: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    commit_sha: str | None = None

    # Features
    features: list[FeatureEntry] = Field(default_factory=list)

    # Summary statistics
    total_features: int = 0
    working_count: int = 0
    partial_count: int = 0
    stubbed_count: int = 0
    unwired_count: int = 0
    dead_count: int = 0
    broken_count: int = 0
    unknown_count: int = 0

    def add_feature(self, feature: FeatureEntry) -> None:
        """Add a feature and update statistics."""
        self.features.append(feature)
        self._update_stats()

    def _update_stats(self) -> None:
        """Update summary statistics."""
        self.total_features = len(self.features)
        self.working_count = sum(1 for f in self.features if f.status == FeatureStatus.WORKING)
        self.partial_count = sum(1 for f in self.features if f.status == FeatureStatus.PARTIAL)
        self.stubbed_count = sum(1 for f in self.features if f.status == FeatureStatus.STUBBED)
        self.unwired_count = sum(1 for f in self.features if f.status == FeatureStatus.UNWIRED)
        self.dead_count = sum(1 for f in self.features if f.status == FeatureStatus.DEAD)
        self.broken_count = sum(1 for f in self.features if f.status == FeatureStatus.BROKEN)
        self.unknown_count = sum(1 for f in self.features if f.status == FeatureStatus.UNKNOWN)

    def to_markdown(self) -> str:
        """Export truth table as markdown."""
        lines = [
            "# Feature Truth Table",
            "",
            f"**Repository:** {self.repo_path}",
            f"**Generated:** {self.generated_at.isoformat()}",
            f"**Commit:** {self.commit_sha or 'N/A'}",
            "",
            "## Summary",
            "",
            f"| Status | Count | Percentage |",
            f"|--------|-------|------------|",
            f"| Working | {self.working_count} | {self._pct(self.working_count)}% |",
            f"| Partial | {self.partial_count} | {self._pct(self.partial_count)}% |",
            f"| Stubbed | {self.stubbed_count} | {self._pct(self.stubbed_count)}% |",
            f"| Unwired | {self.unwired_count} | {self._pct(self.unwired_count)}% |",
            f"| Dead | {self.dead_count} | {self._pct(self.dead_count)}% |",
            f"| Broken | {self.broken_count} | {self._pct(self.broken_count)}% |",
            f"| Unknown | {self.unknown_count} | {self._pct(self.unknown_count)}% |",
            f"| **Total** | **{self.total_features}** | **100%** |",
            "",
            "## Features",
            "",
            "| Feature | Type | Status | Reachable | Wired | Observable | Tested | Blockers |",
            "|---------|------|--------|-----------|-------|------------|--------|----------|",
        ]

        for f in self.features:
            blockers = "; ".join(f.blockers[:2]) if f.blockers else "-"
            lines.append(
                f"| {f.name} | {f.feature_type.value} | {f.status.value} | "
                f"{self._bool_icon(f.is_reachable)} | {self._bool_icon(f.is_wired)} | "
                f"{self._bool_icon(f.is_observable)} | {self._bool_icon(f.is_tested)} | {blockers} |"
            )

        # Add detailed sections for non-working features
        broken_features = [f for f in self.features if f.status == FeatureStatus.BROKEN]
        if broken_features:
            lines.extend(["", "## Broken Features (Require Immediate Attention)", ""])
            for f in broken_features:
                lines.extend(
                    [
                        f"### {f.name}",
                        f"**Type:** {f.feature_type.value}",
                        f"**Blockers:**",
                    ]
                )
                for blocker in f.blockers:
                    lines.append(f"- {blocker}")
                lines.append("")

        unwired_features = [f for f in self.features if f.status == FeatureStatus.UNWIRED]
        if unwired_features:
            lines.extend(["", "## Unwired Features (UI exists but not connected)", ""])
            for f in unwired_features:
                lines.extend(
                    [
                        f"### {f.name}",
                        f"**Type:** {f.feature_type.value}",
                        f"**Blockers:**",
                    ]
                )
                for blocker in f.blockers:
                    lines.append(f"- {blocker}")
                lines.append("")

        return "\n".join(lines)

    def _pct(self, count: int) -> str:
        """Calculate percentage."""
        if self.total_features == 0:
            return "0.0"
        return f"{(count / self.total_features) * 100:.1f}"

    def _bool_icon(self, value: bool | None) -> str:
        """Convert boolean to icon."""
        if value is None:
            return "?"
        return "+" if value else "-"


class TruthTableGenerator:
    """Generates Feature Truth Table from inventory and evidence."""

    def __init__(self, repo_path: Path, evidence_vault: EvidenceVault):
        self.repo_path = repo_path
        self.evidence_vault = evidence_vault

    async def generate(
        self,
        spec_source: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Generate the truth table."""
        from codetruth.core.inventory import RepoInventory

        # Generate inventory
        inventory = RepoInventory(self.repo_path)
        inv_data = await inventory.generate(include_ast=True)

        # Create truth table
        truth_table = TruthTable(repo_path=str(self.repo_path))

        # Add API routes as features
        for route in inv_data.get("api_routes", []):
            feature = await self._create_api_feature(route)
            truth_table.add_feature(feature)

        # Add UI pages as features
        for ui_route in inv_data.get("ui_routes", []):
            feature = await self._create_ui_route_feature(ui_route)
            truth_table.add_feature(feature)

        # Add UI components as features
        for component in inv_data.get("ui_components", []):
            feature = await self._create_ui_component_feature(component)
            truth_table.add_feature(feature)

        # Verify features against evidence
        await self._verify_features(truth_table)

        # Update final statistics
        truth_table._update_stats()

        # Return in requested format
        if output_format == "markdown":
            return {"markdown": truth_table.to_markdown()}
        elif output_format == "html":
            return {"html": self._to_html(truth_table)}
        else:
            return truth_table.model_dump()

    async def _create_api_feature(self, route: dict[str, Any]) -> FeatureEntry:
        """Create feature entry from API route."""
        feature_id = f"api:{route['method']}:{route['path']}"
        name = f"{route['method']} {route['path']}"

        return FeatureEntry(
            id=feature_id,
            name=name,
            feature_type=FeatureType.API_ENDPOINT,
            execution_path=[
                ExecutionStep(
                    layer="api",
                    component=route["handler_function"],
                    file_path=route["handler_file"],
                    function=route["handler_function"],
                )
            ],
            is_reachable=route.get("is_registered", True),
        )

    async def _create_ui_route_feature(self, route: dict[str, Any]) -> FeatureEntry:
        """Create feature entry from UI route."""
        feature_id = f"ui:page:{route['path']}"
        name = f"Page: {route['path']}"

        return FeatureEntry(
            id=feature_id,
            name=name,
            feature_type=FeatureType.UI_PAGE,
            execution_path=[
                ExecutionStep(
                    layer="ui",
                    component=route["component"],
                    file_path=route["file_path"],
                )
            ],
        )

    async def _create_ui_component_feature(self, component: dict[str, Any]) -> FeatureEntry:
        """Create feature entry from UI component."""
        feature_id = f"ui:component:{component['name']}"

        return FeatureEntry(
            id=feature_id,
            name=component["name"],
            feature_type=FeatureType.UI_COMPONENT,
            execution_path=[
                ExecutionStep(
                    layer="ui",
                    component=component["name"],
                    file_path=component["file_path"],
                )
            ],
        )

    async def _verify_features(self, truth_table: TruthTable) -> None:
        """Verify features against evidence vault."""
        for feature in truth_table.features:
            await self._verify_single_feature(feature)

    async def _verify_single_feature(self, feature: FeatureEntry) -> None:
        """Verify a single feature."""
        blockers: list[str] = []
        related_evidence: list[str] = []

        # Search for related evidence
        for step in feature.execution_path:
            if step.file_path:
                evidences = await self.evidence_vault.search(
                    repo_path=str(self.repo_path),
                    file_path=step.file_path,
                    limit=20,
                )

                for e in evidences:
                    related_evidence.append(e.id)

                    # Check for specific evidence types
                    if e.evidence_type == EvidenceType.DEAD_CODE:
                        feature.is_reachable = False
                        blockers.append(f"Dead code: {e.message}")

                    elif e.evidence_type == EvidenceType.UNWIRED_UI:
                        feature.is_wired = False
                        blockers.append(f"Unwired: {e.message}")

                    elif e.evidence_type == EvidenceType.UNBOUND_HANDLER:
                        feature.is_wired = False
                        blockers.append(f"Unbound handler: {e.message}")

                    elif e.evidence_type == EvidenceType.TEST_FAILURE:
                        feature.is_tested = False
                        blockers.append(f"Test failure: {e.message}")

                    elif e.evidence_type in [
                        EvidenceType.LINT_ERROR,
                        EvidenceType.TYPE_ERROR,
                    ]:
                        if e.severity in [Severity.ERROR, Severity.CRITICAL]:
                            blockers.append(f"{e.evidence_type.value}: {e.message}")

        feature.blockers = blockers
        feature.related_evidence = related_evidence

        # Determine status based on evidence
        feature.status = self._determine_status(feature)
        feature.confidence = self._calculate_confidence(feature)
        feature.last_verified = datetime.utcnow()

    def _determine_status(self, feature: FeatureEntry) -> FeatureStatus:
        """Determine feature status based on verification results."""
        # If explicitly marked as unreachable
        if feature.is_reachable is False:
            return FeatureStatus.DEAD

        # If not wired (UI exists but no handler)
        if feature.is_wired is False:
            return FeatureStatus.UNWIRED

        # If has critical blockers
        critical_keywords = ["error", "fail", "crash", "exception"]
        has_critical = any(
            any(kw in b.lower() for kw in critical_keywords) for b in feature.blockers
        )
        if has_critical:
            return FeatureStatus.BROKEN

        # If has TODO/stub markers
        stub_keywords = ["todo", "stub", "mock", "placeholder", "not implemented"]
        has_stub = any(
            any(kw in b.lower() for kw in stub_keywords) for b in feature.blockers
        )
        if has_stub:
            return FeatureStatus.STUBBED

        # If partially working
        if feature.blockers and len(feature.blockers) < 3:
            return FeatureStatus.PARTIAL

        # If we have positive verification
        if (
            feature.is_reachable is True
            and feature.is_wired is not False
            and feature.is_tested is True
        ):
            return FeatureStatus.WORKING

        # Default to unknown if not enough evidence
        return FeatureStatus.UNKNOWN

    def _calculate_confidence(self, feature: FeatureEntry) -> float:
        """Calculate confidence in the status determination."""
        checks = [
            feature.is_reachable is not None,
            feature.is_wired is not None,
            feature.is_observable is not None,
            feature.is_tested is not None,
            feature.gates_pass is not None,
        ]

        verified_count = sum(1 for c in checks if c)
        return verified_count / len(checks)

    def _to_html(self, truth_table: TruthTable) -> str:
        """Convert truth table to HTML."""
        status_colors = {
            FeatureStatus.WORKING: "#28a745",
            FeatureStatus.PARTIAL: "#ffc107",
            FeatureStatus.STUBBED: "#6c757d",
            FeatureStatus.UNWIRED: "#fd7e14",
            FeatureStatus.DEAD: "#868686",
            FeatureStatus.BROKEN: "#dc3545",
            FeatureStatus.UNKNOWN: "#17a2b8",
        }

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Feature Truth Table - {truth_table.repo_path}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status {{ padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-card {{ padding: 15px; border-radius: 8px; background: #f8f9fa; }}
        .bool-true {{ color: #28a745; font-weight: bold; }}
        .bool-false {{ color: #dc3545; font-weight: bold; }}
        .bool-unknown {{ color: #6c757d; }}
    </style>
</head>
<body>
    <h1>Feature Truth Table</h1>
    <p><strong>Repository:</strong> {truth_table.repo_path}</p>
    <p><strong>Generated:</strong> {truth_table.generated_at.isoformat()}</p>

    <div class="summary">
        <div class="summary-card">
            <strong>Total Features:</strong> {truth_table.total_features}
        </div>
        <div class="summary-card" style="border-left: 4px solid {status_colors[FeatureStatus.WORKING]}">
            <strong>Working:</strong> {truth_table.working_count}
        </div>
        <div class="summary-card" style="border-left: 4px solid {status_colors[FeatureStatus.BROKEN]}">
            <strong>Broken:</strong> {truth_table.broken_count}
        </div>
        <div class="summary-card" style="border-left: 4px solid {status_colors[FeatureStatus.UNWIRED]}">
            <strong>Unwired:</strong> {truth_table.unwired_count}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Feature</th>
                <th>Type</th>
                <th>Status</th>
                <th>Reachable</th>
                <th>Wired</th>
                <th>Observable</th>
                <th>Tested</th>
                <th>Confidence</th>
                <th>Blockers</th>
            </tr>
        </thead>
        <tbody>
"""

        for f in truth_table.features:
            status_color = status_colors.get(f.status, "#6c757d")
            blockers_html = "<br>".join(f.blockers[:3]) if f.blockers else "-"

            html += f"""
            <tr>
                <td>{f.name}</td>
                <td>{f.feature_type.value}</td>
                <td><span class="status" style="background-color: {status_color}">{f.status.value}</span></td>
                <td class="{self._bool_class(f.is_reachable)}">{self._bool_text(f.is_reachable)}</td>
                <td class="{self._bool_class(f.is_wired)}">{self._bool_text(f.is_wired)}</td>
                <td class="{self._bool_class(f.is_observable)}">{self._bool_text(f.is_observable)}</td>
                <td class="{self._bool_class(f.is_tested)}">{self._bool_text(f.is_tested)}</td>
                <td>{f.confidence:.0%}</td>
                <td>{blockers_html}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</body>
</html>
"""
        return html

    def _bool_class(self, value: bool | None) -> str:
        """Get CSS class for boolean value."""
        if value is None:
            return "bool-unknown"
        return "bool-true" if value else "bool-false"

    def _bool_text(self, value: bool | None) -> str:
        """Get display text for boolean value."""
        if value is None:
            return "?"
        return "Yes" if value else "No"
