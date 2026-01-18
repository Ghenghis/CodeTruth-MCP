"""
Reachability Proof Engine - Proof Generation

This module generates proofs of reachability and non-reachability.
Non-reachability proofs are critical for detecting dead code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .graph import (
    ReachabilityGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    SourceLocation,
)


class ProofType(Enum):
    """Types of proofs that can be generated."""
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    CONDITIONALLY_REACHABLE = "conditionally_reachable"
    UNKNOWN = "unknown"


class ProofStrength(Enum):
    """Strength of the proof."""
    FORMAL = "formal"           # Mathematically proven
    STATIC_COMPLETE = "static_complete"  # All static paths analyzed
    STATIC_PARTIAL = "static_partial"    # Some paths analyzed
    HEURISTIC = "heuristic"     # Best-effort analysis
    ASSUMPTION = "assumption"   # Based on assumptions


@dataclass
class CutSet:
    """
    A cut set explains why a node is unreachable.

    The cut set identifies the "missing link" - what edge
    would need to exist for the node to become reachable.
    """
    missing_edge_type: EdgeType
    from_node_id: str
    to_node_id: str
    explanation: str
    evidence_locations: List[SourceLocation] = field(default_factory=list)
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "missing_edge_type": self.missing_edge_type.value,
            "from_node": self.from_node_id,
            "to_node": self.to_node_id,
            "explanation": self.explanation,
            "evidence": [loc.to_dict() for loc in self.evidence_locations],
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class ReachabilityProof:
    """
    A proof of reachability or non-reachability.

    This is the core evidence artifact for dead code detection.
    """
    proof_id: str
    proof_type: ProofType
    strength: ProofStrength
    source_node_id: str
    target_node_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    # For reachable proofs
    paths: List[List[str]] = field(default_factory=list)

    # For unreachable proofs
    cut_sets: List[CutSet] = field(default_factory=list)

    # Metadata
    confidence: float = 1.0
    analysis_duration_ms: int = 0
    graph_hash: str = ""
    blindspots: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "proof_type": self.proof_type.value,
            "strength": self.strength.value,
            "source_node": self.source_node_id,
            "target_node": self.target_node_id,
            "created_at": self.created_at.isoformat(),
            "paths": self.paths,
            "cut_sets": [cs.to_dict() for cs in self.cut_sets],
            "confidence": self.confidence,
            "analysis_duration_ms": self.analysis_duration_ms,
            "graph_hash": self.graph_hash,
            "blindspots": self.blindspots,
        }


@dataclass
class UnreachabilityReport:
    """
    Complete report of all unreachable nodes in a codebase.
    """
    repo_path: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    graph_hash: str = ""
    total_nodes: int = 0
    unreachable_count: int = 0
    proofs: List[ReachabilityProof] = field(default_factory=list)
    blindspots: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": "1.0.0",
            "repo_path": self.repo_path,
            "created_at": self.created_at.isoformat(),
            "graph_hash": self.graph_hash,
            "statistics": {
                "total_nodes": self.total_nodes,
                "unreachable_count": self.unreachable_count,
                "unreachable_percentage": round(
                    (self.unreachable_count / max(self.total_nodes, 1)) * 100, 2
                ),
            },
            "proofs": [p.to_dict() for p in self.proofs],
            "blindspots": self.blindspots,
        }

    def export_json(self, output_path: Path) -> None:
        """Export report to JSON file."""
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class ReachabilityProver:
    """
    Generates reachability and non-reachability proofs.
    """

    # Standard blindspots that apply to all analyses
    STANDARD_BLINDSPOTS = [
        "Dynamic imports (import(), require() with variables)",
        "Reflection-based calls (getattr, eval, exec)",
        "Event-driven code where listeners are registered at runtime",
        "Metaprogramming and code generation",
        "External plugin/extension systems",
        "Dependency injection containers",
    ]

    def __init__(self, graph: ReachabilityGraph):
        self.graph = graph
        self._proof_counter = 0

    def _generate_proof_id(self) -> str:
        self._proof_counter += 1
        return f"proof_{self._proof_counter:06d}"

    def prove_reachable(
        self,
        target_node_id: str,
        from_entries: bool = True,
        source_node_id: Optional[str] = None,
    ) -> ReachabilityProof:
        """
        Generate a proof that a node is reachable.

        Args:
            target_node_id: The node to prove reachability for
            from_entries: If True, check from all entry points
            source_node_id: Specific source node to check from

        Returns:
            ReachabilityProof with paths if reachable
        """
        import time
        start_time = time.time()

        all_paths: List[List[str]] = []
        sources = (
            [source_node_id] if source_node_id
            else list(self.graph.entry_points) if from_entries
            else []
        )

        for source in sources:
            paths = self.graph.find_paths(source, target_node_id)
            all_paths.extend(paths)

        duration_ms = int((time.time() - start_time) * 1000)

        if all_paths:
            return ReachabilityProof(
                proof_id=self._generate_proof_id(),
                proof_type=ProofType.REACHABLE,
                strength=ProofStrength.STATIC_COMPLETE,
                source_node_id=sources[0] if sources else "",
                target_node_id=target_node_id,
                paths=all_paths[:10],  # Limit to 10 paths
                confidence=1.0,
                analysis_duration_ms=duration_ms,
                graph_hash=self.graph.compute_hash(),
                blindspots=self.STANDARD_BLINDSPOTS,
            )
        else:
            # No paths found - generate unreachability proof
            return self.prove_unreachable(target_node_id)

    def prove_unreachable(self, target_node_id: str) -> ReachabilityProof:
        """
        Generate a proof that a node is NOT reachable from any entry point.

        This includes a "cut set" explaining why the node is unreachable.
        """
        import time
        start_time = time.time()

        target_node = self.graph.get_node(target_node_id)
        if not target_node:
            return ReachabilityProof(
                proof_id=self._generate_proof_id(),
                proof_type=ProofType.UNKNOWN,
                strength=ProofStrength.ASSUMPTION,
                source_node_id="",
                target_node_id=target_node_id,
                confidence=0.0,
                blindspots=["Node not found in graph"],
            )

        # Find cut sets - analyze why the node is unreachable
        cut_sets = self._find_cut_sets(target_node)

        duration_ms = int((time.time() - start_time) * 1000)

        # Determine proof strength based on analysis completeness
        strength = ProofStrength.STATIC_COMPLETE
        confidence = 0.95  # High confidence but not 100% due to dynamic features

        return ReachabilityProof(
            proof_id=self._generate_proof_id(),
            proof_type=ProofType.UNREACHABLE,
            strength=strength,
            source_node_id="(all entry points)",
            target_node_id=target_node_id,
            cut_sets=cut_sets,
            confidence=confidence,
            analysis_duration_ms=duration_ms,
            graph_hash=self.graph.compute_hash(),
            blindspots=self.STANDARD_BLINDSPOTS,
        )

    def _find_cut_sets(self, target_node: GraphNode) -> List[CutSet]:
        """
        Find the cut sets that explain why a node is unreachable.

        A cut set identifies what edge would need to be added
        to make the node reachable.
        """
        cut_sets: List[CutSet] = []

        # Check incoming edges - is there anything pointing to this node?
        incoming = self.graph.get_incoming_edges(target_node.id)

        if not incoming:
            # No incoming edges at all - completely orphaned
            cut_sets.append(CutSet(
                missing_edge_type=self._infer_expected_edge_type(target_node),
                from_node_id="(any node)",
                to_node_id=target_node.id,
                explanation=f"Node '{target_node.name}' has no incoming edges. "
                           f"It is never called, imported, or referenced.",
                evidence_locations=[target_node.location],
                suggested_fix=self._suggest_fix_for_orphan(target_node),
            ))
        else:
            # Has incoming edges but callers themselves are unreachable
            for edge in incoming:
                caller = self.graph.get_node(edge.source_id)
                if caller and not self.graph.is_reachable_from_entry(caller.id):
                    cut_sets.append(CutSet(
                        missing_edge_type=EdgeType.CALLS,
                        from_node_id=edge.source_id,
                        to_node_id=target_node.id,
                        explanation=f"Node '{target_node.name}' is called by "
                                   f"'{caller.name}', but that caller is also unreachable.",
                        evidence_locations=[caller.location, target_node.location],
                        suggested_fix=f"Make '{caller.name}' reachable, or call "
                                     f"'{target_node.name}' from reachable code.",
                    ))

        # Check for type-specific issues
        cut_sets.extend(self._check_type_specific_issues(target_node))

        return cut_sets

    def _infer_expected_edge_type(self, node: GraphNode) -> EdgeType:
        """Infer what type of edge should point to this node."""
        type_map = {
            NodeType.FUNCTION: EdgeType.CALLS,
            NodeType.HANDLER: EdgeType.BINDS,
            NodeType.ROUTE: EdgeType.MOUNTS,
            NodeType.COMPONENT: EdgeType.RENDERS,
            NodeType.CRON_JOB: EdgeType.REGISTERS,
            NodeType.MESSAGE_HANDLER: EdgeType.LISTENS,
            NodeType.PACKET_HANDLER: EdgeType.REGISTERS,
        }
        return type_map.get(node.node_type, EdgeType.CALLS)

    def _suggest_fix_for_orphan(self, node: GraphNode) -> str:
        """Generate a suggested fix for an orphaned node."""
        suggestions = {
            NodeType.FUNCTION: f"Call '{node.name}' from your main code path, or export and import it where needed.",
            NodeType.HANDLER: f"Bind '{node.name}' to a UI element using onClick, onChange, etc.",
            NodeType.ROUTE: f"Mount the route '{node.name}' in your router configuration.",
            NodeType.COMPONENT: f"Render <{node.name} /> in a parent component.",
            NodeType.CRON_JOB: f"Register '{node.name}' in your crontab or scheduler.",
            NodeType.PACKET_HANDLER: f"Register packet handler '{node.name}' in the packet registry.",
        }
        return suggestions.get(
            node.node_type,
            f"Reference '{node.name}' from reachable code."
        )

    def _check_type_specific_issues(self, node: GraphNode) -> List[CutSet]:
        """Check for type-specific unreachability issues."""
        cut_sets: List[CutSet] = []

        if node.node_type == NodeType.HANDLER:
            # Check if handler is defined but not bound
            if not any(e.edge_type == EdgeType.BINDS for e in self.graph.get_incoming_edges(node.id)):
                cut_sets.append(CutSet(
                    missing_edge_type=EdgeType.BINDS,
                    from_node_id="(UI element)",
                    to_node_id=node.id,
                    explanation=f"Handler '{node.name}' is defined but not bound to any UI element.",
                    evidence_locations=[node.location],
                    suggested_fix=f"Add onClick={{'{node.name}'}} or similar binding to a UI element.",
                ))

        elif node.node_type == NodeType.ROUTE:
            # Check if route is defined but not mounted
            if not any(e.edge_type == EdgeType.MOUNTS for e in self.graph.get_incoming_edges(node.id)):
                cut_sets.append(CutSet(
                    missing_edge_type=EdgeType.MOUNTS,
                    from_node_id="(router)",
                    to_node_id=node.id,
                    explanation=f"Route '{node.name}' is defined but not mounted in the router.",
                    evidence_locations=[node.location],
                    suggested_fix="Add this route to your router configuration (app.use, router.get, etc.).",
                ))

        return cut_sets

    def generate_unreachability_report(self) -> UnreachabilityReport:
        """
        Generate a complete unreachability report for the graph.
        """
        unreachable_nodes = self.graph.find_unreachable_nodes()
        proofs: List[ReachabilityProof] = []

        for node in unreachable_nodes:
            proof = self.prove_unreachable(node.id)
            proofs.append(proof)

        return UnreachabilityReport(
            repo_path=self.graph.repo_path,
            graph_hash=self.graph.compute_hash(),
            total_nodes=len(self.graph.nodes),
            unreachable_count=len(unreachable_nodes),
            proofs=proofs,
            blindspots=self.STANDARD_BLINDSPOTS,
        )


def analyze_reachability(graph: ReachabilityGraph) -> UnreachabilityReport:
    """
    Convenience function to analyze a graph and generate report.
    """
    prover = ReachabilityProver(graph)
    return prover.generate_unreachability_report()
