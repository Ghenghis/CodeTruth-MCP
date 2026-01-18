"""
Java Graph Builder

Parses Java code to build reachability graphs.
Handles classes, methods, interfaces, annotations, and package structure.

Designed for game server codebases (MapleStory, CosmicMS, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..graph import (
    ReachabilityGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    SourceLocation,
)


class JavaGraphBuilder:
    """
    Builds a reachability graph from Java source files.

    Specialized for game server patterns including:
    - Packet handlers (MapleStory protocol)
    - Event listeners
    - Scheduled tasks
    - Database operations (JDBC, JPA)
    - Network handlers
    """

    # Java-specific patterns
    PATTERNS = {
        # Package declaration
        "package": re.compile(
            r"^package\s+([\w.]+)\s*;",
            re.MULTILINE
        ),

        # Import statements
        "import": re.compile(
            r"^import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;",
            re.MULTILINE
        ),

        # Class definitions
        "class_def": re.compile(
            r"(?:public|protected|private)?\s*(?:abstract|final)?\s*class\s+(\w+)"
            r"(?:\s*<[^>]+>)?"
            r"(?:\s+extends\s+(\w+))?"
            r"(?:\s+implements\s+([\w,\s]+))?\s*\{",
            re.MULTILINE
        ),

        # Interface definitions
        "interface_def": re.compile(
            r"(?:public|protected|private)?\s*interface\s+(\w+)"
            r"(?:\s*<[^>]+>)?"
            r"(?:\s+extends\s+([\w,\s]+))?\s*\{",
            re.MULTILINE
        ),

        # Enum definitions
        "enum_def": re.compile(
            r"(?:public|protected|private)?\s*enum\s+(\w+)"
            r"(?:\s+implements\s+([\w,\s]+))?\s*\{",
            re.MULTILINE
        ),

        # Method definitions
        "method_def": re.compile(
            r"(?:@\w+(?:\([^)]*\))?\s*)*"
            r"(?:public|protected|private)\s+"
            r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
            r"(?:(?:<[^>]+>\s+)?(\w+(?:<[^>]+>)?)\s+)"
            r"(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
            re.MULTILINE
        ),

        # Constructor definitions
        "constructor_def": re.compile(
            r"(?:public|protected|private)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
            re.MULTILINE
        ),

        # Annotation definitions
        "annotation": re.compile(
            r"@(\w+)(?:\s*\(([^)]*)\))?",
            re.MULTILINE
        ),

        # Method calls
        "method_call": re.compile(
            r"(?:this\.|super\.)?(\w+)\s*\(",
            re.MULTILINE
        ),

        # Object method calls
        "object_method_call": re.compile(
            r"(\w+)\.(\w+)\s*\(",
            re.MULTILINE
        ),

        # Static method calls
        "static_method_call": re.compile(
            r"(\w+)\.(\w+)\s*\(",
            re.MULTILINE
        ),

        # New object creation
        "new_object": re.compile(
            r"new\s+(\w+)(?:<[^>]+>)?\s*\(",
            re.MULTILINE
        ),

        # Field declarations
        "field_def": re.compile(
            r"(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=|;)",
            re.MULTILINE
        ),

        # Lambda expressions
        "lambda": re.compile(
            r"\(([^)]*)\)\s*->\s*(?:\{|[^{])",
            re.MULTILINE
        ),

        # Thread/Runnable patterns
        "runnable": re.compile(
            r"(?:new\s+(?:Thread|Runnable)\s*\(|Runnable\s+\w+\s*=)",
            re.MULTILINE
        ),

        # SQL queries
        "sql_query": re.compile(
            r'(?:executeQuery|executeUpdate|execute)\s*\(\s*"([^"]+)"',
            re.MULTILINE | re.IGNORECASE
        ),

        # PreparedStatement patterns
        "prepared_statement": re.compile(
            r'prepareStatement\s*\(\s*"([^"]+)"',
            re.MULTILINE | re.IGNORECASE
        ),

        # Exception handling
        "try_block": re.compile(
            r"try\s*\{",
            re.MULTILINE
        ),
        "catch_block": re.compile(
            r"catch\s*\(\s*(\w+(?:\s*\|\s*\w+)*)\s+\w+\s*\)",
            re.MULTILINE
        ),
    }

    # MapleStory/Game server specific patterns
    GAME_PATTERNS = {
        # Packet handlers (MapleStory style)
        "packet_handler": re.compile(
            r"(?:public\s+)?(?:static\s+)?void\s+handle(\w+Packet|\w+Request)\s*\(",
            re.MULTILINE
        ),

        # Packet opcodes
        "packet_opcode": re.compile(
            r"(?:case\s+|RecvPacketOpcode\.)(\w+)\s*:",
            re.MULTILINE
        ),

        # Channel handler (Netty)
        "channel_handler": re.compile(
            r"class\s+(\w+Handler)\s+extends\s+\w*(?:ChannelHandler|InboundHandler)",
            re.MULTILINE
        ),

        # Event handlers
        "event_handler": re.compile(
            r"@(?:EventHandler|Subscribe)\s*(?:\([^)]*\))?\s*"
            r"(?:public\s+)?void\s+(\w+)\s*\(\s*(\w+Event)",
            re.MULTILINE
        ),

        # Scheduled tasks
        "scheduled_task": re.compile(
            r"@(?:Scheduled|Schedule)\s*\([^)]*\)\s*"
            r"(?:public\s+)?void\s+(\w+)\s*\(",
            re.MULTILINE
        ),

        # Timer tasks
        "timer_task": re.compile(
            r"(?:schedule|scheduleAtFixedRate)\s*\(\s*(?:new\s+)?(\w+)",
            re.MULTILINE
        ),

        # Player/Character handlers
        "player_handler": re.compile(
            r"void\s+handle(\w*Player\w*|\w*Character\w*)\s*\(",
            re.MULTILINE | re.IGNORECASE
        ),

        # Map/World handlers
        "world_handler": re.compile(
            r"void\s+(\w*(?:Map|World|Field)\w*)\s*\(",
            re.MULTILINE | re.IGNORECASE
        ),

        # NPC handlers
        "npc_handler": re.compile(
            r"void\s+handle(\w*NPC\w*|\w*Npc\w*)\s*\(",
            re.MULTILINE | re.IGNORECASE
        ),

        # Combat/Attack handlers
        "combat_handler": re.compile(
            r"void\s+handle(\w*Attack\w*|\w*Damage\w*|\w*Combat\w*)\s*\(",
            re.MULTILINE | re.IGNORECASE
        ),

        # Quest handlers
        "quest_handler": re.compile(
            r"void\s+handle(\w*Quest\w*)\s*\(",
            re.MULTILINE | re.IGNORECASE
        ),
    }

    def __init__(self):
        self.graph = ReachabilityGraph()
        self._node_counter = 0
        self._package_map: Dict[str, str] = {}  # package -> node_id
        self._class_map: Dict[str, str] = {}  # class_name -> node_id
        self._method_map: Dict[str, str] = {}  # full_method_name -> node_id
        self._current_package = ""
        self._current_class = ""

    def _generate_node_id(self, prefix: str) -> str:
        self._node_counter += 1
        return f"{prefix}_{self._node_counter:06d}"

    def build_from_directory(self, directory: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from all Java files in a directory.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(directory)
        self.graph.language_versions["java"] = "17"

        # Find all Java files
        files = list(directory.glob("**/*.java"))

        # Exclude build directories and tests (optional)
        files = [
            f for f in files
            if "target" not in str(f)
            and "build" not in str(f)
            and ".git" not in str(f)
            and "node_modules" not in str(f)
        ]

        # First pass: collect all definitions
        for file_path in files:
            self._analyze_file(file_path)

        # Second pass: resolve references and build edges
        for file_path in files:
            self._resolve_references(file_path)

        # Third pass: detect game server patterns
        for file_path in files:
            self._detect_game_patterns(file_path)

        return self.graph

    def build_from_file(self, file_path: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from a single file.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(file_path.parent)
        self.graph.language_versions["java"] = "17"

        self._analyze_file(file_path)
        self._resolve_references(file_path)
        self._detect_game_patterns(file_path)

        return self.graph

    def _analyze_file(self, file_path: Path) -> None:
        """
        Analyze a single file and add nodes to the graph.
        """
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)
        lines = content.split("\n")

        # Extract package name
        package_match = self.PATTERNS["package"].search(content)
        if package_match:
            self._current_package = package_match.group(1)

        # Detect if this is an entry point
        if self._is_entry_point(file_path, content):
            entry_node = GraphNode(
                id=self._generate_node_id("entry"),
                node_type=NodeType.ENTRY_POINT,
                name=file_path.stem,
                location=SourceLocation(rel_path, 1, len(lines)),
                language="java",
                metadata={
                    "package": self._current_package,
                    "file_type": self._get_file_type(file_path, content),
                },
            )
            self.graph.add_node(entry_node)

        # Find class definitions
        for match in self.PATTERNS["class_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            class_name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)

            self._current_class = class_name
            full_name = f"{self._current_package}.{class_name}" if self._current_package else class_name

            # Find annotations above the class
            annotations = self._find_annotations_before(content, match.start())

            node = GraphNode(
                id=self._generate_node_id("class"),
                node_type=NodeType.CLASS,
                name=class_name,
                location=SourceLocation(rel_path, line_num, line_num + 100),
                language="java",
                metadata={
                    "full_name": full_name,
                    "package": self._current_package,
                    "extends": extends,
                    "implements": implements.split(",") if implements else [],
                    "annotations": annotations,
                },
            )
            self.graph.add_node(node)
            self._class_map[class_name] = node.id
            self._class_map[full_name] = node.id

        # Find interface definitions
        for match in self.PATTERNS["interface_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            interface_name = match.group(1)
            extends = match.group(2)

            node = GraphNode(
                id=self._generate_node_id("interface"),
                node_type=NodeType.INTERFACE,
                name=interface_name,
                location=SourceLocation(rel_path, line_num, line_num + 50),
                language="java",
                metadata={
                    "package": self._current_package,
                    "extends": extends.split(",") if extends else [],
                },
            )
            self.graph.add_node(node)

        # Find enum definitions
        for match in self.PATTERNS["enum_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            enum_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("enum"),
                node_type=NodeType.ENUM,
                name=enum_name,
                location=SourceLocation(rel_path, line_num, line_num + 30),
                language="java",
                metadata={"package": self._current_package},
            )
            self.graph.add_node(node)

        # Find method definitions
        for match in self.PATTERNS["method_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)

            # Get method body for analysis
            method_body = self._extract_method_body(content, match.end())
            is_empty = self._is_empty_method(method_body)
            is_debug_only = self._is_debug_only_method(method_body)

            # Find annotations
            annotations = self._find_annotations_before(content, match.start())

            # Determine if this is a handler
            is_handler = (
                "Handler" in method_name or
                method_name.startswith("handle") or
                method_name.startswith("on") or
                "EventHandler" in annotations or
                "Subscribe" in annotations
            )

            node_type = NodeType.HANDLER if is_handler else NodeType.METHOD

            node = GraphNode(
                id=self._generate_node_id("method"),
                node_type=node_type,
                name=method_name,
                location=SourceLocation(rel_path, line_num, line_num + 30),
                language="java",
                metadata={
                    "return_type": return_type,
                    "parameters": params,
                    "class": self._current_class,
                    "annotations": annotations,
                    "is_empty": is_empty,
                    "is_debug_only": is_debug_only,
                },
            )
            self.graph.add_node(node)

            full_method_name = f"{self._current_class}.{method_name}"
            self._method_map[method_name] = node.id
            self._method_map[full_method_name] = node.id

        # Find packet handlers (game server specific)
        for match in self.GAME_PATTERNS["packet_handler"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            handler_name = f"handle{match.group(1)}"

            node = GraphNode(
                id=self._generate_node_id("packet_handler"),
                node_type=NodeType.HANDLER,
                name=handler_name,
                location=SourceLocation(rel_path, line_num, line_num + 30),
                language="java",
                metadata={
                    "handler_type": "packet",
                    "is_game_logic": True,
                },
            )
            self.graph.add_node(node)

        # Find scheduled tasks
        for match in self.GAME_PATTERNS["scheduled_task"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            task_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("scheduled"),
                node_type=NodeType.SCHEDULED_TASK,
                name=task_name,
                location=SourceLocation(rel_path, line_num, line_num + 20),
                language="java",
                metadata={
                    "is_scheduled": True,
                    "schedule_verified": False,  # Need to verify cron/timer config
                },
            )
            self.graph.add_node(node)

        # Find event handlers
        for match in self.GAME_PATTERNS["event_handler"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            handler_name = match.group(1)
            event_type = match.group(2)

            node = GraphNode(
                id=self._generate_node_id("event_handler"),
                node_type=NodeType.HANDLER,
                name=handler_name,
                location=SourceLocation(rel_path, line_num, line_num + 20),
                language="java",
                metadata={
                    "event_type": event_type,
                    "handler_type": "event",
                },
            )
            self.graph.add_node(node)

    def _resolve_references(self, file_path: Path) -> None:
        """
        Resolve references and create edges between nodes.
        """
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)

        # Find method calls
        for match in self.PATTERNS["method_call"].finditer(content):
            method_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Skip constructors and common methods
            if method_name in self._get_common_methods():
                continue

            # Find target node
            if method_name in self._method_map:
                target_id = self._method_map[method_name]
                source_node = self._find_method_at_location(rel_path, line_num)
                if source_node and source_node.id != target_id:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find object method calls
        for match in self.PATTERNS["object_method_call"].finditer(content):
            obj_name = match.group(1)
            method_name = match.group(2)
            line_num = content[:match.start()].count("\n") + 1

            # Skip common objects
            if obj_name.lower() in {"system", "log", "logger", "console"}:
                continue

            # Find target method
            full_name = f"{obj_name}.{method_name}"
            if full_name in self._method_map:
                target_id = self._method_map[full_name]
                source_node = self._find_method_at_location(rel_path, line_num)
                if source_node and source_node.id != target_id:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find class instantiations
        for match in self.PATTERNS["new_object"].finditer(content):
            class_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            if class_name in self._class_map:
                target_id = self._class_map[class_name]
                source_node = self._find_method_at_location(rel_path, line_num)
                if source_node:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.INSTANTIATES,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find inheritance relationships
        for node in list(self.graph.nodes.values()):
            if node.node_type == NodeType.CLASS:
                extends = node.metadata.get("extends")
                if extends and extends in self._class_map:
                    edge = GraphEdge(
                        source_id=node.id,
                        target_id=self._class_map[extends],
                        edge_type=EdgeType.EXTENDS,
                        evidence_locations=[node.location],
                    )
                    self.graph.add_edge(edge)

                implements = node.metadata.get("implements", [])
                for interface in implements:
                    interface = interface.strip()
                    if interface in self._class_map:
                        edge = GraphEdge(
                            source_id=node.id,
                            target_id=self._class_map[interface],
                            edge_type=EdgeType.IMPLEMENTS,
                            evidence_locations=[node.location],
                        )
                        self.graph.add_edge(edge)

    def _detect_game_patterns(self, file_path: Path) -> None:
        """
        Detect game server specific patterns.
        """
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)

        # Find packet opcode to handler mappings
        opcode_to_handler: Dict[str, int] = {}

        for match in self.GAME_PATTERNS["packet_opcode"].finditer(content):
            opcode = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            opcode_to_handler[opcode] = line_num

            # Look for handler call after this case
            case_end = match.end()
            next_case = content.find("case ", case_end)
            if next_case == -1:
                next_case = len(content)

            case_block = content[case_end:next_case]

            # Find handler call in case block
            handler_call = re.search(r"handle(\w+)\s*\(", case_block)
            if handler_call:
                handler_name = f"handle{handler_call.group(1)}"

                # Find the handler node
                for node in self.graph.nodes.values():
                    if node.node_type == NodeType.HANDLER and node.name == handler_name:
                        # Create dispatch edge from opcode
                        route_node = GraphNode(
                            id=self._generate_node_id("opcode"),
                            node_type=NodeType.ROUTE,
                            name=f"opcode:{opcode}",
                            location=SourceLocation(rel_path, line_num, line_num),
                            language="java",
                            metadata={"opcode": opcode},
                        )
                        self.graph.add_node(route_node)

                        edge = GraphEdge(
                            source_id=route_node.id,
                            target_id=node.id,
                            edge_type=EdgeType.DISPATCHES,
                            evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                        )
                        self.graph.add_edge(edge)
                        break

        # Find empty handlers (no-op detection)
        for node in list(self.graph.nodes.values()):
            if node.node_type in {NodeType.HANDLER, NodeType.METHOD}:
                if node.metadata.get("is_empty"):
                    # Create phantom node for empty handler
                    phantom_id = self._generate_node_id("empty_handler")
                    phantom_node = GraphNode(
                        id=phantom_id,
                        node_type=NodeType.STATE,
                        name="EMPTY_HANDLER",
                        location=node.location,
                        language="java",
                        metadata={
                            "is_phantom": True,
                            "issue_type": "empty_handler",
                            "severity": "HIGH",
                        },
                    )
                    self.graph.add_node(phantom_node)

                    edge = GraphEdge(
                        source_id=node.id,
                        target_id=phantom_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[node.location],
                        metadata={"is_no_op": True},
                    )
                    self.graph.add_edge(edge)

    def _is_entry_point(self, file_path: Path, content: str) -> bool:
        """Determine if a file is an entry point."""
        # Has main method
        if re.search(r"public\s+static\s+void\s+main\s*\(\s*String", content):
            return True

        # Spring Boot application
        if "@SpringBootApplication" in content:
            return True

        # Servlet
        if "extends HttpServlet" in content:
            return True

        # Netty handler
        if "extends ChannelInboundHandlerAdapter" in content:
            return True

        # Game server main
        name = file_path.stem.lower()
        if name in {"main", "server", "launcher", "application", "bootstrap"}:
            return True

        return False

    def _get_file_type(self, file_path: Path, content: str) -> str:
        """Determine the type of file."""
        name = file_path.stem

        if "Handler" in name:
            return "handler"
        if "Controller" in name:
            return "controller"
        if "Service" in name:
            return "service"
        if "Repository" in name or "DAO" in name:
            return "repository"
        if "Entity" in name or "Model" in name:
            return "entity"
        if "Packet" in name:
            return "packet"
        if "Config" in name:
            return "config"
        if "Test" in name:
            return "test"

        return "class"

    def _extract_method_body(self, content: str, start_pos: int) -> str:
        """Extract the body of a method starting from a position."""
        brace_count = 0
        in_body = False
        body_start = start_pos
        body_end = start_pos

        # Find the opening brace first
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == "{":
                if not in_body:
                    body_start = i
                    in_body = True
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and in_body:
                    body_end = i
                    break

        return content[body_start:body_end + 1]

    def _is_empty_method(self, body: str) -> bool:
        """Check if a method body is empty or essentially empty."""
        # Remove comments
        cleaned = re.sub(r"//.*$", "", body, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\s+", "", cleaned)

        empty_patterns = [
            "{}",
            "{;}",
            "{return;}",
            "{return}",
            "{returnnull;}",
            "{returnfalse;}",
            "{returntrue;}",
        ]

        return cleaned in empty_patterns

    def _is_debug_only_method(self, body: str) -> bool:
        """Check if a method only contains debug statements."""
        # Remove debug statements
        cleaned = re.sub(r"System\.out\.print(?:ln)?\s*\([^)]*\)\s*;", "", body)
        cleaned = re.sub(r"(?:log|logger|LOG|LOGGER)\.\w+\s*\([^)]*\)\s*;", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\s+", "", cleaned)

        return cleaned in ["{}", "{;}", "{return;}", "{return}"]

    def _find_annotations_before(self, content: str, pos: int) -> List[str]:
        """Find annotations immediately before a position."""
        # Look back for annotations
        lookback = content[max(0, pos - 500):pos]
        annotations = []

        for match in self.PATTERNS["annotation"].finditer(lookback):
            annotations.append(match.group(1))

        return annotations

    def _find_method_at_location(self, file_path: str, line: int) -> Optional[GraphNode]:
        """Find the method that contains a given line."""
        candidates = []
        for node in self.graph.nodes.values():
            if node.node_type in {NodeType.METHOD, NodeType.HANDLER}:
                if node.location.file_path == file_path:
                    if node.location.line_start <= line <= node.location.line_end + 50:
                        candidates.append(node)

        if candidates:
            return min(candidates, key=lambda n: abs(n.location.line_start - line))
        return None

    def _get_common_methods(self) -> Set[str]:
        """Return set of common Java methods to ignore."""
        return {
            # Object methods
            "toString", "hashCode", "equals", "clone", "finalize", "getClass",
            # Collection methods
            "add", "remove", "get", "set", "size", "isEmpty", "contains",
            "put", "clear", "containsKey", "containsValue",
            "iterator", "forEach", "stream",
            # String methods
            "length", "charAt", "substring", "indexOf", "split", "trim",
            "toLowerCase", "toUpperCase", "replace", "matches",
            # IO
            "read", "write", "close", "flush",
            # Logging
            "debug", "info", "warn", "error", "trace",
            # Common
            "valueOf", "parseInt", "parseDouble", "format",
            "print", "println", "printf",
        }


def build_java_graph(path: Path) -> ReachabilityGraph:
    """
    Convenience function to build a graph from Java files.
    """
    builder = JavaGraphBuilder()
    if path.is_file():
        return builder.build_from_file(path)
    else:
        return builder.build_from_directory(path)
