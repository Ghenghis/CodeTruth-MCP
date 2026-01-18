"""
Python Full Analyzer

Comprehensive Python code analysis combining:
- Reachability graph building
- Dead code detection
- No-op function detection
- Framework-specific analysis (Flask, FastAPI, Discord.py, etc.)
- Async pattern analysis
"""

from __future__ import annotations

import ast
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from pydantic import BaseModel, Field

from .base import BaseAnalyzer, AnalysisResult

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class PythonFinding(BaseModel):
    """A finding from Python analysis."""
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


class PythonAnalysisReport(BaseModel):
    """Complete Python analysis report."""
    repo_path: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    files_analyzed: int = 0
    total_lines: int = 0

    # Findings by category
    dead_code_findings: List[PythonFinding] = Field(default_factory=list)
    no_op_findings: List[PythonFinding] = Field(default_factory=list)
    async_findings: List[PythonFinding] = Field(default_factory=list)
    framework_findings: List[PythonFinding] = Field(default_factory=list)
    security_findings: List[PythonFinding] = Field(default_factory=list)

    # Statistics
    functions_found: int = 0
    classes_found: int = 0
    async_functions: int = 0
    decorators_found: int = 0

    # Framework detection
    frameworks_detected: List[str] = Field(default_factory=list)

    # Blindspots
    blindspots: List[str] = Field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return (
            len(self.dead_code_findings) +
            len(self.no_op_findings) +
            len(self.async_findings) +
            len(self.framework_findings) +
            len(self.security_findings)
        )

    @property
    def all_findings(self) -> List[PythonFinding]:
        return (
            self.dead_code_findings +
            self.no_op_findings +
            self.async_findings +
            self.framework_findings +
            self.security_findings
        )


class PythonAnalyzer(BaseAnalyzer):
    """
    Full Python analyzer with comprehensive code analysis.

    Proof Level: P2 (STATIC_PARTIAL)
    Confidence: 0.75-0.95
    """

    name = "python_full"
    description = "Comprehensive Python code analyzer"

    # Known frameworks and their patterns
    FRAMEWORKS = {
        "flask": [
            re.compile(r"from\s+flask\s+import"),
            re.compile(r"Flask\s*\("),
            re.compile(r"@app\.route"),
        ],
        "fastapi": [
            re.compile(r"from\s+fastapi\s+import"),
            re.compile(r"FastAPI\s*\("),
            re.compile(r"@(?:app|router)\.(get|post|put|delete)"),
        ],
        "django": [
            re.compile(r"from\s+django"),
            re.compile(r"INSTALLED_APPS"),
            re.compile(r"def\s+\w+\s*\(\s*request"),
        ],
        "discord.py": [
            re.compile(r"from\s+discord"),
            re.compile(r"commands\.Bot|discord\.Client"),
            re.compile(r"@(?:bot|client)\.(?:command|event)"),
        ],
        "celery": [
            re.compile(r"from\s+celery\s+import"),
            re.compile(r"Celery\s*\("),
            re.compile(r"@(?:app|celery)\.task"),
        ],
        "pytest": [
            re.compile(r"import\s+pytest"),
            re.compile(r"@pytest\.(?:fixture|mark)"),
            re.compile(r"def\s+test_"),
        ],
        "sqlalchemy": [
            re.compile(r"from\s+sqlalchemy"),
            re.compile(r"Base\s*=\s*declarative_base"),
            re.compile(r"Column\s*\("),
        ],
    }

    # No-op patterns
    NO_OP_PATTERNS = {
        "empty_function": re.compile(
            r"def\s+\w+\s*\([^)]*\)\s*:\s*(?:\n\s+)?(?:pass|\.\.\.)",
            re.MULTILINE
        ),
        "only_docstring": re.compile(
            r'def\s+\w+\s*\([^)]*\)\s*:\s*\n\s+["\'][^"\']*["\'](?:\s*\n\s*pass)?',
            re.MULTILINE
        ),
        "debug_only": re.compile(
            r"def\s+\w+\s*\([^)]*\)\s*:\s*\n(?:\s+(?:print|logging?\.\w+)\s*\([^)]*\)\s*\n)+\s*(?:pass)?",
            re.MULTILINE
        ),
        "return_none": re.compile(
            r"def\s+\w+\s*\([^)]*\)\s*:\s*\n\s+return\s*(?:None)?$",
            re.MULTILINE
        ),
    }

    # Security patterns
    SECURITY_PATTERNS = {
        "sql_injection": re.compile(
            r'(?:execute|query)\s*\(\s*["\'].*%s.*["\']|'
            r'(?:execute|query)\s*\(\s*f["\'].*\{.*\}',
            re.MULTILINE
        ),
        "command_injection": re.compile(
            r"(?:os\.system|subprocess\.(?:call|run|Popen))\s*\(\s*(?:f['\"]|\w+\s*\+)",
            re.MULTILINE
        ),
        "hardcoded_secret": re.compile(
            r"(?:password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
            re.MULTILINE | re.IGNORECASE
        ),
        "eval_usage": re.compile(
            r"\beval\s*\(",
            re.MULTILINE
        ),
        "pickle_load": re.compile(
            r"pickle\.(?:load|loads)\s*\(",
            re.MULTILINE
        ),
    }

    STANDARD_BLINDSPOTS = [
        "Dynamic code execution (exec, eval) cannot be statically analyzed",
        "Runtime imports (importlib) may hide dependencies",
        "Metaprogramming (decorators modifying functions) may alter behavior",
        "C extensions cannot be analyzed",
        "async/await patterns may have hidden race conditions",
        "monkey-patching at runtime not detected",
    ]

    def __init__(self):
        self._finding_counter = 0

    def _generate_finding_id(self) -> str:
        self._finding_counter += 1
        return f"py_{self._finding_counter:06d}"

    async def run(
        self,
        repo_path: Path,
        options: Dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        """Run comprehensive Python analysis."""
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

            # Calculate duration
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

    def _analyze_directory(self, directory: Path) -> PythonAnalysisReport:
        """Analyze all Python files in a directory."""
        report = PythonAnalysisReport(repo_path=str(directory))
        report.blindspots = self.STANDARD_BLINDSPOTS.copy()

        # Find all Python files
        files = list(directory.glob("**/*.py"))
        files = [f for f in files if not self._is_ignored(f)]

        # Detect frameworks first
        for file_path in files:
            self._detect_frameworks(file_path, report)

        # Analyze each file
        for file_path in files:
            self._analyze_file(file_path, report)

        report.files_analyzed = len(files)

        return report

    def _detect_frameworks(self, file_path: Path, report: PythonAnalysisReport) -> None:
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

    def _analyze_file(self, file_path: Path, report: PythonAnalysisReport) -> None:
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)
        lines = content.split("\n")
        report.total_lines += len(lines)

        # Try AST analysis first
        try:
            tree = ast.parse(content, filename=str(file_path))
            self._analyze_ast(tree, rel_path, content, report)
        except SyntaxError:
            # Fall back to regex analysis
            self._analyze_regex(content, rel_path, report)

        # Run pattern-based analysis
        self._find_no_ops(content, rel_path, report)
        self._find_security_issues(content, rel_path, report)
        self._find_async_issues(content, rel_path, report)

    def _analyze_ast(
        self,
        tree: ast.AST,
        file_path: str,
        content: str,
        report: PythonAnalysisReport
    ) -> None:
        """Analyze using Python AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                report.classes_found += 1
                self._analyze_class(node, file_path, content, report)

            elif isinstance(node, ast.FunctionDef):
                report.functions_found += 1
                self._analyze_function(node, file_path, content, report)

            elif isinstance(node, ast.AsyncFunctionDef):
                report.functions_found += 1
                report.async_functions += 1
                self._analyze_async_function(node, file_path, content, report)

    def _analyze_class(
        self,
        node: ast.ClassDef,
        file_path: str,
        content: str,
        report: PythonAnalysisReport
    ) -> None:
        """Analyze a class definition."""
        # Check for unused methods
        defined_methods = set()
        called_methods = set()

        for item in ast.walk(node):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_methods.add(item.name)
            elif isinstance(item, ast.Call):
                if isinstance(item.func, ast.Attribute):
                    called_methods.add(item.func.attr)

        # Dunder methods are always "used"
        unused = defined_methods - called_methods
        unused = {m for m in unused if not (m.startswith("__") and m.endswith("__"))}

        for method_name in unused:
            # Find the method node
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name == method_name:
                        report.dead_code_findings.append(PythonFinding(
                            finding_id=self._generate_finding_id(),
                            finding_type="unused_method",
                            severity="LOW",
                            message=f"Method '{method_name}' in class '{node.name}' is defined but never called within the class",
                            file_path=file_path,
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                            confidence=0.6,
                            evidence={"class": node.name, "method": method_name},
                        ))
                        break

    def _analyze_function(
        self,
        node: ast.FunctionDef,
        file_path: str,
        content: str,
        report: PythonAnalysisReport
    ) -> None:
        """Analyze a function definition."""
        # Count decorators
        report.decorators_found += len(node.decorator_list)

        # Check for empty function
        if self._is_empty_function(node):
            # Check if it's intentional (abstract, protocol, etc.)
            decorators = [self._get_decorator_name(d) for d in node.decorator_list]
            if not any(d in ["abstractmethod", "abstractproperty"] for d in decorators):
                report.no_op_findings.append(PythonFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="empty_function",
                    severity="MEDIUM",
                    message=f"Function '{node.name}' has an empty body",
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    confidence=0.9,
                    fix_suggestion="Implement the function body or mark as abstract",
                ))

        # Check for debug-only function
        elif self._is_debug_only_function(node):
            report.no_op_findings.append(PythonFinding(
                finding_id=self._generate_finding_id(),
                finding_type="debug_only_function",
                severity="LOW",
                message=f"Function '{node.name}' only contains debug/print statements",
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                confidence=0.85,
                fix_suggestion="Consider if this function should have real functionality",
            ))

        # Check for unreachable code after return
        self._check_unreachable_after_return(node, file_path, report)

    def _analyze_async_function(
        self,
        node: ast.AsyncFunctionDef,
        file_path: str,
        content: str,
        report: PythonAnalysisReport
    ) -> None:
        """Analyze an async function definition."""
        # Check for missing await
        has_await = False
        for child in ast.walk(node):
            if isinstance(child, ast.Await):
                has_await = True
                break

        if not has_await:
            # Check if it calls async functions without await
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call_name = self._get_call_name(child)
                    if call_name and call_name.startswith("async_"):
                        report.async_findings.append(PythonFinding(
                            finding_id=self._generate_finding_id(),
                            finding_type="missing_await",
                            severity="HIGH",
                            message=f"Async function '{node.name}' may be missing await statements",
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            confidence=0.7,
                            fix_suggestion="Add 'await' before async function calls",
                        ))
                        break

    def _check_unreachable_after_return(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        report: PythonAnalysisReport
    ) -> None:
        """Check for unreachable code after return statements."""
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return) and i < len(node.body) - 1:
                # Code after return
                next_stmt = node.body[i + 1]
                report.dead_code_findings.append(PythonFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="unreachable_code",
                    severity="MEDIUM",
                    message=f"Code after return statement in '{node.name}' is unreachable",
                    file_path=file_path,
                    line_start=next_stmt.lineno,
                    line_end=next_stmt.end_lineno or next_stmt.lineno,
                    confidence=0.95,
                    fix_suggestion="Remove unreachable code or fix control flow",
                ))
                break

    def _analyze_regex(
        self,
        content: str,
        file_path: str,
        report: PythonAnalysisReport
    ) -> None:
        """Fallback regex-based analysis."""
        # Count functions and classes
        report.functions_found += len(re.findall(r"^\s*(?:async\s+)?def\s+", content, re.MULTILINE))
        report.classes_found += len(re.findall(r"^class\s+", content, re.MULTILINE))

    def _find_no_ops(
        self,
        content: str,
        file_path: str,
        report: PythonAnalysisReport
    ) -> None:
        """Find no-op patterns using regex."""
        for pattern_name, pattern in self.NO_OP_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                # Skip if already found by AST analysis
                existing = [
                    f for f in report.no_op_findings
                    if f.file_path == file_path and
                    abs(f.line_start - line_num) < 3
                ]
                if existing:
                    continue

                report.no_op_findings.append(PythonFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity="MEDIUM" if pattern_name == "empty_function" else "LOW",
                    message=f"Detected {pattern_name.replace('_', ' ')} pattern",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + match.group().count("\n"),
                    code_snippet=match.group()[:100],
                    confidence=0.8,
                ))

    def _find_security_issues(
        self,
        content: str,
        file_path: str,
        report: PythonAnalysisReport
    ) -> None:
        """Find potential security issues."""
        for pattern_name, pattern in self.SECURITY_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                severity_map = {
                    "sql_injection": "CRITICAL",
                    "command_injection": "CRITICAL",
                    "hardcoded_secret": "HIGH",
                    "eval_usage": "HIGH",
                    "pickle_load": "MEDIUM",
                }

                report.security_findings.append(PythonFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity=severity_map.get(pattern_name, "MEDIUM"),
                    message=f"Potential {pattern_name.replace('_', ' ')} detected",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=match.group()[:100],
                    confidence=0.7,
                    fix_suggestion=self._get_security_fix(pattern_name),
                ))

    def _find_async_issues(
        self,
        content: str,
        file_path: str,
        report: PythonAnalysisReport
    ) -> None:
        """Find async-related issues."""
        # Check for sync calls in async context
        if "async def" in content:
            sync_calls = [
                (r"time\.sleep\s*\(", "Use asyncio.sleep instead of time.sleep in async code"),
                (r"requests\.(get|post|put|delete)\s*\(", "Use aiohttp or httpx for async HTTP calls"),
                (r"open\s*\([^)]+\)\.read\s*\(", "Use aiofiles for async file operations"),
            ]

            for pattern, message in sync_calls:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1

                    # Check if this is inside an async function
                    # Simple heuristic: look for async def before this line
                    before = content[:match.start()]
                    last_def = before.rfind("def ")
                    if last_def != -1:
                        def_line = before[last_def:].split("\n")[0]
                        if "async def" in def_line or before[last_def-6:last_def] == "async ":
                            report.async_findings.append(PythonFinding(
                                finding_id=self._generate_finding_id(),
                                finding_type="sync_in_async",
                                severity="MEDIUM",
                                message=message,
                                file_path=file_path,
                                line_start=line_num,
                                line_end=line_num,
                                code_snippet=match.group(),
                                confidence=0.75,
                            ))

    def _is_empty_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function body is empty."""
        if len(node.body) == 0:
            return True

        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                return True
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Constant):
                    # Only docstring or ellipsis
                    return True

        if len(node.body) == 2:
            # Docstring + pass
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[1], ast.Pass):
                return True

        return False

    def _is_debug_only_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function only contains debug statements."""
        debug_calls = {"print", "logging", "logger", "log"}

        for stmt in node.body:
            # Skip docstrings
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                continue

            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call_name = self._get_call_name(stmt.value)
                # Check if it's a debug call
                if call_name and not any(d in call_name.lower() for d in debug_calls):
                    return False
            elif isinstance(stmt, ast.Pass):
                continue
            else:
                return False

        return True

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""

    def _get_call_name(self, node: ast.Call) -> str:
        """Get function call name."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _get_security_fix(self, pattern_name: str) -> str:
        """Get fix suggestion for security issue."""
        fixes = {
            "sql_injection": "Use parameterized queries with placeholders",
            "command_injection": "Use subprocess with list arguments, avoid shell=True",
            "hardcoded_secret": "Use environment variables or a secrets manager",
            "eval_usage": "Use ast.literal_eval for safe evaluation or avoid eval entirely",
            "pickle_load": "Use JSON or a safer serialization format for untrusted data",
        }
        return fixes.get(pattern_name, "Review and fix the security issue")


def analyze_python(path: Path) -> PythonAnalysisReport:
    """
    Convenience function to analyze Python code.
    """
    analyzer = PythonAnalyzer()
    return analyzer._analyze_directory(path)
