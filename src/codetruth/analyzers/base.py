"""
Base Analyzer

Abstract base class for all analyzers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class AnalysisResult(BaseModel):
    """Result of running an analyzer."""

    analyzer_name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_ms: int | None = None

    # Status
    success: bool = True
    error_message: str | None = None

    # Results
    findings_count: int = 0
    findings: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    # Metadata
    files_analyzed: int = 0
    commands_run: list[str] = Field(default_factory=list)


class BaseAnalyzer(ABC):
    """Abstract base class for analyzers."""

    name: str = "base"
    description: str = "Base analyzer"

    @abstractmethod
    async def run(
        self,
        repo_path: Path,
        options: dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        """
        Run the analyzer.

        Args:
            repo_path: Path to the repository
            options: Analyzer options
            evidence_vault: Optional evidence vault for storing findings

        Returns:
            Analysis result
        """
        pass

    def _is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored."""
        ignore_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ]
        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)
