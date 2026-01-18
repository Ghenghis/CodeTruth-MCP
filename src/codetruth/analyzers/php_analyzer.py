"""
PHP Full Analyzer

Comprehensive PHP code analysis combining:
- Reachability graph building
- Dead code detection
- Fake success return detection (AJAX handlers)
- Cron job verification
- Database operation analysis
- Game server pattern detection (Travian, TWLan, etc.)
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


class PHPFinding(BaseModel):
    """A finding from PHP analysis."""
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


class PHPAnalysisReport(BaseModel):
    """Complete PHP analysis report."""
    repo_path: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    files_analyzed: int = 0
    total_lines: int = 0

    # Findings by category
    dead_code_findings: List[PHPFinding] = Field(default_factory=list)
    fake_success_findings: List[PHPFinding] = Field(default_factory=list)
    cron_findings: List[PHPFinding] = Field(default_factory=list)
    security_findings: List[PHPFinding] = Field(default_factory=list)
    database_findings: List[PHPFinding] = Field(default_factory=list)
    game_logic_findings: List[PHPFinding] = Field(default_factory=list)

    # Statistics
    functions_found: int = 0
    classes_found: int = 0
    ajax_handlers: int = 0
    cron_jobs: int = 0
    db_queries: int = 0

    # Framework detection
    frameworks_detected: List[str] = Field(default_factory=list)

    # Blindspots
    blindspots: List[str] = Field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return (
            len(self.dead_code_findings) +
            len(self.fake_success_findings) +
            len(self.cron_findings) +
            len(self.security_findings) +
            len(self.database_findings) +
            len(self.game_logic_findings)
        )

    @property
    def all_findings(self) -> List[PHPFinding]:
        return (
            self.dead_code_findings +
            self.fake_success_findings +
            self.cron_findings +
            self.security_findings +
            self.database_findings +
            self.game_logic_findings
        )


class PHPAnalyzer(BaseAnalyzer):
    """
    Full PHP analyzer with comprehensive code analysis.

    Specialized for game server codebases (Travian, TWLan, etc.)

    Proof Level: P2 (STATIC_PARTIAL)
    Confidence: 0.70-0.90
    """

    name = "php_full"
    description = "Comprehensive PHP code analyzer for game servers"

    # Framework patterns
    FRAMEWORKS = {
        "laravel": [
            re.compile(r"namespace\s+App\\"),
            re.compile(r"use\s+Illuminate\\"),
            re.compile(r"extends\s+Controller"),
        ],
        "symfony": [
            re.compile(r"use\s+Symfony\\"),
            re.compile(r"extends\s+AbstractController"),
        ],
        "wordpress": [
            re.compile(r"add_action|add_filter"),
            re.compile(r"wp_"),
            re.compile(r"WP_"),
        ],
        "travian_twlan": [
            re.compile(r"village|dorf|building", re.IGNORECASE),
            re.compile(r"troops|units|army", re.IGNORECASE),
            re.compile(r"attack|raid|reinforce", re.IGNORECASE),
        ],
    }

    # Handler patterns
    HANDLER_PATTERNS = {
        "ajax_handler": re.compile(
            r"function\s+(handle\w+|process\w+|ajax\w+|do\w+Action)\s*\(",
            re.MULTILINE
        ),
        "form_handler": re.compile(
            r"if\s*\(\s*\$_(?:POST|GET|REQUEST)\s*\[",
            re.MULTILINE
        ),
        "action_switch": re.compile(
            r"switch\s*\(\s*\$(?:_GET|_POST|_REQUEST)\s*\[\s*['\"]action['\"]\s*\]\s*\)",
            re.MULTILINE
        ),
    }

    # Fake success patterns - returns success without DB operations
    FAKE_SUCCESS_PATTERNS = {
        "json_success_no_db": re.compile(
            r"function\s+\w+\s*\([^)]*\)\s*\{[^}]*"
            r"json_encode\s*\(\s*\[\s*['\"]success['\"]\s*=>\s*true"
            r"[^}]*\}",
            re.MULTILINE | re.DOTALL
        ),
        "return_true_no_effect": re.compile(
            r"function\s+\w+\s*\([^)]*\)\s*\{[^}]*return\s+true\s*;[^}]*\}",
            re.MULTILINE | re.DOTALL
        ),
    }

    # Database operation patterns
    DB_WRITE_PATTERNS = [
        re.compile(r"INSERT\s+INTO", re.IGNORECASE),
        re.compile(r"UPDATE\s+\w+\s+SET", re.IGNORECASE),
        re.compile(r"DELETE\s+FROM", re.IGNORECASE),
        re.compile(r"REPLACE\s+INTO", re.IGNORECASE),
        re.compile(r"->(?:insert|update|delete|save|persist)\s*\("),
    ]

    # Cron job patterns
    CRON_PATTERNS = {
        "cron_function": re.compile(
            r"function\s+(cron\w+|tick\w+|schedule\w+|process\w+Queue)\s*\(",
            re.MULTILINE
        ),
        "cli_check": re.compile(
            r"php_sapi_name\s*\(\s*\)\s*(?:===?|!==?)\s*['\"]cli['\"]"
        ),
        "entry_point": re.compile(
            r"basename\s*\(\s*__FILE__\s*\)\s*===?\s*basename"
        ),
    }

    # Game server specific patterns
    GAME_PATTERNS = {
        "resource_tick": re.compile(
            r"function\s+\w*(?:resource|tick)\w*\s*\(",
            re.IGNORECASE
        ),
        "building_queue": re.compile(
            r"function\s+\w*(?:building|construction)\w*(?:queue|process)\w*\s*\(",
            re.IGNORECASE
        ),
        "troop_training": re.compile(
            r"function\s+\w*(?:train|troops?|units?)\w*\s*\(",
            re.IGNORECASE
        ),
        "combat_handler": re.compile(
            r"function\s+\w*(?:attack|combat|battle|raid)\w*\s*\(",
            re.IGNORECASE
        ),
        "village_handler": re.compile(
            r"function\s+\w*(?:village|dorf|settlement)\w*\s*\(",
            re.IGNORECASE
        ),
    }

    # Security patterns
    SECURITY_PATTERNS = {
        "sql_injection": re.compile(
            r"(?:query|execute)\s*\(\s*['\"].*\$_(?:GET|POST|REQUEST)",
            re.MULTILINE
        ),
        "sql_concat": re.compile(
            r"(?:query|execute)\s*\(\s*['\"].*\.\s*\$",
            re.MULTILINE
        ),
        "command_injection": re.compile(
            r"(?:exec|system|passthru|shell_exec|popen)\s*\(\s*\$",
            re.MULTILINE
        ),
        "file_inclusion": re.compile(
            r"(?:include|require)(?:_once)?\s*\(\s*\$",
            re.MULTILINE
        ),
        "eval_usage": re.compile(
            r"\beval\s*\(",
            re.MULTILINE
        ),
        "unserialize": re.compile(
            r"unserialize\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)",
            re.MULTILINE
        ),
        "hardcoded_password": re.compile(
            r"(?:password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
            re.IGNORECASE
        ),
    }

    # Empty function patterns
    EMPTY_FUNCTION_PATTERNS = [
        re.compile(r"function\s+(\w+)\s*\([^)]*\)\s*\{\s*\}", re.MULTILINE),
        re.compile(r"function\s+(\w+)\s*\([^)]*\)\s*\{\s*//[^\n]*\s*\}", re.MULTILINE),
        re.compile(r"function\s+(\w+)\s*\([^)]*\)\s*\{\s*return\s*;\s*\}", re.MULTILINE),
    ]

    STANDARD_BLINDSPOTS = [
        "Dynamic code execution (eval, create_function) cannot be analyzed",
        "Variable variables ($$var) obscure data flow",
        "Magic methods (__call, __get) may hide behavior",
        "Include/require with variable paths cannot be traced",
        "External crontab configuration not analyzed",
        "Runtime class loading and autoloaders",
        "Database triggers and stored procedures",
    ]

    def __init__(self):
        self._finding_counter = 0

    def _generate_finding_id(self) -> str:
        self._finding_counter += 1
        return f"php_{self._finding_counter:06d}"

    async def run(
        self,
        repo_path: Path,
        options: Dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        """Run comprehensive PHP analysis."""
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

    def _analyze_directory(self, directory: Path) -> PHPAnalysisReport:
        """Analyze all PHP files in a directory."""
        report = PHPAnalysisReport(repo_path=str(directory))
        report.blindspots = self.STANDARD_BLINDSPOTS.copy()

        # Find all PHP files
        files = list(directory.glob("**/*.php"))
        files = [f for f in files if not self._is_ignored(f)]

        # Detect frameworks first
        for file_path in files:
            self._detect_frameworks(file_path, report)

        # Check for crontab
        crontab_exists = self._check_crontab(directory)

        # Analyze each file
        for file_path in files:
            self._analyze_file(file_path, crontab_exists, report)

        report.files_analyzed = len(files)

        return report

    def _detect_frameworks(self, file_path: Path, report: PHPAnalysisReport) -> None:
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

    def _check_crontab(self, directory: Path) -> bool:
        """Check if crontab configuration exists."""
        crontab_patterns = ["crontab", "cron.d", "cron.txt", "scheduler"]
        for pattern in crontab_patterns:
            if list(directory.glob(f"**/*{pattern}*")):
                return True
        return False

    def _analyze_file(
        self,
        file_path: Path,
        crontab_exists: bool,
        report: PHPAnalysisReport
    ) -> None:
        """Analyze a single PHP file."""
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
        self._find_empty_functions(content, rel_path, report)
        self._find_fake_success_handlers(content, rel_path, report)
        self._find_cron_issues(content, rel_path, crontab_exists, report)
        self._find_security_issues(content, rel_path, report)
        self._find_database_issues(content, rel_path, report)
        self._find_game_logic_issues(content, rel_path, report)

    def _count_constructs(self, content: str, report: PHPAnalysisReport) -> None:
        """Count various code constructs."""
        # Functions
        report.functions_found += len(re.findall(
            r"function\s+\w+\s*\(",
            content
        ))

        # Classes
        report.classes_found += len(re.findall(
            r"class\s+\w+",
            content
        ))

        # AJAX handlers
        for handler_type, pattern in self.HANDLER_PATTERNS.items():
            if handler_type == "ajax_handler":
                report.ajax_handlers += len(pattern.findall(content))

        # Cron jobs
        for cron_type, pattern in self.CRON_PATTERNS.items():
            if cron_type == "cron_function":
                report.cron_jobs += len(pattern.findall(content))

        # Database queries
        for pattern in self.DB_WRITE_PATTERNS:
            report.db_queries += len(pattern.findall(content))

    def _find_empty_functions(
        self,
        content: str,
        file_path: str,
        report: PHPAnalysisReport
    ) -> None:
        """Find empty functions."""
        for pattern in self.EMPTY_FUNCTION_PATTERNS:
            for match in pattern.finditer(content):
                func_name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1

                report.dead_code_findings.append(PHPFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="empty_function",
                    severity="MEDIUM",
                    message=f"Function '{func_name}' has empty body",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + match.group().count("\n"),
                    code_snippet=match.group()[:100],
                    confidence=0.9,
                    fix_suggestion="Implement the function or remove if unused",
                ))

    def _find_fake_success_handlers(
        self,
        content: str,
        file_path: str,
        report: PHPAnalysisReport
    ) -> None:
        """Find handlers that return success without DB operations."""
        # Find all AJAX-style handlers
        handler_pattern = re.compile(
            r"function\s+(\w*(?:handle|process|ajax|do)\w*)\s*\([^)]*\)\s*\{",
            re.MULTILINE | re.IGNORECASE
        )

        for match in handler_pattern.finditer(content):
            func_name = match.group(1)
            func_start = match.end()

            # Extract function body
            func_body = self._extract_function_body(content, func_start)
            if not func_body:
                continue

            line_num = content[:match.start()].count("\n") + 1

            # Check for success return
            has_success = (
                re.search(r"['\"]success['\"]\s*=>\s*true", func_body) or
                re.search(r"return\s+true", func_body)
            )

            # Check for DB write operations
            has_db_write = any(
                pattern.search(func_body)
                for pattern in self.DB_WRITE_PATTERNS
            )

            if has_success and not has_db_write:
                report.fake_success_findings.append(PHPFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="fake_success_return",
                    severity="CRITICAL",
                    message=f"Handler '{func_name}' returns success without any database operation",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + func_body.count("\n"),
                    confidence=0.85,
                    fix_suggestion="Add database operation or return error if action cannot be completed",
                    evidence={
                        "handler_name": func_name,
                        "has_success_return": True,
                        "has_db_write": False,
                    },
                ))

    def _find_cron_issues(
        self,
        content: str,
        file_path: str,
        crontab_exists: bool,
        report: PHPAnalysisReport
    ) -> None:
        """Find cron job issues."""
        for match in self.CRON_PATTERNS["cron_function"].finditer(content):
            func_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Check if file has entry point detection
            has_entry_check = (
                self.CRON_PATTERNS["cli_check"].search(content) or
                self.CRON_PATTERNS["entry_point"].search(content)
            )

            if not crontab_exists:
                report.cron_findings.append(PHPFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="unreachable_cron",
                    severity="CRITICAL",
                    message=f"Cron function '{func_name}' exists but no crontab configuration found",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + 5,
                    confidence=0.75,
                    fix_suggestion="Add crontab entry to schedule this function",
                    evidence={
                        "cron_function": func_name,
                        "crontab_exists": False,
                    },
                ))

            if not has_entry_check:
                report.cron_findings.append(PHPFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="no_cli_protection",
                    severity="MEDIUM",
                    message=f"Cron function '{func_name}' lacks CLI/entry point check",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.8,
                    fix_suggestion="Add php_sapi_name() check for CLI-only execution",
                ))

    def _find_security_issues(
        self,
        content: str,
        file_path: str,
        report: PHPAnalysisReport
    ) -> None:
        """Find security issues."""
        for pattern_name, pattern in self.SECURITY_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                severity_map = {
                    "sql_injection": "CRITICAL",
                    "sql_concat": "CRITICAL",
                    "command_injection": "CRITICAL",
                    "file_inclusion": "CRITICAL",
                    "eval_usage": "HIGH",
                    "unserialize": "HIGH",
                    "hardcoded_password": "MEDIUM",
                }

                message_map = {
                    "sql_injection": "SQL injection vulnerability - user input in query",
                    "sql_concat": "SQL injection risk - string concatenation in query",
                    "command_injection": "Command injection - user input in shell command",
                    "file_inclusion": "File inclusion vulnerability - variable in include path",
                    "eval_usage": "eval() usage is dangerous",
                    "unserialize": "Unserialize of user input can lead to RCE",
                    "hardcoded_password": "Hardcoded password detected",
                }

                fix_map = {
                    "sql_injection": "Use prepared statements with bound parameters",
                    "sql_concat": "Use prepared statements with bound parameters",
                    "command_injection": "Use escapeshellarg() or avoid shell commands",
                    "file_inclusion": "Use whitelist for allowed includes",
                    "eval_usage": "Avoid eval - use safer alternatives",
                    "unserialize": "Use JSON instead of serialization",
                    "hardcoded_password": "Use environment variables or secure vault",
                }

                report.security_findings.append(PHPFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity=severity_map.get(pattern_name, "HIGH"),
                    message=message_map.get(pattern_name, "Security issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=match.group()[:100],
                    confidence=0.8,
                    fix_suggestion=fix_map.get(pattern_name, "Fix security issue"),
                ))

    def _find_database_issues(
        self,
        content: str,
        file_path: str,
        report: PHPAnalysisReport
    ) -> None:
        """Find database operation issues."""
        # Find functions that claim to save but don't
        save_patterns = re.compile(
            r"function\s+(\w*(?:save|store|persist|write)\w*)\s*\([^)]*\)\s*\{",
            re.IGNORECASE
        )

        for match in save_patterns.finditer(content):
            func_name = match.group(1)
            func_start = match.end()
            func_body = self._extract_function_body(content, func_start)

            if func_body:
                has_db_write = any(
                    pattern.search(func_body)
                    for pattern in self.DB_WRITE_PATTERNS
                )

                if not has_db_write:
                    line_num = content[:match.start()].count("\n") + 1

                    report.database_findings.append(PHPFinding(
                        finding_id=self._generate_finding_id(),
                        finding_type="save_without_db",
                        severity="HIGH",
                        message=f"Function '{func_name}' claims to save but has no DB write operation",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num + func_body.count("\n"),
                        confidence=0.75,
                        fix_suggestion="Add database INSERT/UPDATE or rename function",
                    ))

    def _find_game_logic_issues(
        self,
        content: str,
        file_path: str,
        report: PHPAnalysisReport
    ) -> None:
        """Find game server specific issues."""
        for pattern_name, pattern in self.GAME_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                # Extract function body
                func_start = match.end()
                func_body = self._extract_function_body(content, func_start)

                if not func_body:
                    continue

                # Check for stub implementations
                is_stub = (
                    re.search(r"//\s*TODO", func_body) or
                    re.search(r"return\s+true\s*;", func_body) or
                    len(func_body.strip()) < 50
                )

                if is_stub:
                    func_name_match = re.search(r"function\s+(\w+)", match.group(0) + func_body[:50])
                    func_name = func_name_match.group(1) if func_name_match else pattern_name

                    report.game_logic_findings.append(PHPFinding(
                        finding_id=self._generate_finding_id(),
                        finding_type=f"stub_{pattern_name}",
                        severity="HIGH",
                        message=f"Game logic function appears to be a stub: {func_name}",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num + func_body.count("\n"),
                        confidence=0.7,
                        fix_suggestion="Implement full game logic for this handler",
                        evidence={"pattern_type": pattern_name},
                    ))

    def _extract_function_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract function body from starting position."""
        brace_count = 0
        in_body = False
        body_start = start_pos
        body_end = start_pos

        # Find the opening brace first
        for i in range(start_pos, len(content)):
            if content[i] == "{":
                if not in_body:
                    body_start = i
                    in_body = True
                brace_count += 1
            elif content[i] == "}":
                brace_count -= 1
                if brace_count == 0 and in_body:
                    body_end = i
                    break

        if body_end > body_start:
            return content[body_start:body_end + 1]
        return None


def analyze_php(path: Path) -> PHPAnalysisReport:
    """
    Convenience function to analyze PHP code.
    """
    analyzer = PHPAnalyzer()
    return analyzer._analyze_directory(path)
