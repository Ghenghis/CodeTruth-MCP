"""
TypeScript/React Full Analyzer

Comprehensive TypeScript and React code analysis combining:
- Reachability graph building
- Dead code detection
- No-op handler detection
- React-specific analysis (hooks, effects, event handlers)
- Type safety analysis
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import BaseAnalyzer, AnalysisResult

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class TypeScriptFinding(BaseModel):
    """A finding from TypeScript analysis."""
    finding_id: str
    finding_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    message: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    confidence: float = 1.0
    evidence: Dict[str, Any] = Field(default_factory=dict)


class TypeScriptAnalysisReport(BaseModel):
    """Complete TypeScript analysis report."""
    repo_path: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    files_analyzed: int = 0
    total_lines: int = 0

    # Findings by category
    dead_code_findings: List[TypeScriptFinding] = Field(default_factory=list)
    no_op_findings: List[TypeScriptFinding] = Field(default_factory=list)
    react_findings: List[TypeScriptFinding] = Field(default_factory=list)
    type_findings: List[TypeScriptFinding] = Field(default_factory=list)
    security_findings: List[TypeScriptFinding] = Field(default_factory=list)

    # Statistics
    functions_found: int = 0
    components_found: int = 0
    hooks_found: int = 0
    handlers_found: int = 0

    # Framework detection
    frameworks_detected: List[str] = Field(default_factory=list)

    # Blindspots
    blindspots: List[str] = Field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return (
            len(self.dead_code_findings) +
            len(self.no_op_findings) +
            len(self.react_findings) +
            len(self.type_findings) +
            len(self.security_findings)
        )

    @property
    def all_findings(self) -> List[TypeScriptFinding]:
        return (
            self.dead_code_findings +
            self.no_op_findings +
            self.react_findings +
            self.type_findings +
            self.security_findings
        )


class TypeScriptAnalyzer(BaseAnalyzer):
    """
    Full TypeScript/React analyzer with comprehensive code analysis.

    Proof Level: P2 (STATIC_PARTIAL)
    Confidence: 0.75-0.95
    """

    name = "typescript_full"
    description = "Comprehensive TypeScript/React code analyzer"

    # Framework patterns
    FRAMEWORKS = {
        "react": [
            re.compile(r"from\s+['\"]react['\"]"),
            re.compile(r"import\s+React"),
            re.compile(r"<[A-Z]\w+"),
        ],
        "next": [
            re.compile(r"from\s+['\"]next"),
            re.compile(r"getServerSideProps|getStaticProps"),
            re.compile(r"pages/|app/"),
        ],
        "vue": [
            re.compile(r"from\s+['\"]vue['\"]"),
            re.compile(r"defineComponent"),
            re.compile(r"<template>"),
        ],
        "express": [
            re.compile(r"from\s+['\"]express['\"]"),
            re.compile(r"app\.(get|post|put|delete)\s*\("),
            re.compile(r"Router\s*\(\s*\)"),
        ],
        "nestjs": [
            re.compile(r"from\s+['\"]@nestjs"),
            re.compile(r"@Controller|@Injectable|@Module"),
        ],
        "angular": [
            re.compile(r"from\s+['\"]@angular"),
            re.compile(r"@Component|@Injectable|@NgModule"),
        ],
    }

    # Handler patterns
    HANDLER_PATTERNS = {
        "onClick": re.compile(r"onClick\s*=\s*\{?\s*(\w+)"),
        "onChange": re.compile(r"onChange\s*=\s*\{?\s*(\w+)"),
        "onSubmit": re.compile(r"onSubmit\s*=\s*\{?\s*(\w+)"),
        "onBlur": re.compile(r"onBlur\s*=\s*\{?\s*(\w+)"),
        "onFocus": re.compile(r"onFocus\s*=\s*\{?\s*(\w+)"),
        "onKeyDown": re.compile(r"onKeyDown\s*=\s*\{?\s*(\w+)"),
        "onKeyUp": re.compile(r"onKeyUp\s*=\s*\{?\s*(\w+)"),
        "onMouseOver": re.compile(r"onMouseOver\s*=\s*\{?\s*(\w+)"),
    }

    # Empty handler patterns
    EMPTY_HANDLER_PATTERNS = [
        re.compile(r"const\s+(\w+)\s*=\s*\(\s*\)\s*=>\s*\{\s*\}"),
        re.compile(r"const\s+(\w+)\s*=\s*\(\s*\)\s*=>\s*\{\s*//.*\s*\}"),
        re.compile(r"function\s+(\w+)\s*\(\s*\)\s*\{\s*\}"),
    ]

    # Debug-only handler patterns
    DEBUG_ONLY_PATTERNS = [
        re.compile(r"const\s+(\w+)\s*=\s*\(\s*\)\s*=>\s*\{\s*console\.\w+\([^)]*\)\s*;?\s*\}"),
        re.compile(r"function\s+(\w+)\s*\(\s*\)\s*\{\s*console\.\w+\([^)]*\)\s*;?\s*\}"),
    ]

    # React hook patterns
    HOOK_PATTERNS = {
        "useState": re.compile(r"useState\s*<?\w*>?\s*\("),
        "useEffect": re.compile(r"useEffect\s*\(\s*\(\)\s*=>\s*\{"),
        "useCallback": re.compile(r"useCallback\s*\(\s*\(\s*\)\s*=>\s*\{"),
        "useMemo": re.compile(r"useMemo\s*\(\s*\(\s*\)\s*=>\s*\{"),
        "useRef": re.compile(r"useRef\s*<?\w*>?\s*\("),
        "useContext": re.compile(r"useContext\s*\("),
        "useReducer": re.compile(r"useReducer\s*\("),
        "custom": re.compile(r"use[A-Z]\w+\s*\("),
    }

    # useEffect issues
    USE_EFFECT_ISSUES = {
        "missing_deps": re.compile(
            r"useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*(\w+)[^}]*\}\s*,\s*\[\s*\]\s*\)",
            re.DOTALL
        ),
        "infinite_loop": re.compile(
            r"useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*set\w+\([^)]*\)[^}]*\}\s*\)",
            re.DOTALL
        ),
    }

    # Security patterns
    SECURITY_PATTERNS = {
        "dangerouslySetInnerHTML": re.compile(
            r"dangerouslySetInnerHTML\s*=\s*\{",
            re.MULTILINE
        ),
        "eval": re.compile(
            r"\beval\s*\(",
            re.MULTILINE
        ),
        "innerHTML": re.compile(
            r"\.innerHTML\s*=",
            re.MULTILINE
        ),
        "document_write": re.compile(
            r"document\.write\s*\(",
            re.MULTILINE
        ),
        "xss_vulnerable": re.compile(
            r"window\.location\s*=\s*.*\$\{",
            re.MULTILINE
        ),
    }

    # Type issues
    TYPE_PATTERNS = {
        "any_type": re.compile(
            r":\s*any\b",
            re.MULTILINE
        ),
        "ts_ignore": re.compile(
            r"@ts-ignore|@ts-nocheck",
            re.MULTILINE
        ),
        "non_null_assertion": re.compile(
            r"\w+!\.",
            re.MULTILINE
        ),
    }

    STANDARD_BLINDSPOTS = [
        "Dynamic imports cannot be statically analyzed",
        "Runtime JSX generation (React.createElement) may hide component usage",
        "HOC-wrapped components may obscure handler chains",
        "Context values passed through providers are not traced",
        "Server components vs client components in Next.js 13+",
        "Redux/Zustand store updates may have hidden side effects",
    ]

    def __init__(self):
        self._finding_counter = 0

    def _generate_finding_id(self) -> str:
        self._finding_counter += 1
        return f"ts_{self._finding_counter:06d}"

    async def run(
        self,
        repo_path: Path,
        options: Dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        """Run comprehensive TypeScript analysis."""
        start_time = datetime.utcnow()

        try:
            report = self._analyze_directory(repo_path)

            result = AnalysisResult(
                analyzer_name=self.name,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                success=True,
                findings_count=report.total_findings,
                findings=[f.model_dump() for f in report.all_findings],
                files_analyzed=report.files_analyzed,
            )

            result.duration_ms = int(
                (result.completed_at - result.started_at).total_seconds() * 1000
            )

            return result

        except Exception as e:
            return AnalysisResult(
                analyzer_name=self.name,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                success=False,
                error_message=str(e),
            )

    def _analyze_directory(self, directory: Path) -> TypeScriptAnalysisReport:
        """Analyze all TypeScript files in a directory."""
        report = TypeScriptAnalysisReport(repo_path=str(directory))
        report.blindspots = self.STANDARD_BLINDSPOTS.copy()

        # Find all TypeScript/JavaScript files
        patterns = ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
        files: List[Path] = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))

        files = [f for f in files if not self._is_ignored(f)]

        # Detect frameworks first
        for file_path in files:
            self._detect_frameworks(file_path, report)

        # First pass: collect all handlers
        all_handlers: Dict[str, str] = {}  # handler_name -> file_path
        for file_path in files:
            handlers = self._find_handler_definitions(file_path)
            all_handlers.update(handlers)

        # Analyze each file
        for file_path in files:
            self._analyze_file(file_path, all_handlers, report)

        report.files_analyzed = len(files)

        return report

    def _detect_frameworks(self, file_path: Path, report: TypeScriptAnalysisReport) -> None:
        """Detect frameworks used in the file."""
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        for framework, patterns in self.FRAMEWORKS.items():
            if framework not in report.frameworks_detected:
                for pattern in patterns:
                    if pattern.search(content):
                        report.frameworks_detected.append(framework)
                        break

    def _find_handler_definitions(self, file_path: Path) -> Dict[str, str]:
        """Find all handler definitions in a file."""
        handlers = {}
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return handlers

        rel_path = str(file_path)

        # Find function handlers
        func_pattern = re.compile(
            r"(?:const|let|var|function)\s+(handle\w+|on\w+)\s*(?:=|:|\()",
            re.MULTILINE
        )

        for match in func_pattern.finditer(content):
            handlers[match.group(1)] = rel_path

        return handlers

    def _analyze_file(
        self,
        file_path: Path,
        all_handlers: Dict[str, str],
        report: TypeScriptAnalysisReport
    ) -> None:
        """Analyze a single TypeScript file."""
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)
        lines = content.split("\n")
        report.total_lines += len(lines)

        # Count constructs
        self._count_constructs(content, report)

        # Find issues
        self._find_empty_handlers(content, rel_path, report)
        self._find_debug_only_handlers(content, rel_path, report)
        self._find_unused_handlers(content, rel_path, all_handlers, report)
        self._find_react_issues(content, rel_path, report)
        self._find_hook_issues(content, rel_path, report)
        self._find_type_issues(content, rel_path, report)
        self._find_security_issues(content, rel_path, report)

    def _count_constructs(self, content: str, report: TypeScriptAnalysisReport) -> None:
        """Count various code constructs."""
        # Functions
        report.functions_found += len(re.findall(
            r"(?:function|const|let|var)\s+\w+\s*(?:=\s*(?:async\s+)?\([^)]*\)\s*=>|\([^)]*\)\s*(?::\s*\w+)?\s*\{)",
            content
        ))

        # React components
        report.components_found += len(re.findall(
            r"(?:function|const)\s+([A-Z]\w+)\s*(?::\s*React\.FC|\s*=\s*\([^)]*\)\s*=>)",
            content
        ))

        # Hooks
        for hook_type, pattern in self.HOOK_PATTERNS.items():
            report.hooks_found += len(pattern.findall(content))

        # Handlers
        report.handlers_found += len(re.findall(
            r"(?:const|let|var|function)\s+(?:handle\w+|on\w+)",
            content
        ))

    def _find_empty_handlers(
        self,
        content: str,
        file_path: str,
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find empty handler functions."""
        for pattern in self.EMPTY_HANDLER_PATTERNS:
            for match in pattern.finditer(content):
                handler_name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1

                report.no_op_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="empty_handler",
                    severity="HIGH",
                    message=f"Handler '{handler_name}' has empty body - does nothing when invoked",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + match.group().count("\n"),
                    code_snippet=match.group()[:100],
                    confidence=0.95,
                    fix_suggestion="Implement the handler functionality or remove if unused",
                ))

    def _find_debug_only_handlers(
        self,
        content: str,
        file_path: str,
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find handlers that only contain console.log."""
        for pattern in self.DEBUG_ONLY_PATTERNS:
            for match in pattern.finditer(content):
                handler_name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1

                report.no_op_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="debug_only_handler",
                    severity="MEDIUM",
                    message=f"Handler '{handler_name}' only contains console.log - likely placeholder",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + match.group().count("\n"),
                    code_snippet=match.group()[:100],
                    confidence=0.85,
                    fix_suggestion="Implement actual functionality or remove debug code",
                ))

    def _find_unused_handlers(
        self,
        content: str,
        file_path: str,
        all_handlers: Dict[str, str],
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find handlers defined but never bound to elements."""
        # Find handlers defined in this file
        handler_pattern = re.compile(
            r"(?:const|let|var|function)\s+(handle\w+|on\w+)\s*(?:=|:|\()",
            re.MULTILINE
        )

        for match in handler_pattern.finditer(content):
            handler_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Check if handler is used anywhere in the file
            usage_patterns = [
                rf"{handler_name}\s*\}}",  # {handleClick}
                rf"={handler_name}\}}",  # onClick={handleClick}
                rf"\({handler_name}\)",  # callback(handleClick)
                rf":\s*{handler_name}\b",  # prop: handleClick
            ]

            is_used = any(
                re.search(pattern, content)
                for pattern in usage_patterns
            )

            if not is_used:
                report.dead_code_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="unused_handler",
                    severity="LOW",
                    message=f"Handler '{handler_name}' is defined but never bound to any element",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.7,
                    fix_suggestion="Bind handler to an element or remove if unused",
                    evidence={"handler_name": handler_name},
                ))

    def _find_react_issues(
        self,
        content: str,
        file_path: str,
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find React-specific issues."""
        # Button without onClick
        button_pattern = re.compile(
            r"<button[^>]*>",
            re.IGNORECASE
        )

        for match in button_pattern.finditer(content):
            button_tag = match.group()
            if "onClick" not in button_tag and "disabled" not in button_tag:
                line_num = content[:match.start()].count("\n") + 1

                report.react_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="button_no_handler",
                    severity="LOW",
                    message="Button element without onClick handler",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.6,
                    fix_suggestion="Add onClick handler or mark as disabled if intentional",
                ))

        # Form without onSubmit
        form_pattern = re.compile(r"<form[^>]*>", re.IGNORECASE)
        for match in form_pattern.finditer(content):
            form_tag = match.group()
            if "onSubmit" not in form_tag:
                line_num = content[:match.start()].count("\n") + 1

                report.react_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="form_no_submit",
                    severity="MEDIUM",
                    message="Form element without onSubmit handler",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.7,
                    fix_suggestion="Add onSubmit handler to process form submission",
                ))

    def _find_hook_issues(
        self,
        content: str,
        file_path: str,
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find React hook issues."""
        # useEffect with empty deps but using variables
        for issue_type, pattern in self.USE_EFFECT_ISSUES.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                severity = "MEDIUM" if issue_type == "missing_deps" else "HIGH"
                message_map = {
                    "missing_deps": "useEffect may be missing dependencies in dependency array",
                    "infinite_loop": "useEffect may cause infinite loop - setState without dependencies",
                }

                report.react_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=issue_type,
                    severity=severity,
                    message=message_map.get(issue_type, "useEffect issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + match.group().count("\n"),
                    confidence=0.7,
                    fix_suggestion="Review useEffect dependencies and add exhaustive deps",
                ))

    def _find_type_issues(
        self,
        content: str,
        file_path: str,
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find TypeScript type issues."""
        for pattern_name, pattern in self.TYPE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                severity_map = {
                    "any_type": "LOW",
                    "ts_ignore": "MEDIUM",
                    "non_null_assertion": "LOW",
                }

                message_map = {
                    "any_type": "Usage of 'any' type bypasses type checking",
                    "ts_ignore": "TypeScript error suppression - may hide real issues",
                    "non_null_assertion": "Non-null assertion (!) may cause runtime errors",
                }

                report.type_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity=severity_map.get(pattern_name, "LOW"),
                    message=message_map.get(pattern_name, "Type issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.9,
                ))

    def _find_security_issues(
        self,
        content: str,
        file_path: str,
        report: TypeScriptAnalysisReport
    ) -> None:
        """Find security issues."""
        for pattern_name, pattern in self.SECURITY_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                severity_map = {
                    "dangerouslySetInnerHTML": "HIGH",
                    "eval": "CRITICAL",
                    "innerHTML": "HIGH",
                    "document_write": "MEDIUM",
                    "xss_vulnerable": "CRITICAL",
                }

                message_map = {
                    "dangerouslySetInnerHTML": "dangerouslySetInnerHTML may expose XSS vulnerability",
                    "eval": "eval() is dangerous and should be avoided",
                    "innerHTML": "innerHTML assignment may expose XSS vulnerability",
                    "document_write": "document.write can cause security issues",
                    "xss_vulnerable": "Potential XSS vulnerability with dynamic URL",
                }

                report.security_findings.append(TypeScriptFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity=severity_map.get(pattern_name, "MEDIUM"),
                    message=message_map.get(pattern_name, "Security issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.85,
                    fix_suggestion="Sanitize input and use safe alternatives",
                ))


def analyze_typescript(path: Path) -> TypeScriptAnalysisReport:
    """
    Convenience function to analyze TypeScript code.
    """
    analyzer = TypeScriptAnalyzer()
    return analyzer._analyze_directory(path)
