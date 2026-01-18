"""
Java Full Analyzer

Comprehensive Java code analysis combining:
- Reachability graph building
- Dead code detection
- Packet handler verification (MapleStory servers)
- Event handler analysis
- Database operation verification
- Scheduled task analysis
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


class JavaFinding(BaseModel):
    """A finding from Java analysis."""
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


class JavaAnalysisReport(BaseModel):
    """Complete Java analysis report."""
    repo_path: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    files_analyzed: int = 0
    total_lines: int = 0

    # Findings by category
    dead_code_findings: List[JavaFinding] = Field(default_factory=list)
    handler_findings: List[JavaFinding] = Field(default_factory=list)
    packet_findings: List[JavaFinding] = Field(default_factory=list)
    security_findings: List[JavaFinding] = Field(default_factory=list)
    concurrency_findings: List[JavaFinding] = Field(default_factory=list)
    database_findings: List[JavaFinding] = Field(default_factory=list)

    # Statistics
    classes_found: int = 0
    methods_found: int = 0
    packet_handlers: int = 0
    event_handlers: int = 0
    scheduled_tasks: int = 0

    # Framework detection
    frameworks_detected: List[str] = Field(default_factory=list)

    # Blindspots
    blindspots: List[str] = Field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return (
            len(self.dead_code_findings) +
            len(self.handler_findings) +
            len(self.packet_findings) +
            len(self.security_findings) +
            len(self.concurrency_findings) +
            len(self.database_findings)
        )

    @property
    def all_findings(self) -> List[JavaFinding]:
        return (
            self.dead_code_findings +
            self.handler_findings +
            self.packet_findings +
            self.security_findings +
            self.concurrency_findings +
            self.database_findings
        )


class JavaAnalyzer(BaseAnalyzer):
    """
    Full Java analyzer with comprehensive code analysis.

    Specialized for game server codebases (MapleStory, CosmicMS, etc.)

    Proof Level: P2 (STATIC_PARTIAL)
    Confidence: 0.70-0.90
    """

    name = "java_full"
    description = "Comprehensive Java code analyzer for game servers"

    # Framework patterns
    FRAMEWORKS = {
        "spring": [
            re.compile(r"import\s+org\.springframework"),
            re.compile(r"@(?:Controller|Service|Repository|Component)"),
            re.compile(r"@(?:Autowired|Bean|Configuration)"),
        ],
        "netty": [
            re.compile(r"import\s+io\.netty"),
            re.compile(r"extends\s+\w*ChannelHandler"),
            re.compile(r"ChannelPipeline"),
        ],
        "maplestory": [
            re.compile(r"MapleCharacter|MapleClient"),
            re.compile(r"SendPacketOpcode|RecvPacketOpcode"),
            re.compile(r"PacketHandler|PacketProcessor"),
        ],
        "hibernate": [
            re.compile(r"import\s+org\.hibernate"),
            re.compile(r"@Entity|@Table"),
            re.compile(r"SessionFactory"),
        ],
    }

    # Packet handler patterns (MapleStory specific)
    PACKET_PATTERNS = {
        "handler_def": re.compile(
            r"(?:public\s+)?(?:static\s+)?void\s+handle(\w+)\s*\(",
            re.MULTILINE
        ),
        "opcode_case": re.compile(
            r"case\s+(?:RecvPacketOpcode\.)?(\w+)\s*:",
            re.MULTILINE
        ),
        "packet_reader": re.compile(
            r"(?:slea|packet|reader)\.read(?:Byte|Short|Int|Long|String|MapleAscii)\s*\(",
            re.MULTILINE
        ),
        "packet_writer": re.compile(
            r"(?:mplew|writer)\.write(?:Byte|Short|Int|Long|String)\s*\(",
            re.MULTILINE
        ),
    }

    # Event handler patterns
    EVENT_PATTERNS = {
        "event_handler": re.compile(
            r"@(?:EventHandler|Subscribe)\s*(?:\([^)]*\))?\s*"
            r"(?:public\s+)?void\s+(\w+)\s*\(\s*(\w+Event)",
            re.MULTILINE
        ),
        "listener_class": re.compile(
            r"class\s+(\w+)\s+implements\s+\w*Listener",
            re.MULTILINE
        ),
    }

    # Scheduled task patterns
    SCHEDULED_PATTERNS = {
        "annotation": re.compile(
            r"@(?:Scheduled|Schedule)\s*\([^)]*\)\s*"
            r"(?:public\s+)?void\s+(\w+)",
            re.MULTILINE
        ),
        "timer_task": re.compile(
            r"(?:schedule|scheduleAtFixedRate|scheduleWithFixedDelay)\s*\(",
            re.MULTILINE
        ),
        "executor_service": re.compile(
            r"ExecutorService|ScheduledExecutorService",
            re.MULTILINE
        ),
    }

    # Empty method patterns
    EMPTY_METHOD_PATTERNS = [
        re.compile(r"(?:public|protected|private)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{\s*\}", re.MULTILINE),
        re.compile(r"(?:public|protected|private)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{\s*//[^\n]*\s*\}", re.MULTILINE),
        re.compile(r"(?:public|protected|private)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{\s*return\s*;\s*\}", re.MULTILINE),
    ]

    # Security patterns
    SECURITY_PATTERNS = {
        "sql_injection": re.compile(
            r'(?:executeQuery|executeUpdate|execute)\s*\(\s*["\'].*\+\s*\w+',
            re.MULTILINE
        ),
        "sql_concat": re.compile(
            r'(?:Statement|PreparedStatement)\s*\w*\s*=.*\+\s*\w+',
            re.MULTILINE
        ),
        "command_injection": re.compile(
            r'Runtime\.getRuntime\(\)\.exec\s*\(\s*[^)]*\+',
            re.MULTILINE
        ),
        "path_traversal": re.compile(
            r'new\s+File\s*\([^)]*\+[^)]*\)',
            re.MULTILINE
        ),
        "insecure_random": re.compile(
            r'new\s+Random\s*\(',
            re.MULTILINE
        ),
        "hardcoded_secret": re.compile(
            r'(?:password|secret|apiKey|token)\s*=\s*"[^"]+"',
            re.IGNORECASE
        ),
    }

    # Concurrency patterns
    CONCURRENCY_PATTERNS = {
        "race_condition": re.compile(
            r'(?!synchronized).*\+\+|--(?!.*synchronized)',
            re.MULTILINE
        ),
        "double_checked_locking": re.compile(
            r'if\s*\([^)]+\s*==\s*null\s*\)\s*\{[^}]*synchronized',
            re.MULTILINE | re.DOTALL
        ),
        "thread_unsafe_collection": re.compile(
            r'(?:ArrayList|HashMap|HashSet|LinkedList)\s*<.*>\s*\w+\s*=\s*new',
            re.MULTILINE
        ),
    }

    # Database patterns
    DATABASE_PATTERNS = {
        "unclosed_connection": re.compile(
            r'getConnection\s*\([^)]*\)\s*;(?![^}]*\.close\s*\(\s*\))',
            re.MULTILINE | re.DOTALL
        ),
        "no_try_with_resources": re.compile(
            r'(?:Connection|Statement|ResultSet)\s+\w+\s*=(?!.*try\s*\()',
            re.MULTILINE
        ),
    }

    STANDARD_BLINDSPOTS = [
        "Reflection-based code execution cannot be statically analyzed",
        "Dynamic class loading obscures dependencies",
        "Native methods (JNI) cannot be analyzed",
        "Runtime bytecode generation (ASM, CGLIB) not visible",
        "Aspect-oriented programming (AOP) may modify behavior",
        "OSGi bundle dynamics not traceable",
        "Custom class loaders hide true class hierarchy",
    ]

    def __init__(self):
        self._finding_counter = 0

    def _generate_finding_id(self) -> str:
        self._finding_counter += 1
        return f"java_{self._finding_counter:06d}"

    async def run(
        self,
        repo_path: Path,
        options: Dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        """Run comprehensive Java analysis."""
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

    def _analyze_directory(self, directory: Path) -> JavaAnalysisReport:
        """Analyze all Java files in a directory."""
        report = JavaAnalysisReport(repo_path=str(directory))
        report.blindspots = self.STANDARD_BLINDSPOTS.copy()

        # Find all Java files
        files = list(directory.glob("**/*.java"))
        files = [f for f in files if not self._is_ignored(f)]

        # Detect frameworks first
        for file_path in files:
            self._detect_frameworks(file_path, report)

        # Build opcode to handler mapping
        opcode_handlers: Dict[str, str] = {}
        for file_path in files:
            self._collect_opcode_handlers(file_path, opcode_handlers)

        # Analyze each file
        for file_path in files:
            self._analyze_file(file_path, opcode_handlers, report)

        report.files_analyzed = len(files)

        return report

    def _detect_frameworks(self, file_path: Path, report: JavaAnalysisReport) -> None:
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

    def _collect_opcode_handlers(
        self,
        file_path: Path,
        opcode_handlers: Dict[str, str]
    ) -> None:
        """Collect opcode to handler mappings."""
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        # Find case statements with opcodes
        for match in self.PACKET_PATTERNS["opcode_case"].finditer(content):
            opcode = match.group(1)
            case_pos = match.end()

            # Look for handler call after case
            handler_search = content[case_pos:case_pos + 500]
            handler_match = re.search(r"(\w+Handler)\.handle|handle(\w+)\s*\(", handler_search)

            if handler_match:
                handler_name = handler_match.group(1) or f"handle{handler_match.group(2)}"
                opcode_handlers[opcode] = handler_name

    def _analyze_file(
        self,
        file_path: Path,
        opcode_handlers: Dict[str, str],
        report: JavaAnalysisReport
    ) -> None:
        """Analyze a single Java file."""
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
        self._find_empty_methods(content, rel_path, report)
        self._find_packet_issues(content, rel_path, opcode_handlers, report)
        self._find_handler_issues(content, rel_path, report)
        self._find_security_issues(content, rel_path, report)
        self._find_concurrency_issues(content, rel_path, report)
        self._find_database_issues(content, rel_path, report)

    def _count_constructs(self, content: str, report: JavaAnalysisReport) -> None:
        """Count various code constructs."""
        # Classes
        report.classes_found += len(re.findall(
            r"class\s+\w+",
            content
        ))

        # Methods
        report.methods_found += len(re.findall(
            r"(?:public|protected|private)\s+\w+\s+\w+\s*\(",
            content
        ))

        # Packet handlers
        report.packet_handlers += len(
            self.PACKET_PATTERNS["handler_def"].findall(content)
        )

        # Event handlers
        report.event_handlers += len(
            self.EVENT_PATTERNS["event_handler"].findall(content)
        )

        # Scheduled tasks
        for pattern in self.SCHEDULED_PATTERNS.values():
            report.scheduled_tasks += len(pattern.findall(content))

    def _find_empty_methods(
        self,
        content: str,
        file_path: str,
        report: JavaAnalysisReport
    ) -> None:
        """Find empty methods."""
        for pattern in self.EMPTY_METHOD_PATTERNS:
            for match in pattern.finditer(content):
                method_name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1

                # Skip interface methods, abstract methods
                context = content[max(0, match.start() - 100):match.start()]
                if "interface " in context or "abstract " in context:
                    continue

                report.dead_code_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="empty_method",
                    severity="MEDIUM",
                    message=f"Method '{method_name}' has empty body",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + match.group().count("\n"),
                    code_snippet=match.group()[:100],
                    confidence=0.85,
                    fix_suggestion="Implement method or mark as abstract",
                ))

    def _find_packet_issues(
        self,
        content: str,
        file_path: str,
        opcode_handlers: Dict[str, str],
        report: JavaAnalysisReport
    ) -> None:
        """Find packet handling issues (MapleStory specific)."""
        # Find packet handlers
        for match in self.PACKET_PATTERNS["handler_def"].finditer(content):
            handler_name = f"handle{match.group(1)}"
            handler_start = match.end()
            line_num = content[:match.start()].count("\n") + 1

            # Extract handler body
            handler_body = self._extract_method_body(content, handler_start)
            if not handler_body:
                continue

            # Check if handler reads packet but doesn't process
            has_read = self.PACKET_PATTERNS["packet_reader"].search(handler_body)
            has_write = self.PACKET_PATTERNS["packet_writer"].search(handler_body)
            has_effect = re.search(r"save|update|set|add|remove|drop|gain|lose", handler_body, re.IGNORECASE)

            if has_read and not (has_write or has_effect):
                report.packet_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="packet_no_effect",
                    severity="HIGH",
                    message=f"Packet handler '{handler_name}' reads data but has no visible effect",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + handler_body.count("\n"),
                    confidence=0.75,
                    fix_suggestion="Implement packet processing or add response",
                    evidence={"handler_name": handler_name},
                ))

            # Check for empty handler
            cleaned_body = re.sub(r"//.*$", "", handler_body, flags=re.MULTILINE)
            cleaned_body = re.sub(r"/\*.*?\*/", "", cleaned_body, flags=re.DOTALL)
            cleaned_body = re.sub(r"\s+", "", cleaned_body)

            if cleaned_body in ["{}", "{;}", "{return;}"]:
                report.packet_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="empty_packet_handler",
                    severity="CRITICAL",
                    message=f"Packet handler '{handler_name}' is empty - packets will be silently dropped",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + handler_body.count("\n"),
                    confidence=0.95,
                    fix_suggestion="Implement packet handling or log unhandled packets",
                ))

        # Check for unhandled opcodes
        for match in self.PACKET_PATTERNS["opcode_case"].finditer(content):
            opcode = match.group(1)
            case_pos = match.end()

            # Look for break without handler
            next_content = content[case_pos:case_pos + 200]
            if re.search(r"break\s*;", next_content) and not re.search(r"handle\w+|process\w+", next_content):
                line_num = content[:match.start()].count("\n") + 1

                report.packet_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="unhandled_opcode",
                    severity="HIGH",
                    message=f"Opcode '{opcode}' has case but no handler",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.8,
                    fix_suggestion="Add handler for this opcode or document why it's ignored",
                ))

    def _find_handler_issues(
        self,
        content: str,
        file_path: str,
        report: JavaAnalysisReport
    ) -> None:
        """Find event handler issues."""
        for match in self.EVENT_PATTERNS["event_handler"].finditer(content):
            handler_name = match.group(1)
            event_type = match.group(2)
            handler_start = match.end()
            line_num = content[:match.start()].count("\n") + 1

            # Extract handler body
            handler_body = self._extract_method_body(content, handler_start)
            if not handler_body:
                continue

            # Check for empty handler
            cleaned = re.sub(r"//.*$|/\*.*?\*/|\s+", "", handler_body, flags=re.MULTILINE | re.DOTALL)
            if cleaned in ["{}", "{;}"]:
                report.handler_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type="empty_event_handler",
                    severity="HIGH",
                    message=f"Event handler '{handler_name}' for {event_type} is empty",
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + handler_body.count("\n"),
                    confidence=0.9,
                    fix_suggestion="Implement event handling or remove listener registration",
                ))

            # Check for event.setCancelled without conditions
            if "setCancelled(true)" in handler_body:
                if not re.search(r"if\s*\(", handler_body):
                    report.handler_findings.append(JavaFinding(
                        finding_id=self._generate_finding_id(),
                        finding_type="unconditional_cancel",
                        severity="MEDIUM",
                        message=f"Event '{event_type}' is always cancelled without conditions",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        confidence=0.7,
                        fix_suggestion="Add conditions for cancellation or document why always cancelled",
                    ))

    def _find_security_issues(
        self,
        content: str,
        file_path: str,
        report: JavaAnalysisReport
    ) -> None:
        """Find security issues."""
        for pattern_name, pattern in self.SECURITY_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                severity_map = {
                    "sql_injection": "CRITICAL",
                    "sql_concat": "CRITICAL",
                    "command_injection": "CRITICAL",
                    "path_traversal": "HIGH",
                    "insecure_random": "MEDIUM",
                    "hardcoded_secret": "MEDIUM",
                }

                message_map = {
                    "sql_injection": "SQL injection vulnerability - string concatenation in query",
                    "sql_concat": "SQL injection risk - building query with concatenation",
                    "command_injection": "Command injection - user input in shell command",
                    "path_traversal": "Path traversal risk - user input in file path",
                    "insecure_random": "Insecure random - java.util.Random is predictable",
                    "hardcoded_secret": "Hardcoded secret detected",
                }

                fix_map = {
                    "sql_injection": "Use PreparedStatement with parameterized queries",
                    "sql_concat": "Use PreparedStatement with parameterized queries",
                    "command_injection": "Validate and sanitize input, use ProcessBuilder",
                    "path_traversal": "Validate path and use canonical path checking",
                    "insecure_random": "Use SecureRandom for security-sensitive operations",
                    "hardcoded_secret": "Use environment variables or secure configuration",
                }

                report.security_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity=severity_map.get(pattern_name, "MEDIUM"),
                    message=message_map.get(pattern_name, "Security issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=match.group()[:100],
                    confidence=0.8,
                    fix_suggestion=fix_map.get(pattern_name, "Fix security issue"),
                ))

    def _find_concurrency_issues(
        self,
        content: str,
        file_path: str,
        report: JavaAnalysisReport
    ) -> None:
        """Find concurrency issues."""
        for pattern_name, pattern in self.CONCURRENCY_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                message_map = {
                    "race_condition": "Potential race condition - non-atomic operation without synchronization",
                    "double_checked_locking": "Double-checked locking may be broken - use volatile or holder pattern",
                    "thread_unsafe_collection": "Thread-unsafe collection in multi-threaded context",
                }

                fix_map = {
                    "race_condition": "Use synchronized block, AtomicInteger, or volatile",
                    "double_checked_locking": "Use volatile keyword or lazy holder idiom",
                    "thread_unsafe_collection": "Use ConcurrentHashMap, CopyOnWriteArrayList, or Collections.synchronized*",
                }

                report.concurrency_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity="HIGH",
                    message=message_map.get(pattern_name, "Concurrency issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.65,
                    fix_suggestion=fix_map.get(pattern_name, "Fix concurrency issue"),
                ))

    def _find_database_issues(
        self,
        content: str,
        file_path: str,
        report: JavaAnalysisReport
    ) -> None:
        """Find database issues."""
        for pattern_name, pattern in self.DATABASE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                message_map = {
                    "unclosed_connection": "Database connection may not be closed",
                    "no_try_with_resources": "JDBC resource without try-with-resources",
                }

                fix_map = {
                    "unclosed_connection": "Use try-with-resources or ensure close() in finally",
                    "no_try_with_resources": "Use try-with-resources for automatic cleanup",
                }

                report.database_findings.append(JavaFinding(
                    finding_id=self._generate_finding_id(),
                    finding_type=pattern_name,
                    severity="HIGH",
                    message=message_map.get(pattern_name, "Database issue detected"),
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    confidence=0.7,
                    fix_suggestion=fix_map.get(pattern_name, "Fix database resource handling"),
                ))

    def _extract_method_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract method body from starting position."""
        brace_count = 0
        in_body = False
        body_start = start_pos
        body_end = start_pos

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


def analyze_java(path: Path) -> JavaAnalysisReport:
    """
    Convenience function to analyze Java code.
    """
    analyzer = JavaAnalyzer()
    return analyzer._analyze_directory(path)
