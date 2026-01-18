"""
Analyzers Module

Provides various code analyzers for:
- Dead code detection
- UI wiring audit
- Linting
- Type checking
- SAST security scanning
- Dependency auditing
- Secret scanning
- API contract validation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codetruth.analyzers.base import BaseAnalyzer, AnalysisResult
from codetruth.analyzers.dead_code import DeadCodeAnalyzer
from codetruth.analyzers.ui_wiring import UIWiringAnalyzer
from codetruth.analyzers.lint import LintAnalyzer
from codetruth.analyzers.type_check import TypeCheckAnalyzer
from codetruth.analyzers.sast import SASTAnalyzer
from codetruth.analyzers.secrets import SecretScanner
from codetruth.analyzers.dependencies import DependencyAuditor
from codetruth.analyzers.contracts import APIContractAnalyzer

if TYPE_CHECKING:
    pass

__all__ = [
    "BaseAnalyzer",
    "AnalysisResult",
    "DeadCodeAnalyzer",
    "UIWiringAnalyzer",
    "LintAnalyzer",
    "TypeCheckAnalyzer",
    "SASTAnalyzer",
    "SecretScanner",
    "DependencyAuditor",
    "APIContractAnalyzer",
    "get_analyzer",
]


# Analyzer registry
_ANALYZER_MAP = {
    "dead_code_audit": DeadCodeAnalyzer,
    "dead_code": DeadCodeAnalyzer,
    "ui_wiring_audit": UIWiringAnalyzer,
    "ui_wiring": UIWiringAnalyzer,
    "lint_audit": LintAnalyzer,
    "lint": LintAnalyzer,
    "type_check": TypeCheckAnalyzer,
    "sast_scan": SASTAnalyzer,
    "sast": SASTAnalyzer,
    "secret_scan": SecretScanner,
    "secrets": SecretScanner,
    "dependency_audit": DependencyAuditor,
    "dependencies": DependencyAuditor,
    "api_contract_audit": APIContractAnalyzer,
    "contracts": APIContractAnalyzer,
}


def get_analyzer(name: str) -> BaseAnalyzer | None:
    """
    Get an analyzer instance by name.

    Args:
        name: Analyzer name or tool name

    Returns:
        Analyzer instance or None
    """
    analyzer_class = _ANALYZER_MAP.get(name)
    if analyzer_class:
        return analyzer_class()
    return None
