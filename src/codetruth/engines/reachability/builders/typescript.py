"""
TypeScript/React Graph Builder

Parses TypeScript and React code to build reachability graphs.
Handles components, handlers, hooks, and imports.
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


class TypeScriptGraphBuilder:
    """
    Builds a reachability graph from TypeScript/React source files.
    """

    # Patterns for detecting various constructs
    PATTERNS = {
        # Function/handler definitions
        "function_def": re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
            re.MULTILINE
        ),
        "arrow_function": re.compile(
            r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?::\s*\w+)?\s*=>",
            re.MULTILINE
        ),
        "method_def": re.compile(
            r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{",
            re.MULTILINE
        ),

        # React components
        "react_component": re.compile(
            r"(?:export\s+)?(?:default\s+)?(?:function|const)\s+([A-Z]\w+)\s*[:=\(]",
            re.MULTILINE
        ),

        # Handler definitions (onClick, onChange, etc.)
        "handler_def": re.compile(
            r"(?:const|let|var)\s+(handle\w+|on\w+)\s*=",
            re.MULTILINE
        ),

        # Handler bindings in JSX
        "handler_binding": re.compile(
            r"(?:onClick|onChange|onSubmit|onBlur|onFocus|onKeyDown|onKeyUp|onMouseOver|onMouseOut)\s*=\s*\{?\s*(\w+)",
            re.MULTILINE
        ),

        # Imports
        "import_from": re.compile(
            r"import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),
        "import_default": re.compile(
            r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE
        ),

        # Exports
        "export_named": re.compile(
            r"export\s+(?:const|function|class|interface|type)\s+(\w+)",
            re.MULTILINE
        ),
        "export_default": re.compile(
            r"export\s+default\s+(\w+)",
            re.MULTILINE
        ),

        # Function calls
        "function_call": re.compile(
            r"(?<![.\w])(\w+)\s*\(",
            re.MULTILINE
        ),

        # React hooks
        "use_hook": re.compile(
            r"(use\w+)\s*\(",
            re.MULTILINE
        ),

        # JSX component usage
        "jsx_component": re.compile(
            r"<([A-Z]\w+)",
            re.MULTILINE
        ),

        # Route definitions (React Router, Next.js)
        "route_def": re.compile(
            r"(?:path|route)\s*[:=]\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE | re.IGNORECASE
        ),

        # API routes (Next.js)
        "api_export": re.compile(
            r"export\s+(?:default\s+)?(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|handler)",
            re.MULTILINE
        ),

        # useEffect dependencies
        "use_effect": re.compile(
            r"useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*\}\s*,\s*\[([^\]]*)\]",
            re.MULTILINE | re.DOTALL
        ),

        # Event listeners
        "add_event_listener": re.compile(
            r"addEventListener\s*\(\s*['\"](\w+)['\"]\s*,\s*(\w+)",
            re.MULTILINE
        ),
    }

    def __init__(self):
        self.graph = ReachabilityGraph()
        self._node_counter = 0

    def _generate_node_id(self, prefix: str) -> str:
        self._node_counter += 1
        return f"{prefix}_{self._node_counter:06d}"

    def build_from_directory(self, directory: Path) -> ReachabilityGraph:
        """
        Build a reachability graph from all TypeScript files in a directory.
        """
        self.graph = ReachabilityGraph()
        self.graph.repo_path = str(directory)
        self.graph.language_versions["typescript"] = "5.x"

        # Find all TypeScript/React files
        patterns = ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
        files: List[Path] = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))

        # Exclude node_modules and other common excludes
        files = [f for f in files if "node_modules" not in str(f) and ".next" not in str(f)]

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
        self.graph.language_versions["typescript"] = "5.x"

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

        # Detect entry points
        if self._is_entry_point(file_path, content):
            entry_node = GraphNode(
                id=self._generate_node_id("entry"),
                node_type=NodeType.ENTRY_POINT,
                name=file_path.name,
                location=SourceLocation(rel_path, 1, len(lines)),
                language="typescript",
                metadata={"file_type": self._get_file_type(file_path, content)},
            )
            self.graph.add_node(entry_node)

        # Find React components
        for match in self.PATTERNS["react_component"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            node = GraphNode(
                id=self._generate_node_id("component"),
                node_type=NodeType.COMPONENT,
                name=match.group(1),
                location=SourceLocation(rel_path, line_num, line_num + 10),
                language="typescript",
                metadata={"component_name": match.group(1)},
            )
            self.graph.add_node(node)

        # Find handler definitions
        for match in self.PATTERNS["handler_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            handler_name = match.group(1)

            # Check if handler is empty or debug-only
            handler_body = self._extract_function_body(content, match.end())
            is_empty = self._is_empty_handler(handler_body)
            is_debug_only = self._is_debug_only_handler(handler_body)

            node = GraphNode(
                id=self._generate_node_id("handler"),
                node_type=NodeType.HANDLER,
                name=handler_name,
                location=SourceLocation(rel_path, line_num, line_num + 5),
                language="typescript",
                metadata={
                    "handler_name": handler_name,
                    "is_empty": is_empty,
                    "is_debug_only": is_debug_only,
                },
            )
            self.graph.add_node(node)

        # Find function definitions
        for match in self.PATTERNS["function_def"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            func_name = match.group(1)
            # Skip if already added as handler
            if not func_name.startswith("handle") and not func_name.startswith("on"):
                node = GraphNode(
                    id=self._generate_node_id("function"),
                    node_type=NodeType.FUNCTION,
                    name=func_name,
                    location=SourceLocation(rel_path, line_num, line_num + 10),
                    language="typescript",
                )
                self.graph.add_node(node)

        # Find arrow functions
        for match in self.PATTERNS["arrow_function"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            func_name = match.group(1)
            # Skip handlers (already captured) and components (already captured)
            if not func_name.startswith("handle") and not func_name.startswith("on") and not func_name[0].isupper():
                node = GraphNode(
                    id=self._generate_node_id("function"),
                    node_type=NodeType.FUNCTION,
                    name=func_name,
                    location=SourceLocation(rel_path, line_num, line_num + 5),
                    language="typescript",
                )
                self.graph.add_node(node)

        # Find API routes (Next.js style)
        for match in self.PATTERNS["api_export"].finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            method = match.group(1)
            node = GraphNode(
                id=self._generate_node_id("route"),
                node_type=NodeType.ROUTE,
                name=f"{method} {file_path.stem}",
                location=SourceLocation(rel_path, line_num, line_num + 10),
                language="typescript",
                metadata={"http_method": method, "is_api_route": True},
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

        # Find handler bindings (onClick={handleXxx})
        for match in self.PATTERNS["handler_binding"].finditer(content):
            handler_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Find the handler node
            handler_node = self._find_node_by_name(handler_name, NodeType.HANDLER)
            if handler_node:
                # Find the component containing this binding
                component_node = self._find_component_at_location(rel_path, line_num)
                if component_node:
                    edge = GraphEdge(
                        source_id=component_node.id,
                        target_id=handler_node.id,
                        edge_type=EdgeType.BINDS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find function calls
        for match in self.PATTERNS["function_call"].finditer(content):
            func_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Skip built-in functions and hooks
            if func_name in {"console", "setTimeout", "setInterval", "fetch", "Promise", "JSON", "Array", "Object", "Math"}:
                continue

            # Find target node
            target_node = self._find_node_by_name(func_name, NodeType.FUNCTION)
            if not target_node:
                target_node = self._find_node_by_name(func_name, NodeType.HANDLER)

            if target_node:
                # Find source node (function/handler containing this call)
                source_node = self._find_function_at_location(rel_path, line_num)
                if source_node and source_node.id != target_node.id:
                    edge = GraphEdge(
                        source_id=source_node.id,
                        target_id=target_node.id,
                        edge_type=EdgeType.CALLS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

        # Find JSX component usage
        for match in self.PATTERNS["jsx_component"].finditer(content):
            component_name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1

            # Find the component node
            target_node = self._find_node_by_name(component_name, NodeType.COMPONENT)
            if target_node:
                # Find the parent component
                parent_node = self._find_component_at_location(rel_path, line_num)
                if parent_node and parent_node.id != target_node.id:
                    edge = GraphEdge(
                        source_id=parent_node.id,
                        target_id=target_node.id,
                        edge_type=EdgeType.RENDERS,
                        evidence_locations=[SourceLocation(rel_path, line_num, line_num)],
                    )
                    self.graph.add_edge(edge)

    def _is_entry_point(self, file_path: Path, content: str) -> bool:
        """Determine if a file is an entry point."""
        name = file_path.name.lower()
        # Common entry points
        if name in {"index.ts", "index.tsx", "index.js", "index.jsx", "main.ts", "main.tsx", "app.ts", "app.tsx"}:
            return True
        # Next.js pages
        if "pages/" in str(file_path) or "app/" in str(file_path):
            return True
        # Has default export that looks like a page/app
        if re.search(r"export\s+default", content):
            return True
        return False

    def _get_file_type(self, file_path: Path, content: str) -> str:
        """Determine the type of file."""
        if "pages/api" in str(file_path) or "app/api" in str(file_path):
            return "api_route"
        if "pages/" in str(file_path) or "app/" in str(file_path):
            return "page"
        if re.search(r"<[A-Z]", content):
            return "component"
        return "module"

    def _extract_function_body(self, content: str, start_pos: int) -> str:
        """Extract the body of a function starting from a position."""
        # Simple brace matching
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

    def _is_empty_handler(self, body: str) -> bool:
        """Check if a handler body is empty or essentially empty."""
        # Remove comments and whitespace
        cleaned = re.sub(r"//.*$", "", body, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\s+", "", cleaned)
        # Check if only braces remain
        return cleaned in {"{}", "{;}", "{return;}", "{return}", "{returnundefined;}", "{returnundefined}"}

    def _is_debug_only_handler(self, body: str) -> bool:
        """Check if a handler only contains debug statements."""
        # Remove console.log, console.debug, etc.
        cleaned = re.sub(r"console\.\w+\([^)]*\);?", "", body)
        cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s+", "", cleaned)
        return cleaned in {"{}", "{;}", "{return;}", "{return}"}

    def _find_node_by_name(self, name: str, node_type: Optional[NodeType] = None) -> Optional[GraphNode]:
        """Find a node by name and optionally type."""
        for node in self.graph.nodes.values():
            if node.name == name:
                if node_type is None or node.node_type == node_type:
                    return node
        return None

    def _find_component_at_location(self, file_path: str, line: int) -> Optional[GraphNode]:
        """Find the component that contains a given line."""
        candidates = []
        for node in self.graph.nodes.values():
            if node.node_type == NodeType.COMPONENT:
                if node.location.file_path == file_path:
                    if node.location.line_start <= line <= node.location.line_end + 100:
                        candidates.append(node)
        # Return the closest one
        if candidates:
            return min(candidates, key=lambda n: abs(n.location.line_start - line))
        return None

    def _find_function_at_location(self, file_path: str, line: int) -> Optional[GraphNode]:
        """Find the function/handler that contains a given line."""
        candidates = []
        for node in self.graph.nodes.values():
            if node.node_type in {NodeType.FUNCTION, NodeType.HANDLER, NodeType.COMPONENT}:
                if node.location.file_path == file_path:
                    if node.location.line_start <= line <= node.location.line_end + 50:
                        candidates.append(node)
        if candidates:
            return min(candidates, key=lambda n: abs(n.location.line_start - line))
        return None


def build_typescript_graph(path: Path) -> ReachabilityGraph:
    """
    Convenience function to build a graph from TypeScript files.
    """
    builder = TypeScriptGraphBuilder()
    if path.is_file():
        return builder.build_from_file(path)
    else:
        return builder.build_from_directory(path)
