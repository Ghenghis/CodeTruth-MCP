"""
PHP Graph Builder

Parses PHP code to build reachability graphs.
Handles classes, methods, functions, AJAX handlers, cron jobs, and database operations.

Designed for game server codebases (Travian, TWLan, MapleStory servers).
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


class PHPGraphBuilder:
    """
    Builds a reachability graph from PHP source files.

    Specialized for game server patterns including:
    - AJAX handlers that return success without effect
    - Cron jobs that are defined but never scheduled
    - Database operations (PDO, mysqli)
    - Session-based authentication
    - Include/require chains
    """

    # PHP-specific patterns
    PATTERNS = {
        # Class definitions
        "class_def": re.compile(
            r"(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{",
            re.MULTILINE
        ),

        # Interface definitions
        "interface_def": re.compile(
            r"interface\s+(\w+)(?:\s+extends\s+[\w,\s]+)?\s*\{",
            re.MULTILINE
        ),

        # Method definitions (inside classes)
        "method_def": re.compile(
            r"(?:public|protected|private)\s+(?:static\s+)?function\s+(\w+)\s*\(",
            re.MULTILINE
        ),

        # Function definitions (standalone)
        "function_def": re.compile(
            r"^function\s+(\w+)\s*\(",
            re.MULTILINE
        ),

        # Handler patterns (AJAX/form handlers)
        "handler_def": re.compile(
            r"function\s+(handle\w+|process\w+|ajax\w+|do\w+Action)\s*\(",
            re.MULTILINE
        ),

        # Cron job patterns
        "cron_def": re.compile(
            r"function\s+(cron\w+|tick\w+|schedule\w+|process\w+Queue)\s*\(",
            re.MULTILINE
        ),

        # Route patterns (switch/case action handling)
        "action_route": re.compile(
            r"switch\s*\(\s*\$(?:_GET|_POST|_REQUEST)\s*\[\s*['\"](\w+)['\"]\s*\]\s*\)",
            re.MULTILINE
        ),

        # Case handlers in switch
        "case_handler": re.compile(
            r"case\s+['\"](\w+)['\"]\s*:",
            re.MULTILINE
        ),

        # Database operations - PDO
        "pdo_query": re.compile(
            r"\$\w+->(?:query|prepare|exec)\s*\(\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE | re.IGNORECASE
        ),

        # Database operations - mysqli
        "mysqli_query": re.compile(
            r"mysqli?_query\s*\(\s*\$\w+\s*,\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE | re.IGNORECASE
        ),

        # Raw SQL patterns
        "sql_select": re.compile(
            r"SELECT\s+.+?\s+FROM\s+(\w+)",
            re.IGNORECASE | re.DOTALL
        ),
        "sql_insert": re.compile(
            r"INSERT\s+INTO\s+(\w+)",
            re.IGNORECASE
        ),
        "sql_update": re.compile(
            r"UPDATE\s+(\w+)\s+SET",
            re.IGNORECASE
        ),
        "sql_delete": re.compile(
            r"DELETE\s+FROM\s+(\w+)",
            re.IGNORECASE
        ),

        # Include/require
        "include": re.compile(
            r"(?:include|include_once|require|require_once)\s*\(?['\"]([^'\"]+)['\"]\)?",
            re.MULTILINE
        ),

        # JSON response (success pattern)
        "json_success": re.compile(
            r"(?:echo|return)\s+json_encode\s*\(\s*\[\s*['\"]success['\"]\s*=>\s*true",
            re.MULTILINE
        ),

        # JSON response (error pattern)
        "json_error": re.compile(
            r"(?:echo|return)\s+json_encode\s*\(\s*\[\s*['\"](?:success|error)['\"]\s*=>\s*false",
            re.MULTILINE
        ),

        # Session access
        "session_access": re.compile(
            r"\$_SESSION\s*\[\s*['\"](\w+)['\"]\s*\]",
            re.MULTILINE
        ),

        # Superglobal access
        "get_access": re.compile(
            r"\$_GET\s*\[\s*['\"](\w+)['\"]\s*\]",
            re.MULTILINE
        ),
        "post_access": re.compile(
            r"\$_POST\s*\[\s*['\"](\w+)['\"]\s*\]",
            re.MULTILINE
        ),
        "request_access": re.compile(
            r"\$_REQUEST\s*\[\s*['\"](\w+)['\"]\s*\]",
            re.MULTILINE
        ),

        # Function calls
        "function_call": re.compile(
            r"(?<![->$])(\w+)\s*\(",
            re.MULTILINE
        ),

        # Method calls
        "method_call": re.compile(
            r"\$(\w+)->(\w+)\s*\(",
            re.MULTILINE
        ),

        # Static method calls
        "static_call": re.compile(
            r"(\w+)::(\w+)\s*\(",
            re.MULTILINE
        ),

        # New object creation
        "new_object": re.compile(
            r"new\s+(\w+)\s*\(",
            re.MULTILINE
        ),

        # CLI detection
        "cli_check": re.compile(
            r"php_sapi_name\s*\(\s*\)\s*(?:===?|!==?)\s*['\"]cli['\"]",
            re.MULTILINE
        ),

        # Entry point detection
        "entry_point": re.compile(
            r"basename\s*\(\s*__FILE__\s*\)\s*===?\s*basename\s*\(",
            re.MULTILINE
        ),
    }

    # Game server specific patterns
    GAME_PATTERNS = {
        # Resource tick handlers (Travian-style)
        "resource_tick": re.compile(
            r"function\s+(\w*resource\w*tick\w*|\w*tick\w*resource\w*)",
            re.MULTILINE | re.IGNORECASE
        ),

        # Building queue handlers
        "building_queue": re.compile(
            r"function\s+(\w*building\w*queue\w*|\w*process\w*building\w*)",
            re.MULTILINE | re.IGNORECASE
        ),

        # Troop training handlers
        "troop_training": re.compile(
            r"function\s+(\w*train\w*troop\w*|\w*troop\w*train\w*)",
            re.MULTILINE | re.IGNORECASE
        ),

        # Attack/combat handlers
        "combat_handler": re.compile(
            r"function\s+(\w*attack\w*|\w*combat\w*|\w*battle\w*)",
            re.MULTILINE | re.IGNORECASE
        ),

        # Village management
        "village_handler": re.compile(
            r"function\s+(\w*village\w*|\w*settlement\w*)",
            re.MULTILINE | re.IGNORECASE
        ),
    }

    def __init__(self):
        self.graph = ReachabilityGraph()
        self._node_counter = 0
        self._include_map: Dict[str, Set[str]] = {}
        self._class_map: Dict[str, str] = {}  # class_name -> node_id
        self._function_map: Dict[str, str] = {}  # function_name -> node_id

    def _generate_node_id(self, prefix: str) -> str:
        self._node_counter += 1
        return f"{prefix}_{self._node_counter:06d}"

    def build_from_directory(self, directory: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from all PHP files in a directory.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(directory)
        self.graph.language_versions["php"] = "8.x"

        # Find all PHP files
        files = list(directory.glob("**/*.php"))

        # Exclude vendor and common excludes
        files = [
            f for f in files
            if "vendor" not in str(f)
            and "node_modules" not in str(f)
            and ".git" not in str(f)
        ]

        # First pass: collect all definitions
        for file_path in files:
            self._analyze_file(file_path)

        # Second pass: resolve references and build edges
        for file_path in files:
            self._resolve_references(file_path)

        # Third pass: detect no-op patterns
        for file_path in files:
            self._detect_no_op_patterns(file_path)

        return self.graph

    def build_from_file(self, file_path: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from a single file.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(file_path.parent)
        self.graph.language_versions["php"] = "8.x"

        self._analyze_file(file_path)
        self._resolve_references(file_path)
        self._detect_no_op_patterns(file_path)

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

        # Detect entry points
        if self._is_entry_point(file_path, content):
            entry_node = GraphNode(
                id=self._generate_node_id("entry"),
                node_type=NodeType.ENTRY_POINT,
                name=file_path.name,
                location=SourceLocation(rel_path, 1, len(lines)),
                language="php",
                metadata={"file_type": self._get_file_type(file_path, content)},
            )
            self.graph.add_node(entry_node)

        # Find class definitions
        for match in self.PATTERNS["class_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            class_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("class"),
                node_type=NodeType.CLASS,
                name=class_name,
                location=SourceLocation(rel_path, line_num, line_num + 50),
                language="php",
                metadata={"class_name": class_name},
            )
            self.graph.add_node(node)
            self._class_map[class_name] = node.id

        # Find interface definitions
        for match in self.PATTERNS["interface_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            interface_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("interface"),
                node_type=NodeType.INTERFACE,
                name=interface_name,
                location=SourceLocation(rel_path, line_num, line_num + 20),
                language="php",
                metadata={"interface_name": interface_name},
            )
            self.graph.add_node(node)

        # Find method definitions
        for match in self.PATTERNS["method_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            method_name = match.group(1)

            # Get method body to check for no-op patterns
            method_body = self._extract_function_body(content, match.end())
            is_empty = self._is_empty_function(method_body)
            is_debug_only = self._is_debug_only_function(method_body)

            node = GraphNode(
                id=self._generate_node_id("method"),
                node_type=NodeType.METHOD,
                name=method_name,
                location=SourceLocation(rel_path, line_num, line_num + 20),
                language="php",
                metadata={
                    "method_name": method_name,
                    "is_empty": is_empty,
                    "is_debug_only": is_debug_only,
                },
            )
            self.graph.add_node(node)

        # Find standalone function definitions
        for match in self.PATTERNS["function_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            func_name = match.group(1)

            function_body = self._extract_function_body(content, match.end())
            is_empty = self._is_empty_function(function_body)
            is_debug_only = self._is_debug_only_function(function_body)

            node = GraphNode(
                id=self._generate_node_id("function"),
                node_type=NodeType.FUNCTION,
                name=func_name,
                location=SourceLocation(rel_path, line_num, line_num + 20),
                language="php",
                metadata={
                    "function_name": func_name,
                    "is_empty": is_empty,
                    "is_debug_only": is_debug_only,
                },
            )
            self.graph.add_node(node)
            self._function_map[func_name] = node.id

        # Find handler definitions (AJAX, form, etc.)
        for match in self.PATTERNS["handler_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            handler_name = match.group(1)

            handler_body = self._extract_function_body(content, match.end())
            has_db_write = self._has_database_write(handler_body)
            has_success_return = self._has_success_return(handler_body)
            is_fake_success = has_success_return and not has_db_write

            node = GraphNode(
                id=self._generate_node_id("handler"),
                node_type=NodeType.HANDLER,
                name=handler_name,
                location=SourceLocation(rel_path, line_num, line_num + 30),
                language="php",
                metadata={
                    "handler_name": handler_name,
                    "has_db_write": has_db_write,
                    "has_success_return": has_success_return,
                    "is_fake_success": is_fake_success,
                },
            )
            self.graph.add_node(node)

        # Find cron job definitions
        for match in self.PATTERNS["cron_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            cron_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("cron"),
                node_type=NodeType.CRON_JOB,
                name=cron_name,
                location=SourceLocation(rel_path, line_num, line_num + 30),
                language="php",
                metadata={
                    "cron_name": cron_name,
                    "is_scheduled": False,  # Default - will be updated if crontab found
                },
            )
            self.graph.add_node(node)

        # Find action routes
        for match in self.PATTERNS["action_route"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            param_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("route"),
                node_type=NodeType.ROUTE,
                name=f"action:{param_name}",
                location=SourceLocation(rel_path, line_num, line_num + 5),
                language="php",
                metadata={"param_name": param_name},
            )
            self.graph.add_node(node)

        # Find game-specific patterns
        self._find_game_patterns(file_path, content)

    def _find_game_patterns(self, file_path: Path, content: str) -> None:
        """Find game server specific patterns."""
        rel_path = str(file_path)

        for pattern_name, pattern in self.GAME_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                func_name = match.group(1)

                node = GraphNode(
                    id=self._generate_node_id("game_handler"),
                    node_type=NodeType.HANDLER,
                    name=func_name,
                    location=SourceLocation(rel_path, line_num, line_num + 30),
                    language="php",
                    metadata={
                        "handler_type": pattern_name,
                        "is_game_logic": True,
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

        # Find include/require statements
        for match in self.PATTERNS["include"].finditer(content):
            included_file = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Try to find the included file in our graph
            for node in self.graph.nodes.values():
                if node.node_type == NodeType.ENTRY_POINT:
                    if included_file in node.name or node.name in included_file:
                        # Find source node
                        source_node = self._find_entry_for_file(rel_path)
                        if source_node:
                            edge = GraphEdge(
                                source_id=source_node.id,
                                target_id=node.id,
                                edge_type=EdgeType.INCLUDES,
                                evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                            )
                            self.graph.add_edge(edge)

        # Find function calls
        for match in self.PATTERNS["function_call"].finditer(content):
            func_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Skip PHP built-in functions
            if func_name in self._get_builtin_functions():
                continue

            # Find target node
            if func_name in self._function_map:
                target_id = self._function_map[func_name]
                source_node = self._find_function_at_location(rel_path, line_num)
                if source_node:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find method calls
        for match in self.PATTERNS["method_call"].finditer(content):
            obj_name = match.group(1)
            method_name = match.group(2)
            line_num = content[:match.start()].count("\n") + 1

            # Find target method node
            target_node = self._find_node_by_name(method_name, NodeType.METHOD)
            if target_node:
                source_node = self._find_function_at_location(rel_path, line_num)
                if source_node and source_node.id != target_node.id:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_node.id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find static method calls
        for match in self.PATTERNS["static_call"].finditer(content):
            class_name = match.group(1)
            method_name = match.group(2)
            line_num = content[:match.start()].count("\n") + 1

            # Find class node
            if class_name in self._class_map:
                target_id = self._class_map[class_name]
                source_node = self._find_function_at_location(rel_path, line_num)
                if source_node:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find case handlers and connect to route
        for route_match in self.PATTERNS["action_route"].finditer(content):
            route_line = content[:route_match.start()].count("\n") + 1
            route_node = None

            for node in self.graph.nodes.values():
                if node.node_type == NodeType.ROUTE:
                    if abs(node.location.line_start - route_line) < 5:
                        route_node = node
                        break

            if route_node:
                # Find all case statements after this switch
                switch_end = route_match.end()
                case_content = content[switch_end:switch_end + 2000]  # Look ahead

                for case_match in self.PATTERNS["case_handler"].finditer(case_content):
                    action_name = case_match.group(1)
                    case_line = route_line + case_content[:case_match.start()].count("\n")

                    # Find handler for this action
                    handler_pattern = re.compile(
                        rf"handle{action_name}|{action_name}Handler|do{action_name}",
                        re.IGNORECASE
                    )

                    for node in self.graph.nodes.values():
                        if node.node_type == NodeType.HANDLER:
                            if handler_pattern.search(node.name):
                                edge = GraphEdge(
                                    source_id=route_node.id,
                                    target_id=node.id,
                                    edge_type=EdgeType.DISPATCHES,
                                    evidence_locations=[SourceLocation(rel_path, case_line, case_line)],
                                )
                                self.graph.add_edge(edge)

    def _detect_no_op_patterns(self, file_path: Path) -> None:
        """
        Detect no-op patterns specific to PHP game servers.
        """
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)

        # Find handlers that return success without database writes
        for node in list(self.graph.nodes.values()):
            if node.node_type == NodeType.HANDLER:
                if node.metadata.get("is_fake_success"):
                    # Add a "fake_success" edge to a phantom node
                    phantom_id = self._generate_node_id("fake_success")
                    phantom_node = GraphNode(
                        id=phantom_id,
                        node_type=NodeType.STATE,
                        name="FAKE_SUCCESS",
                        location=node.location,
                        language="php",
                        metadata={
                            "is_phantom": True,
                            "issue_type": "fake_success_return",
                            "severity": "CRITICAL",
                        },
                    )
                    self.graph.add_node(phantom_node)

                    edge = GraphEdge(
                        source_id=node.id,
                        target_id=phantom_id,
                        edge_type=EdgeType.MUTATES,
                        evidence_locations=[node.location],
                        metadata={"is_fake": True},
                    )
                    self.graph.add_edge(edge)

    def _is_entry_point(self, file_path: Path, content: str) -> bool:
        """Determine if a file is an entry point."""
        name = file_path.name.lower()

        # Common entry points
        if name in {"index.php", "main.php", "ajax.php", "api.php", "cron.php"}:
            return True

        # Has direct execution check
        if self.PATTERNS["entry_point"].search(content):
            return True

        # Has CLI check (cron entry)
        if self.PATTERNS["cli_check"].search(content):
            return True

        # AJAX handler files
        if "ajax" in name or "handler" in name:
            return True

        return False

    def _get_file_type(self, file_path: Path, content: str) -> str:
        """Determine the type of file."""
        name = file_path.name.lower()

        if "ajax" in name:
            return "ajax_handler"
        if "cron" in name:
            return "cron_job"
        if "api" in name:
            return "api_endpoint"
        if "class" in name or self.PATTERNS["class_def"].search(content):
            return "class_file"
        if "config" in name:
            return "config"
        if "include" in str(file_path) or "inc" in name:
            return "include"

        return "module"

    def _extract_function_body(self, content: str, start_pos: int) -> str:
        """Extract the body of a function starting from a position."""
        brace_count = 0
        in_body = False
        body_start = start_pos
        body_end = start_pos

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

    def _is_empty_function(self, body: str) -> bool:
        """Check if a function body is empty or essentially empty."""
        # Remove comments
        cleaned = re.sub(r"//.*$", "", body, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"#.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s+", "", cleaned)

        # Check if only braces remain
        return cleaned in {"{}", "{;}", "{return;}", "{return}", "{returntrue;}", "{returnfalse;}"}

    def _is_debug_only_function(self, body: str) -> bool:
        """Check if a function only contains debug statements."""
        # Remove debug statements
        cleaned = re.sub(r"(?:echo|print|print_r|var_dump|error_log)\s*\([^)]*\)\s*;?", "", body)
        cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\s+", "", cleaned)

        return cleaned in {"{}", "{;}", "{return;}", "{return}"}

    def _has_database_write(self, body: str) -> bool:
        """Check if a function body has database write operations."""
        write_patterns = [
            r"INSERT\s+INTO",
            r"UPDATE\s+\w+\s+SET",
            r"DELETE\s+FROM",
            r"REPLACE\s+INTO",
            r"->(?:insert|update|delete|save|persist)\s*\(",
        ]

        for pattern in write_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return True

        return False

    def _has_success_return(self, body: str) -> bool:
        """Check if a function returns success."""
        success_patterns = [
            r"json_encode\s*\(\s*\[\s*['\"]success['\"]\s*=>\s*true",
            r"['\"]success['\"]\s*=>\s*true",
            r"return\s+true\s*;",
            r"['\"]status['\"]\s*=>\s*['\"]?success",
        ]

        for pattern in success_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return True

        return False

    def _find_node_by_name(self, name: str, node_type: Optional[NodeType] = None) -> Optional[GraphNode]:
        """Find a node by name and optionally type."""
        for node in self.graph.nodes.values():
            if node.name == name:
                if node_type is None or node.node_type == node_type:
                    return node
        return None

    def _find_entry_for_file(self, file_path: str) -> Optional[GraphNode]:
        """Find the entry point node for a file."""
        for node in self.graph.nodes.values():
            if node.node_type == NodeType.ENTRY_POINT:
                if file_path in node.location.file_path:
                    return node
        return None

    def _find_function_at_location(self, file_path: str, line: int) -> Optional[GraphNode]:
        """Find the function/method that contains a given line."""
        candidates = []
        for node in self.graph.nodes.values():
            if node.node_type in {NodeType.FUNCTION, NodeType.METHOD, NodeType.HANDLER}:
                if node.location.file_path == file_path:
                    if node.location.line_start <= line <= node.location.line_end + 50:
                        candidates.append(node)

        if candidates:
            return min(candidates, key=lambda n: abs(n.location.line_start - line))
        return None

    def _get_builtin_functions(self) -> Set[str]:
        """Return set of PHP built-in functions to ignore."""
        return {
            # Common functions
            "echo", "print", "printf", "sprintf", "var_dump", "print_r",
            "isset", "empty", "unset", "is_null", "is_array", "is_string", "is_int",
            "array", "list", "count", "sizeof", "strlen", "substr", "strpos",
            "explode", "implode", "join", "trim", "ltrim", "rtrim",
            "strtolower", "strtoupper", "ucfirst", "ucwords",
            "array_merge", "array_push", "array_pop", "array_shift", "array_unshift",
            "array_keys", "array_values", "array_map", "array_filter", "array_reduce",
            "in_array", "array_search", "array_key_exists",
            "json_encode", "json_decode",
            "file_get_contents", "file_put_contents", "file_exists", "is_file", "is_dir",
            "include", "include_once", "require", "require_once",
            "die", "exit", "return",
            "date", "time", "strtotime", "mktime",
            "rand", "mt_rand", "abs", "floor", "ceil", "round", "max", "min",
            "preg_match", "preg_replace", "preg_split",
            "header", "setcookie", "session_start",
            "mysqli_query", "mysqli_fetch_assoc", "mysqli_num_rows",
            "htmlspecialchars", "htmlentities", "strip_tags",
            "md5", "sha1", "hash", "password_hash", "password_verify",
            "base64_encode", "base64_decode", "urlencode", "urldecode",
            "intval", "floatval", "strval", "boolval",
            "define", "defined", "constant",
            "class_exists", "method_exists", "function_exists",
            "get_class", "get_parent_class", "instanceof",
            "throw", "try", "catch", "finally",
            "error_log", "trigger_error", "set_error_handler",
            "basename", "dirname", "pathinfo", "realpath",
            "php_sapi_name", "phpversion", "phpinfo",
        }


def build_php_graph(path: Path) -> ReachabilityGraph:
    """
    Convenience function to build a graph from PHP files.
    """
    builder = PHPGraphBuilder()
    if path.is_file():
        return builder.build_from_file(path)
    else:
        return builder.build_from_directory(path)
