"""
Reachability Proof Engine - Graph Model

This module defines the core graph structure for reachability analysis.
Nodes represent code elements, edges represent relationships.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class NodeType(Enum):
    """Types of nodes in the reachability graph."""
    ENTRY_POINT = "entry_point"          # main(), index.ts, app.py
    UI_EVENT = "ui_event"                # onClick, onSubmit, onChange
    ROUTE = "route"                      # /api/users, /admin/*
    HANDLER = "handler"                  # Route handler, event handler
    FUNCTION = "function"                # Regular function/method
    METHOD = "method"                    # Class method
    CLASS = "class"                      # Class definition
    INTERFACE = "interface"              # Interface definition
    ENUM = "enum"                        # Enum definition
    SQL_QUERY = "sql_query"              # Database query
    PROCESS_SPAWN = "process_spawn"      # subprocess, exec, spawn
    FILE_WRITE = "file_write"            # File system writes
    NETWORK_CALL = "network_call"        # fetch, axios, http calls
    IMPORT = "import"                    # Module import
    EXPORT = "export"                    # Module export
    COMPONENT = "component"              # React/Vue component
    HOOK = "hook"                        # React hook (useState, useEffect)
    MIDDLEWARE = "middleware"            # Express/FastAPI middleware
    CRON_JOB = "cron_job"               # Scheduled task
    SCHEDULED_TASK = "scheduled_task"    # Scheduled/cron task
    MESSAGE_HANDLER = "message_handler"  # Queue/event listener
    PACKET_HANDLER = "packet_handler"    # Game server packet handler
    STATE = "state"                      # State node (for analysis markers)


class EdgeType(Enum):
    """Types of edges connecting nodes."""
    IMPORTS = "imports"           # import x from y
    INCLUDES = "includes"         # PHP include/require
    CALLS = "calls"               # function call
    DISPATCHES = "dispatches"     # event dispatch
    MOUNTS = "mounts"             # route mounting
    NAVIGATES = "navigates"       # client-side navigation
    FETCHES = "fetches"           # HTTP fetch/request
    SPAWNS = "spawns"             # process spawn
    WRITES = "writes"             # file write
    QUERIES = "queries"           # SQL query
    RENDERS = "renders"           # React render
    BINDS = "binds"               # Event binding
    REGISTERS = "registers"       # Handler registration
    INHERITS = "inherits"         # Class inheritance
    EXTENDS = "extends"           # Class extension
    IMPLEMENTS = "implements"     # Interface implementation
    INSTANTIATES = "instantiates" # Object creation
    MUTATES = "mutates"           # State mutation
    LISTENS = "listens"           # Event listener


@dataclass
class SourceLocation:
    """Location in source code."""
    file_path: str
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "column_start": self.column_start,
            "column_end": self.column_end,
        }

    def __hash__(self) -> int:
        return hash((self.file_path, self.line_start, self.column_start))


@dataclass
class GraphNode:
    """A node in the reachability graph."""
    id: str
    node_type: NodeType
    name: str
    location: SourceLocation
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "name": self.name,
            "location": self.location.to_dict(),
            "language": self.language,
            "metadata": self.metadata,
            "confidence": self.confidence,
        }

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GraphNode):
            return self.id == other.id
        return False


@dataclass
class GraphEdge:
    """An edge connecting two nodes."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_locations: List[SourceLocation] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.source_id}->{self.target_id}:{self.edge_type.value}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "evidence": [loc.to_dict() for loc in self.evidence_locations],
        }

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class ReachabilityGraph:
    """
    The complete reachability graph for a codebase.

    This graph tracks all code paths from entry points to effects.
    """
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: Dict[str, GraphEdge] = field(default_factory=dict)
    entry_points: Set[str] = field(default_factory=set)
    repo_path: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    language_versions: Dict[str, str] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.node_type == NodeType.ENTRY_POINT:
            self.entry_points.add(node.id)

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges[edge.id] = edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges originating from a node."""
        return [e for e in self.edges.values() if e.source_id == node_id]

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges pointing to a node."""
        return [e for e in self.edges.values() if e.target_id == node_id]

    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get all nodes directly connected to a node."""
        neighbors = set()
        for edge in self.edges.values():
            if edge.source_id == node_id:
                neighbors.add(edge.target_id)
            if edge.target_id == node_id:
                neighbors.add(edge.source_id)
        return neighbors

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 50
    ) -> List[List[str]]:
        """
        Find all paths from source to target node.

        Returns list of paths, where each path is a list of node IDs.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        paths: List[List[str]] = []
        visited: Set[str] = set()

        def dfs(current: str, path: List[str]) -> None:
            if len(path) > max_depth:
                return
            if current == target_id:
                paths.append(path.copy())
                return
            if current in visited:
                return

            visited.add(current)
            for edge in self.get_outgoing_edges(current):
                path.append(edge.target_id)
                dfs(edge.target_id, path)
                path.pop()
            visited.remove(current)

        dfs(source_id, [source_id])
        return paths

    def is_reachable(self, source_id: str, target_id: str) -> bool:
        """Check if target is reachable from source."""
        return len(self.find_paths(source_id, target_id, max_depth=100)) > 0

    def is_reachable_from_entry(self, node_id: str) -> bool:
        """Check if node is reachable from any entry point."""
        for entry in self.entry_points:
            if self.is_reachable(entry, node_id):
                return True
        return False

    def find_unreachable_nodes(self) -> List[GraphNode]:
        """Find all nodes not reachable from any entry point."""
        unreachable = []
        for node_id, node in self.nodes.items():
            if node.node_type != NodeType.ENTRY_POINT:
                if not self.is_reachable_from_entry(node_id):
                    unreachable.append(node)
        return unreachable

    def compute_hash(self) -> str:
        """Compute deterministic hash of graph state."""
        data = {
            "nodes": sorted([n.to_dict() for n in self.nodes.values()], key=lambda x: x["id"]),
            "edges": sorted([e.to_dict() for e in self.edges.values()], key=lambda x: x["id"]),
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Export graph to dictionary."""
        return {
            "version": "1.0.0",
            "repo_path": self.repo_path,
            "created_at": self.created_at.isoformat(),
            "hash": self.compute_hash(),
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "entry_points": len(self.entry_points),
                "node_types": self._count_node_types(),
                "edge_types": self._count_edge_types(),
            },
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "entry_points": list(self.entry_points),
            "language_versions": self.language_versions,
        }

    def _count_node_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for node in self.nodes.values():
            key = node.node_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_edge_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for edge in self.edges.values():
            key = edge.edge_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def export_json(self, output_path: Path) -> None:
        """Export graph to JSON file."""
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReachabilityGraph":
        """Load graph from dictionary."""
        graph = cls()
        graph.repo_path = data.get("repo_path", "")
        graph.language_versions = data.get("language_versions", {})

        for node_data in data.get("nodes", []):
            node = GraphNode(
                id=node_data["id"],
                node_type=NodeType(node_data["type"]),
                name=node_data["name"],
                location=SourceLocation(
                    file_path=node_data["location"]["file"],
                    line_start=node_data["location"]["line_start"],
                    line_end=node_data["location"]["line_end"],
                ),
                language=node_data["language"],
                metadata=node_data.get("metadata", {}),
                confidence=node_data.get("confidence", 1.0),
            )
            graph.add_node(node)

        for edge_data in data.get("edges", []):
            edge = GraphEdge(
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                edge_type=EdgeType(edge_data["type"]),
                confidence=edge_data.get("confidence", 1.0),
                metadata=edge_data.get("metadata", {}),
            )
            graph.add_edge(edge)

        return graph
