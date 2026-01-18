"""
Python Graph Builder

Parses Python code to build reachability graphs.
Handles classes, methods, functions, decorators, and async patterns.

Designed for bot/automation codebases and web frameworks.
"""

from __future__ import annotations

import ast
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


class PythonGraphBuilder:
    """
    Builds a reachability graph from Python source files.

    Uses AST parsing for accurate analysis, with regex fallback.
    Handles:
    - Functions and async functions
    - Classes and methods
    - Decorators (@route, @command, @scheduled, etc.)
    - Import chains
    - Framework-specific patterns (Flask, FastAPI, Discord.py, etc.)
    """

    # Regex patterns for fallback when AST fails
    PATTERNS = {
        # Class definitions
        "class_def": re.compile(
            r"^class\s+(\w+)(?:\s*\([^)]*\))?\s*:",
            re.MULTILINE
        ),

        # Function definitions
        "function_def": re.compile(
            r"^(?:async\s+)?def\s+(\w+)\s*\(",
            re.MULTILINE
        ),

        # Method definitions (indented)
        "method_def": re.compile(
            r"^\s+(?:async\s+)?def\s+(\w+)\s*\(",
            re.MULTILINE
        ),

        # Decorator patterns
        "decorator": re.compile(
            r"^@(\w+(?:\.\w+)?)\s*(?:\([^)]*\))?",
            re.MULTILINE
        ),

        # Import statements
        "import": re.compile(
            r"^import\s+([\w.]+)",
            re.MULTILINE
        ),
        "from_import": re.compile(
            r"^from\s+([\w.]+)\s+import\s+(.+)",
            re.MULTILINE
        ),

        # Function calls
        "function_call": re.compile(
            r"(?<![.\w])(\w+)\s*\(",
            re.MULTILINE
        ),

        # Method calls
        "method_call": re.compile(
            r"(\w+)\.(\w+)\s*\(",
            re.MULTILINE
        ),

        # Async patterns
        "await_call": re.compile(
            r"await\s+(\w+(?:\.\w+)?)\s*\(",
            re.MULTILINE
        ),

        # Database operations (SQLAlchemy, raw SQL)
        "sql_query": re.compile(
            r"(?:execute|query|filter|filter_by)\s*\(.*?(?:SELECT|INSERT|UPDATE|DELETE)",
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        ),

        # HTTP requests
        "http_request": re.compile(
            r"(?:requests|httpx|aiohttp)\.\s*(get|post|put|delete|patch)\s*\(",
            re.MULTILINE | re.IGNORECASE
        ),
    }

    # Framework-specific patterns
    FRAMEWORK_PATTERNS = {
        # Flask routes
        "flask_route": re.compile(
            r"@(?:app|blueprint|bp)\.route\s*\(\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),

        # FastAPI routes
        "fastapi_route": re.compile(
            r"@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),

        # Discord.py commands
        "discord_command": re.compile(
            r"@(?:commands?|bot)\.\s*(?:command|slash_command|group)\s*\((?:[^)]*name\s*=\s*)?['\"]?(\w+)?",
            re.MULTILINE
        ),

        # Discord.py events
        "discord_event": re.compile(
            r"@(?:client|bot)\.\s*event\s*\n\s*async\s+def\s+(on_\w+)",
            re.MULTILINE
        ),

        # Celery tasks
        "celery_task": re.compile(
            r"@(?:app|celery)\.\s*task\s*(?:\([^)]*\))?\s*\n\s*def\s+(\w+)",
            re.MULTILINE
        ),

        # Scheduled tasks (APScheduler, etc.)
        "scheduled_task": re.compile(
            r"@(?:scheduler|cron|schedule)\.\s*(?:scheduled_job|job|cron)\s*\([^)]*\)\s*\n\s*(?:async\s+)?def\s+(\w+)",
            re.MULTILINE
        ),

        # Click CLI commands
        "click_command": re.compile(
            r"@(?:click\.)?\s*(?:command|group)\s*\((?:[^)]*name\s*=\s*)?['\"]?(\w+)?",
            re.MULTILINE
        ),

        # Django views
        "django_view": re.compile(
            r"def\s+(\w+)\s*\(\s*request\s*(?:,|\))",
            re.MULTILINE
        ),

        # Django class-based views
        "django_cbv": re.compile(
            r"class\s+(\w+View)\s*\(",
            re.MULTILINE
        ),

        # Pytest fixtures
        "pytest_fixture": re.compile(
            r"@pytest\.fixture\s*(?:\([^)]*\))?\s*\n\s*def\s+(\w+)",
            re.MULTILINE
        ),
    }

    def __init__(self):
        self.graph = ReachabilityGraph()
        self._node_counter = 0
        self._module_map: Dict[str, str] = {}  # module_name -> node_id
        self._class_map: Dict[str, str] = {}  # class_name -> node_id
        self._function_map: Dict[str, str] = {}  # function_name -> node_id
        self._current_module = ""
        self._current_class = ""

    def _generate_node_id(self, prefix: str) -> str:
        self._node_counter += 1
        return f"{prefix}_{self._node_counter:06d}"

    def build_from_directory(self, directory: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from all Python files in a directory.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(directory)
        self.graph.language_versions["python"] = "3.11"

        # Find all Python files
        files = list(directory.glob("**/*.py"))

        # Exclude virtual environments and common excludes
        files = [
            f for f in files
            if "venv" not in str(f)
            and ".venv" not in str(f)
            and "env" not in str(f).split("/")
            and "site-packages" not in str(f)
            and "__pycache__" not in str(f)
            and ".git" not in str(f)
            and "node_modules" not in str(f)
        ]

        # First pass: collect all definitions
        for file_path in files:
            self._analyze_file(file_path)

        # Second pass: resolve references and build edges
        for file_path in files:
            self._resolve_references(file_path)

        return self.graph

    def build_from_file(self, file_path: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from a single file.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(file_path.parent)
        self.graph.language_versions["python"] = "3.11"

        self._analyze_file(file_path)
        self._resolve_references(file_path)

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
        self._current_module = file_path.stem

        # Try AST parsing first
        try:
            tree = ast.parse(content, filename=str(file_path))
            self._analyze_ast(tree, rel_path, content)
        except SyntaxError:
            # Fall back to regex parsing
            self._analyze_regex(content, rel_path)

        # Detect entry points
        if self._is_entry_point(file_path, content):
            entry_node = GraphNode(
                id=self._generate_node_id("entry"),
                node_type=NodeType.ENTRY_POINT,
                name=file_path.name,
                location=SourceLocation(rel_path, 1, len(lines)),
                language="python",
                metadata={"file_type": self._get_file_type(file_path, content)},
            )
            self.graph.add_node(entry_node)

        # Detect framework-specific patterns
        self._analyze_frameworks(content, rel_path)

    def _analyze_ast(self, tree: ast.AST, file_path: str, content: str) -> None:
        """
        Analyze using Python's AST.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._process_class_def(node, file_path, content)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function_def(node, file_path, content)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self._module_map[alias.asname or alias.name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        self._module_map[alias.asname or alias.name] = node.module

    def _process_class_def(self, node: ast.ClassDef, file_path: str, content: str) -> None:
        """Process a class definition."""
        self._current_class = node.name

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Determine class type
        bases = [self._get_name(b) for b in node.bases]

        graph_node = GraphNode(
            id=self._generate_node_id("class"),
            node_type=NodeType.CLASS,
            name=node.name,
            location=SourceLocation(
                file_path,
                node.lineno,
                node.end_lineno or node.lineno + 20
            ),
            language="python",
            metadata={
                "decorators": decorators,
                "bases": bases,
                "is_dataclass": "dataclass" in decorators,
            },
        )
        self.graph.add_node(graph_node)
        self._class_map[node.name] = graph_node.id

        # Process methods within the class
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_method_def(item, node.name, file_path, content)

    def _process_function_def(self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str, content: str) -> None:
        """Process a function definition."""
        # Skip if already processed as a method
        if self._current_class:
            return

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Determine function type
        is_async = isinstance(node, ast.AsyncFunctionDef)
        is_handler = node.name.startswith("handle") or node.name.startswith("on_")
        is_route = any(d in ["route", "get", "post", "put", "delete", "patch"] for d in decorators)

        # Get function body to check for no-op
        body_lines = content.split("\n")[node.lineno - 1:node.end_lineno or node.lineno]
        body_text = "\n".join(body_lines)
        is_empty = self._is_empty_function(node)
        is_debug_only = self._is_debug_only_function(node, content)

        node_type = NodeType.HANDLER if is_handler or is_route else NodeType.FUNCTION

        graph_node = GraphNode(
            id=self._generate_node_id("function"),
            node_type=node_type,
            name=node.name,
            location=SourceLocation(
                file_path,
                node.lineno,
                node.end_lineno or node.lineno + 10
            ),
            language="python",
            metadata={
                "decorators": decorators,
                "is_async": is_async,
                "is_handler": is_handler,
                "is_empty": is_empty,
                "is_debug_only": is_debug_only,
                "arg_count": len(node.args.args),
            },
        )
        self.graph.add_node(graph_node)
        self._function_map[node.name] = graph_node.id

    def _process_method_def(self, node: ast.FunctionDef | ast.AsyncFunctionDef, class_name: str, file_path: str, content: str) -> None:
        """Process a method definition within a class."""
        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        is_async = isinstance(node, ast.AsyncFunctionDef)
        is_static = "staticmethod" in decorators
        is_classmethod = "classmethod" in decorators
        is_property = "property" in decorators
        is_empty = self._is_empty_function(node)
        is_debug_only = self._is_debug_only_function(node, content)

        # Special method detection
        is_dunder = node.name.startswith("__") and node.name.endswith("__")
        is_handler = node.name.startswith("handle") or node.name.startswith("on_")

        node_type = NodeType.HANDLER if is_handler else NodeType.METHOD

        graph_node = GraphNode(
            id=self._generate_node_id("method"),
            node_type=node_type,
            name=node.name,
            location=SourceLocation(
                file_path,
                node.lineno,
                node.end_lineno or node.lineno + 10
            ),
            language="python",
            metadata={
                "class": class_name,
                "decorators": decorators,
                "is_async": is_async,
                "is_static": is_static,
                "is_classmethod": is_classmethod,
                "is_property": is_property,
                "is_dunder": is_dunder,
                "is_empty": is_empty,
                "is_debug_only": is_debug_only,
            },
        )
        self.graph.add_node(graph_node)

        full_name = f"{class_name}.{node.name}"
        self._function_map[full_name] = graph_node.id
        self._function_map[node.name] = graph_node.id  # Also index by short name

    def _analyze_regex(self, content: str, file_path: str) -> None:
        """
        Fallback regex-based analysis when AST fails.
        """
        # Find class definitions
        for match in self.PATTERNS["class_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            class_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("class"),
                node_type=NodeType.CLASS,
                name=class_name,
                location=SourceLocation(file_path, line_num, line_num + 30),
                language="python",
            )
            self.graph.add_node(node)
            self._class_map[class_name] = node.id

        # Find function definitions
        for match in self.PATTERNS["function_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            func_name = match.group(1)

            is_handler = func_name.startswith("handle") or func_name.startswith("on_")
            node_type = NodeType.HANDLER if is_handler else NodeType.FUNCTION

            node = GraphNode(
                id=self._generate_node_id("function"),
                node_type=node_type,
                name=func_name,
                location=SourceLocation(file_path, line_num, line_num + 15),
                language="python",
            )
            self.graph.add_node(node)
            self._function_map[func_name] = node.id

    def _analyze_frameworks(self, content: str, file_path: str) -> None:
        """
        Detect framework-specific patterns.
        """
        # Flask routes
        for match in self.FRAMEWORK_PATTERNS["flask_route"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            route_path = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("route"),
                node_type=NodeType.ROUTE,
                name=route_path,
                location=SourceLocation(file_path, line_num, line_num),
                language="python",
                metadata={"framework": "flask", "path": route_path},
            )
            self.graph.add_node(node)

        # FastAPI routes
        for match in self.FRAMEWORK_PATTERNS["fastapi_route"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            method = match.group(1)
            route_path = match.group(2)

            node = GraphNode(
                id=self._generate_node_id("route"),
                node_type=NodeType.ROUTE,
                name=f"{method.upper()} {route_path}",
                location=SourceLocation(file_path, line_num, line_num),
                language="python",
                metadata={"framework": "fastapi", "method": method, "path": route_path},
            )
            self.graph.add_node(node)

        # Discord.py commands
        for match in self.FRAMEWORK_PATTERNS["discord_command"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            command_name = match.group(1) or "command"

            node = GraphNode(
                id=self._generate_node_id("command"),
                node_type=NodeType.HANDLER,
                name=f"!{command_name}",
                location=SourceLocation(file_path, line_num, line_num + 10),
                language="python",
                metadata={"framework": "discord.py", "command": command_name},
            )
            self.graph.add_node(node)

        # Discord.py events
        for match in self.FRAMEWORK_PATTERNS["discord_event"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            event_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("event"),
                node_type=NodeType.HANDLER,
                name=event_name,
                location=SourceLocation(file_path, line_num, line_num + 10),
                language="python",
                metadata={"framework": "discord.py", "event": event_name},
            )
            self.graph.add_node(node)

        # Celery tasks
        for match in self.FRAMEWORK_PATTERNS["celery_task"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            task_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("task"),
                node_type=NodeType.SCHEDULED_TASK,
                name=task_name,
                location=SourceLocation(file_path, line_num, line_num + 10),
                language="python",
                metadata={"framework": "celery", "task": task_name},
            )
            self.graph.add_node(node)

        # Scheduled tasks
        for match in self.FRAMEWORK_PATTERNS["scheduled_task"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            task_name = match.group(1)

            node = GraphNode(
                id=self._generate_node_id("scheduled"),
                node_type=NodeType.SCHEDULED_TASK,
                name=task_name,
                location=SourceLocation(file_path, line_num, line_num + 10),
                language="python",
                metadata={"is_scheduled": True},
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

        # Try AST parsing for accurate call detection
        try:
            tree = ast.parse(content, filename=str(file_path))
            self._resolve_ast_references(tree, rel_path)
        except SyntaxError:
            # Fall back to regex
            self._resolve_regex_references(content, rel_path)

    def _resolve_ast_references(self, tree: ast.AST, file_path: str) -> None:
        """Resolve references using AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name and call_name in self._function_map:
                    target_id = self._function_map[call_name]

                    # Find source function
                    source_node = self._find_function_containing_line(file_path, node.lineno)
                    if source_node and source_node.id != target_id:
                        edge = GraphEdge(
                            source_id=source_node.id,
                            target_id=target_id,
                            edge_type=EdgeType.CALLS,
                            evidence_locations=[SourceLocation(file_path, node.lineno, node.lineno)],
                        )
                        self.graph.add_edge(edge)

            elif isinstance(node, ast.Attribute):
                # Method call on object
                if isinstance(node.ctx, ast.Load):
                    method_name = node.attr
                    if method_name in self._function_map:
                        target_id = self._function_map[method_name]
                        source_node = self._find_function_containing_line(file_path, node.lineno)
                        if source_node and source_node.id != target_id:
                            edge = GraphEdge(
                                source_id=source_node.id,
                                target_id=target_id,
                                edge_type=EdgeType.CALLS,
                                evidence_locations=[SourceLocation(file_path, node.lineno, node.lineno)],
                            )
                            self.graph.add_edge(edge)

    def _resolve_regex_references(self, content: str, file_path: str) -> None:
        """Resolve references using regex fallback."""
        # Find function calls
        for match in self.PATTERNS["function_call"].finditer(content):
            func_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Skip built-in functions
            if func_name in self._get_builtin_functions():
                continue

            if func_name in self._function_map:
                target_id = self._function_map[func_name]
                source_node = self._find_function_containing_line(file_path, line_num)
                if source_node and source_node.id != target_id:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(file_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find method calls
        for match in self.PATTERNS["method_call"].finditer(content):
            obj_name = match.group(1)
            method_name = match.group(2)
            line_num = content[:match.start()].count("\n") + 1

            # Skip common objects
            if obj_name in {"self", "cls", "super", "print", "log", "logger"}:
                continue

            full_name = f"{obj_name}.{method_name}"
            if full_name in self._function_map:
                target_id = self._function_map[full_name]
                source_node = self._find_function_containing_line(file_path, line_num)
                if source_node and source_node.id != target_id:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(file_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

    def _is_entry_point(self, file_path: Path, content: str) -> bool:
        """Determine if a file is an entry point."""
        # Has if __name__ == "__main__"
        if re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", content):
            return True

        # Common entry points
        name = file_path.stem.lower()
        if name in {"main", "app", "run", "server", "bot", "cli", "manage", "__main__"}:
            return True

        # Has @click.command or similar
        if "@click.command" in content or "@app.command" in content:
            return True

        # Flask/FastAPI app
        if "app = Flask" in content or "app = FastAPI" in content:
            return True

        return False

    def _get_file_type(self, file_path: Path, content: str) -> str:
        """Determine the type of file."""
        name = file_path.stem.lower()

        if "test" in name:
            return "test"
        if "conftest" in name:
            return "pytest_config"
        if name in {"setup", "settings", "config"}:
            return "config"
        if "model" in name:
            return "model"
        if "view" in name:
            return "view"
        if "route" in name or "api" in name:
            return "route"
        if "util" in name or "helper" in name:
            return "utility"
        if "command" in name or "bot" in name:
            return "bot"

        return "module"

    def _is_empty_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if a function body is empty."""
        if len(node.body) == 0:
            return True

        if len(node.body) == 1:
            stmt = node.body[0]
            # Only pass
            if isinstance(stmt, ast.Pass):
                return True
            # Only docstring
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                return True
            # Only ellipsis (...)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
                return True

        return False

    def _is_debug_only_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, content: str) -> bool:
        """Check if a function only contains debug statements."""
        if self._is_empty_function(node):
            return False

        for stmt in node.body:
            # Skip docstrings
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                continue

            # Check if it's a print/logging call
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                call_name = self._get_call_name(call)
                if call_name not in {"print", "log", "logging.debug", "logging.info", "logger.debug", "logger.info"}:
                    return False
            else:
                # Non-print statement found
                return False

        return True

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get the name of a decorator."""
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

    def _get_name(self, node: ast.expr) -> str:
        """Get the name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""

    def _get_call_name(self, node: ast.Call) -> str:
        """Get the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _find_function_containing_line(self, file_path: str, line: int) -> Optional[GraphNode]:
        """Find the function that contains a given line."""
        candidates = []
        for node in self.graph.nodes.values():
            if node.node_type in {NodeType.FUNCTION, NodeType.METHOD, NodeType.HANDLER}:
                if node.location.file_path == file_path:
                    if node.location.line_start <= line <= node.location.line_end + 20:
                        candidates.append(node)

        if candidates:
            return min(candidates, key=lambda n: abs(n.location.line_start - line))
        return None

    def _get_builtin_functions(self) -> Set[str]:
        """Return set of Python built-in functions to ignore."""
        return {
            # Built-ins
            "print", "len", "range", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
            "open", "input", "type", "isinstance", "issubclass", "hasattr", "getattr", "setattr",
            "sorted", "reversed", "enumerate", "zip", "map", "filter", "any", "all", "sum", "min", "max",
            "abs", "round", "pow", "divmod", "bin", "hex", "oct", "ord", "chr",
            "super", "property", "staticmethod", "classmethod",
            "next", "iter", "callable", "id", "hash", "repr", "format",
            "vars", "dir", "locals", "globals", "eval", "exec", "compile",
            "Exception", "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError",
            "RuntimeError", "StopIteration", "FileNotFoundError", "IOError", "OSError",
            # Common modules
            "join", "split", "strip", "replace", "format", "startswith", "endswith",
            "append", "extend", "insert", "remove", "pop", "clear", "copy",
            "keys", "values", "items", "get", "update", "setdefault",
            "add", "discard", "union", "intersection", "difference",
            # Async
            "async", "await", "asyncio",
        }


def build_python_graph(path: Path) -> ReachabilityGraph:
    """
    Convenience function to build a graph from Python files.
    """
    builder = PythonGraphBuilder()
    if path.is_file():
        return builder.build_from_file(path)
    else:
        return builder.build_from_directory(path)
