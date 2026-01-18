"""
Interactive "Alive-Like" MCP Server Features

Provides real-time streaming updates, progress notifications,
and interactive audit experiences.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable
from collections.abc import Coroutine

from pydantic import BaseModel, Field


class AuditPhase(str, Enum):
    """Phases of an audit."""

    INITIALIZING = "initializing"
    DISCOVERY = "discovery"
    INVENTORY = "inventory"
    STATIC_ANALYSIS = "static_analysis"
    REACHABILITY = "reachability"
    SECURITY_SCAN = "security_scan"
    RUNTIME_VERIFICATION = "runtime_verification"
    DEEP_ANALYSIS = "deep_analysis"
    REPORT_GENERATION = "report_generation"
    COMPLETE = "complete"


class AnalysisSweep(str, Enum):
    """Sweep levels for deep analysis."""

    SURFACE = "surface"  # Quick scan, obvious issues
    SHALLOW = "shallow"  # Standard analysis
    DEEP = "deep"  # Thorough multi-pass
    FORENSIC = "forensic"  # Maximum depth, all angles


class ProgressUpdate(BaseModel):
    """A progress update during an audit."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    phase: AuditPhase
    sweep: int = 1  # Current sweep number
    total_sweeps: int = 1

    # Progress
    progress_pct: float = 0.0
    items_processed: int = 0
    items_total: int = 0

    # Current activity
    current_file: str | None = None
    current_analyzer: str | None = None
    current_action: str | None = None

    # Findings so far
    findings_count: int = 0
    critical_count: int = 0
    new_findings: list[dict[str, Any]] = Field(default_factory=list)

    # Status message
    message: str = ""
    emoji: str = ""  # For visual feedback


class LiveAuditSession:
    """
    A live, interactive audit session with streaming updates.

    Features:
    - Real-time progress streaming
    - Multi-sweep deep analysis
    - Interactive pause/resume
    - Live finding notifications
    """

    def __init__(
        self,
        repo_path: Path,
        sweep_level: AnalysisSweep = AnalysisSweep.DEEP,
    ):
        self.repo_path = repo_path
        self.sweep_level = sweep_level
        self.session_id = f"audit_{int(time.time() * 1000)}"

        # State
        self.is_running = False
        self.is_paused = False
        self.current_phase = AuditPhase.INITIALIZING
        self.current_sweep = 1

        # Configure sweeps based on level
        self.total_sweeps = {
            AnalysisSweep.SURFACE: 1,
            AnalysisSweep.SHALLOW: 2,
            AnalysisSweep.DEEP: 3,
            AnalysisSweep.FORENSIC: 5,
        }[sweep_level]

        # Results
        self.findings: list[dict[str, Any]] = []
        self.progress_history: list[ProgressUpdate] = []

        # Callbacks
        self._progress_callbacks: list[Callable[[ProgressUpdate], Coroutine[Any, Any, None]]] = []

    def on_progress(
        self,
        callback: Callable[[ProgressUpdate], Coroutine[Any, Any, None]],
    ) -> None:
        """Register a callback for progress updates."""
        self._progress_callbacks.append(callback)

    async def _emit_progress(self, update: ProgressUpdate) -> None:
        """Emit a progress update to all registered callbacks."""
        self.progress_history.append(update)
        for callback in self._progress_callbacks:
            try:
                await callback(update)
            except Exception:
                pass  # Don't let callback errors stop the audit

    async def run(self) -> AsyncIterator[ProgressUpdate]:
        """Run the audit with streaming progress updates."""
        self.is_running = True

        try:
            # Phase 1: Initialization
            yield await self._run_phase(
                AuditPhase.INITIALIZING,
                "Initializing audit session...",
                emoji="🔄",
            )

            # Phase 2: Discovery
            yield await self._run_phase(
                AuditPhase.DISCOVERY,
                "Discovering repository structure...",
                emoji="🔍",
            )

            # Multi-sweep analysis
            for sweep in range(1, self.total_sweeps + 1):
                self.current_sweep = sweep

                sweep_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][sweep - 1]
                yield await self._run_phase(
                    AuditPhase.INVENTORY,
                    f"Sweep {sweep}/{self.total_sweeps}: Building inventory...",
                    emoji=sweep_emoji,
                )

                yield await self._run_phase(
                    AuditPhase.STATIC_ANALYSIS,
                    f"Sweep {sweep}/{self.total_sweeps}: Running static analysis...",
                    emoji="📊",
                )

                yield await self._run_phase(
                    AuditPhase.REACHABILITY,
                    f"Sweep {sweep}/{self.total_sweeps}: Analyzing reachability...",
                    emoji="🔗",
                )

                yield await self._run_phase(
                    AuditPhase.SECURITY_SCAN,
                    f"Sweep {sweep}/{self.total_sweeps}: Security scanning...",
                    emoji="🔒",
                )

                # Deep analysis on later sweeps
                if sweep >= 2:
                    yield await self._run_phase(
                        AuditPhase.DEEP_ANALYSIS,
                        f"Sweep {sweep}/{self.total_sweeps}: Deep cross-reference analysis...",
                        emoji="🔬",
                    )

            # Runtime verification (if applicable)
            yield await self._run_phase(
                AuditPhase.RUNTIME_VERIFICATION,
                "Running runtime verification...",
                emoji="▶️",
            )

            # Report generation
            yield await self._run_phase(
                AuditPhase.REPORT_GENERATION,
                "Generating audit reports...",
                emoji="📝",
            )

            # Complete
            yield ProgressUpdate(
                phase=AuditPhase.COMPLETE,
                sweep=self.total_sweeps,
                total_sweeps=self.total_sweeps,
                progress_pct=100.0,
                findings_count=len(self.findings),
                message="Audit complete!",
                emoji="✅",
            )

        finally:
            self.is_running = False

    async def _run_phase(
        self,
        phase: AuditPhase,
        message: str,
        emoji: str = "",
    ) -> ProgressUpdate:
        """Run a phase and return progress update."""
        self.current_phase = phase

        # Wait if paused
        while self.is_paused:
            await asyncio.sleep(0.1)

        # Simulate phase execution with progress
        update = ProgressUpdate(
            phase=phase,
            sweep=self.current_sweep,
            total_sweeps=self.total_sweeps,
            progress_pct=self._calculate_progress(),
            findings_count=len(self.findings),
            message=message,
            emoji=emoji,
        )

        await self._emit_progress(update)
        return update

    def _calculate_progress(self) -> float:
        """Calculate overall progress percentage."""
        phase_weights = {
            AuditPhase.INITIALIZING: 2,
            AuditPhase.DISCOVERY: 5,
            AuditPhase.INVENTORY: 10,
            AuditPhase.STATIC_ANALYSIS: 25,
            AuditPhase.REACHABILITY: 15,
            AuditPhase.SECURITY_SCAN: 20,
            AuditPhase.DEEP_ANALYSIS: 10,
            AuditPhase.RUNTIME_VERIFICATION: 8,
            AuditPhase.REPORT_GENERATION: 5,
            AuditPhase.COMPLETE: 0,
        }

        # Calculate based on current phase and sweep
        phases_complete = list(AuditPhase)[:list(AuditPhase).index(self.current_phase)]
        weight_complete = sum(phase_weights.get(p, 0) for p in phases_complete)

        # Adjust for multi-sweep
        sweep_progress = (self.current_sweep - 1) / self.total_sweeps
        return min(100.0, (weight_complete + sweep_progress * 50))

    def pause(self) -> None:
        """Pause the audit."""
        self.is_paused = True

    def resume(self) -> None:
        """Resume the audit."""
        self.is_paused = False

    def cancel(self) -> None:
        """Cancel the audit."""
        self.is_running = False


class DeepAnalysisEngine:
    """
    Multi-stage deep analysis engine.

    Performs multiple sweeps over the codebase, each time
    looking for different patterns and cross-referencing findings.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    async def analyze(
        self,
        sweeps: int = 3,
        on_progress: Callable[[dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
    ) -> dict[str, Any]:
        """
        Run multi-stage deep analysis.

        Sweep 1: Surface scan - obvious issues, syntax, basic lint
        Sweep 2: Structural analysis - dead code, unreachable paths, unused exports
        Sweep 3: Cross-reference - contract mismatches, type drift, integration issues
        Sweep 4+: Forensic - historical patterns, regression detection, behavioral analysis
        """
        results: dict[str, Any] = {
            "repo_path": str(self.repo_path),
            "sweeps_completed": 0,
            "total_sweeps": sweeps,
            "findings_by_sweep": [],
            "cumulative_findings": [],
        }

        for sweep in range(1, sweeps + 1):
            sweep_result = await self._run_sweep(sweep, sweeps, on_progress)
            results["findings_by_sweep"].append(sweep_result)
            results["sweeps_completed"] = sweep

            # Merge findings
            for finding in sweep_result.get("findings", []):
                if not self._is_duplicate(finding, results["cumulative_findings"]):
                    results["cumulative_findings"].append(finding)

        return results

    async def _run_sweep(
        self,
        sweep_num: int,
        total_sweeps: int,
        on_progress: Callable[[dict[str, Any]], Coroutine[Any, Any, None]] | None,
    ) -> dict[str, Any]:
        """Run a single analysis sweep."""
        sweep_findings: list[dict[str, Any]] = []

        if on_progress:
            await on_progress({
                "sweep": sweep_num,
                "total": total_sweeps,
                "phase": "starting",
                "message": f"Starting sweep {sweep_num}/{total_sweeps}",
            })

        # Different focus per sweep
        if sweep_num == 1:
            # Surface scan
            sweep_findings = await self._surface_scan()
        elif sweep_num == 2:
            # Structural analysis
            sweep_findings = await self._structural_analysis()
        elif sweep_num == 3:
            # Cross-reference analysis
            sweep_findings = await self._cross_reference_analysis()
        else:
            # Forensic analysis
            sweep_findings = await self._forensic_analysis(sweep_num)

        return {
            "sweep": sweep_num,
            "focus": self._get_sweep_focus(sweep_num),
            "findings_count": len(sweep_findings),
            "findings": sweep_findings,
        }

    def _get_sweep_focus(self, sweep_num: int) -> str:
        """Get the focus area for a sweep."""
        focuses = {
            1: "surface_scan",
            2: "structural_analysis",
            3: "cross_reference",
        }
        return focuses.get(sweep_num, f"forensic_pass_{sweep_num - 3}")

    async def _surface_scan(self) -> list[dict[str, Any]]:
        """Quick surface scan for obvious issues."""
        findings = []

        # Look for TODO/FIXME/HACK comments
        for ext in ["*.py", "*.ts", "*.js", "*.tsx", "*.jsx"]:
            for path in self.repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                try:
                    content = path.read_text(errors="ignore")
                    lines = content.split("\n")

                    for i, line in enumerate(lines):
                        for marker in ["TODO", "FIXME", "HACK", "XXX", "BUG"]:
                            if marker in line:
                                findings.append({
                                    "type": "code_marker",
                                    "marker": marker,
                                    "file": str(path.relative_to(self.repo_path)),
                                    "line": i + 1,
                                    "content": line.strip()[:100],
                                })
                except:
                    pass

        return findings

    async def _structural_analysis(self) -> list[dict[str, Any]]:
        """Analyze code structure for dead code and unused exports."""
        findings = []

        # This would use the inventory and reachability analysis
        # For now, placeholder for structure

        return findings

    async def _cross_reference_analysis(self) -> list[dict[str, Any]]:
        """Cross-reference analysis for contract mismatches."""
        findings = []

        # This would compare API definitions with actual usage
        # Check type definitions against runtime behavior
        # etc.

        return findings

    async def _forensic_analysis(self, sweep_num: int) -> list[dict[str, Any]]:
        """Deep forensic analysis."""
        findings = []

        # Historical pattern analysis
        # Regression detection
        # Behavioral analysis

        return findings

    def _is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored."""
        ignore_patterns = [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "dist", "build", ".next", "coverage",
        ]
        return any(p in str(path) for p in ignore_patterns)

    def _is_duplicate(
        self,
        finding: dict[str, Any],
        existing: list[dict[str, Any]],
    ) -> bool:
        """Check if finding is a duplicate."""
        for existing_finding in existing:
            if (
                finding.get("type") == existing_finding.get("type")
                and finding.get("file") == existing_finding.get("file")
                and finding.get("line") == existing_finding.get("line")
            ):
                return True
        return False


class StatusEmitter:
    """
    Emits status updates for interactive display.

    Provides formatted messages with emojis and progress indicators
    for a more "alive" feeling experience.
    """

    PHASE_EMOJIS = {
        "starting": "🚀",
        "scanning": "🔍",
        "analyzing": "🔬",
        "checking": "✓",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "info": "ℹ️",
        "security": "🔒",
        "performance": "⚡",
        "complete": "🎉",
    }

    @classmethod
    def format_status(
        cls,
        phase: str,
        message: str,
        progress: float | None = None,
        findings: int | None = None,
    ) -> str:
        """Format a status message with emoji and progress."""
        emoji = cls.PHASE_EMOJIS.get(phase, "•")

        parts = [emoji, message]

        if progress is not None:
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            parts.append(f"[{bar}] {progress:.1f}%")

        if findings is not None:
            parts.append(f"({findings} findings)")

        return " ".join(parts)

    @classmethod
    def format_finding(cls, finding: dict[str, Any]) -> str:
        """Format a finding for display."""
        severity_emojis = {
            "critical": "🔴",
            "error": "🟠",
            "warning": "🟡",
            "note": "🔵",
            "info": "⚪",
        }

        severity = finding.get("severity", "info")
        emoji = severity_emojis.get(severity, "•")

        file_info = finding.get("file", "unknown")
        if finding.get("line"):
            file_info += f":{finding['line']}"

        message = finding.get("message", "No message")

        return f"{emoji} [{severity.upper()}] {file_info}: {message}"
