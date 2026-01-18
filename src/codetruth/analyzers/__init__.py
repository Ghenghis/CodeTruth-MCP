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
- Full language analyzers (Python, TypeScript, PHP, Java)
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

# Full language analyzers
from codetruth.analyzers.python_analyzer import PythonAnalyzer, PythonAnalysisReport, analyze_python
from codetruth.analyzers.typescript_analyzer import TypeScriptAnalyzer, TypeScriptAnalysisReport, analyze_typescript
from codetruth.analyzers.php_analyzer import PHPAnalyzer, PHPAnalysisReport, analyze_php
from codetruth.analyzers.java_analyzer import JavaAnalyzer, JavaAnalysisReport, analyze_java

if TYPE_CHECKING:
    pass

__all__ = [
    # Base
    "BaseAnalyzer",
    "AnalysisResult",
    # Tool-specific analyzers
    "DeadCodeAnalyzer",
    "UIWiringAnalyzer",
    "LintAnalyzer",
    "TypeCheckAnalyzer",
    "SASTAnalyzer",
    "SecretScanner",
    "DependencyAuditor",
    "APIContractAnalyzer",
    # Full language analyzers
    "PythonAnalyzer",
    "PythonAnalysisReport",
    "analyze_python",
    "TypeScriptAnalyzer",
    "TypeScriptAnalysisReport",
    "analyze_typescript",
    "PHPAnalyzer",
    "PHPAnalysisReport",
    "analyze_php",
    "JavaAnalyzer",
    "JavaAnalysisReport",
    "analyze_java",
    # Registry
    "get_analyzer",
]


# Analyzer registry
_ANALYZER_MAP = {
    # Tool-specific
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
    # Full language analyzers
    "python": PythonAnalyzer,
    "python_full": PythonAnalyzer,
    "typescript": TypeScriptAnalyzer,
    "typescript_full": TypeScriptAnalyzer,
    "react": TypeScriptAnalyzer,
    "php": PHPAnalyzer,
    "php_full": PHPAnalyzer,
    "java": JavaAnalyzer,
    "java_full": JavaAnalyzer,
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
