"""
Language Truth Profile Schema

This module defines the formal specification schema for Language Truth Profiles.
Every supported language/stack MUST have a complete profile that defines:

1. PARSE: What parsing capabilities exist and their accuracy guarantees
2. SEMANTICS: What execution meaning we can understand statically
3. WIRING: What reachability proofs are possible
4. RUNTIME: What dynamic verification is available
5. EVIDENCE: What proof artifacts can be generated
6. LIMITS: What CANNOT be detected (critical for honesty)

Without these definitions, language support claims are meaningless.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProofLevel(str, Enum):
    """Classification of proof strength - NEVER mix these silently."""

    FORMAL = "formal"           # Mathematical proof, 100% guarantee
    STATIC_COMPLETE = "static_complete"  # Static analysis, complete for scope
    STATIC_PARTIAL = "static_partial"    # Static analysis, known gaps
    DYNAMIC_VERIFIED = "dynamic_verified"  # Runtime verified
    DYNAMIC_SAMPLED = "dynamic_sampled"   # Runtime sampled (not exhaustive)
    HEURISTIC = "heuristic"     # Pattern-based, may have false positives/negatives
    ASSUMPTION = "assumption"    # Cannot prove, must assume
    IMPOSSIBLE = "impossible"    # Fundamentally unprovable (halting problem, etc.)


class TrustLevel(str, Enum):
    """Trust classification for evidence sources."""

    VERIFIED = "verified"       # Independently verified, reproducible
    TOOL_OUTPUT = "tool_output"  # From trusted tool, not independently verified
    INFERRED = "inferred"       # Derived from other evidence
    CLAIMED = "claimed"         # Stated but not verified (should trigger warnings)
    UNKNOWN = "unknown"         # Source unknown (should block release)


class ParserType(str, Enum):
    """Types of parsers available."""

    TREE_SITTER = "tree_sitter"
    LANGUAGE_SERVER = "language_server"
    AST_NATIVE = "ast_native"  # Python ast, esprima, etc.
    REGEX = "regex"  # Pattern matching only (lower trust)
    CUSTOM = "custom"


@dataclass
class ParseCapability:
    """Defines what parsing is possible for a language."""

    parser_type: ParserType
    parser_name: str  # Specific parser: "tree-sitter-typescript", "tsserver", etc.
    grammar_version: str | None = None

    # Accuracy guarantees
    syntax_accuracy: float = 1.0  # 0.0-1.0, how accurate is syntax parsing
    semantic_accuracy: float = 0.0  # 0.0-1.0, how much semantics understood

    # Capabilities
    can_parse_partial: bool = False  # Can parse incomplete/invalid code
    can_recover_errors: bool = False  # Can continue past syntax errors
    supports_incremental: bool = False  # Incremental parsing for large files

    # Known parse failures
    known_parse_failures: list[str] = field(default_factory=list)
    # e.g., ["decorators with complex expressions", "template literal types"]


@dataclass
class SemanticCapability:
    """Defines what semantic understanding is possible."""

    # Type system understanding
    type_inference_level: str  # "none", "basic", "full", "dependent"
    can_resolve_imports: bool = False
    can_resolve_types: bool = False
    can_track_mutations: bool = False
    can_track_control_flow: bool = False
    can_track_data_flow: bool = False

    # Scope analysis
    can_resolve_scopes: bool = False
    can_detect_shadowing: bool = False
    can_detect_closures: bool = False

    # Symbol resolution
    symbol_resolution_accuracy: float = 0.0  # 0.0-1.0
    cross_file_resolution: bool = False
    cross_module_resolution: bool = False

    # Semantic gaps - CRITICAL
    semantic_blindspots: list[str] = field(default_factory=list)
    # e.g., ["eval() contents", "dynamic imports", "reflection"]


@dataclass
class WiringCapability:
    """Defines what reachability/wiring proofs are possible."""

    # Call graph construction
    can_build_call_graph: bool = False
    call_graph_completeness: float = 0.0  # 0.0-1.0
    call_graph_proof_level: ProofLevel = ProofLevel.IMPOSSIBLE

    # Event graph (UI events, async, etc.)
    can_build_event_graph: bool = False
    event_graph_completeness: float = 0.0
    event_graph_proof_level: ProofLevel = ProofLevel.IMPOSSIBLE

    # Routing graph (HTTP, IPC, etc.)
    can_build_route_graph: bool = False
    route_graph_completeness: float = 0.0
    route_graph_proof_level: ProofLevel = ProofLevel.IMPOSSIBLE

    # Cross-boundary detection
    can_detect_ipc: bool = False
    can_detect_http: bool = False
    can_detect_file_io: bool = False
    can_detect_process_spawn: bool = False

    # Reachability proofs
    can_prove_reachable: bool = False
    can_prove_unreachable: bool = False  # This is harder!
    unreachability_proof_level: ProofLevel = ProofLevel.IMPOSSIBLE

    # Wiring gaps - CRITICAL
    wiring_blindspots: list[str] = field(default_factory=list)
    # e.g., ["dynamic dispatch", "runtime routing", "plugin loading"]


@dataclass
class RuntimeCapability:
    """Defines what runtime verification is possible."""

    # Execution environment
    can_execute: bool = False
    execution_environment: str | None = None  # "node", "browser", "python", etc.
    min_runtime_version: str | None = None

    # Runtime probes
    can_instrument: bool = False  # Code instrumentation
    can_trace: bool = False  # Execution tracing
    can_profile: bool = False  # Performance profiling
    can_snapshot: bool = False  # State snapshots

    # Browser-specific (for UI)
    can_dom_inspect: bool = False
    can_network_intercept: bool = False
    can_storage_inspect: bool = False
    can_console_capture: bool = False

    # Test execution
    can_run_unit_tests: bool = False
    can_run_integration_tests: bool = False
    can_run_e2e_tests: bool = False

    # Coverage
    can_measure_coverage: bool = False
    coverage_granularity: str = "none"  # "none", "line", "branch", "condition", "mcdc"

    # Runtime gaps - CRITICAL
    runtime_blindspots: list[str] = field(default_factory=list)
    # e.g., ["web workers", "service workers", "native modules"]


@dataclass
class EvidenceArtifact:
    """Defines a specific evidence artifact that can be produced."""

    name: str  # "ast_graph", "call_graph", "coverage_report", etc.
    format: str  # "json", "sarif", "lcov", "html", etc.
    proof_level: ProofLevel
    trust_level: TrustLevel

    # Reproducibility
    is_deterministic: bool = False  # Same input = same output?
    requires_runtime: bool = False  # Needs execution to generate?
    requires_network: bool = False  # Needs network access?

    # Schema
    schema_path: str | None = None  # JSON schema for validation

    # Generation
    generator: str | None = None  # Tool/code that generates this
    generation_timeout_seconds: int = 60


@dataclass
class KnownBlindspot:
    """
    Explicit declaration of what CANNOT be detected.

    This is the most important part of a Language Truth Profile.
    Honest systems declare their limits.
    """

    category: str  # "parsing", "semantic", "wiring", "runtime"
    name: str  # Human-readable name
    description: str  # Detailed explanation

    # Why it's a blindspot
    reason: str  # "halting_problem", "dynamic_behavior", "external_dependency", etc.

    # Severity
    impact: str  # "false_negative", "false_positive", "incomplete_analysis"
    severity: str  # "critical", "high", "medium", "low"

    # Mitigation
    mitigation: str | None = None  # What can partially address this
    requires_human_review: bool = True

    # Examples
    examples: list[str] = field(default_factory=list)


@dataclass
class CrossLanguageBoundary:
    """Defines how this language interacts with others."""

    target_language: str  # The other language
    boundary_type: str  # "ffi", "ipc", "http", "file", "process", "wasm"

    # Detection capability
    can_detect_calls: bool = False
    can_trace_data: bool = False
    can_verify_contracts: bool = False

    # Proof level
    detection_proof_level: ProofLevel = ProofLevel.IMPOSSIBLE

    # Common patterns
    common_patterns: list[str] = field(default_factory=list)
    # e.g., ["fetch() to Python API", "child_process.spawn()"]


@dataclass
class LanguageTruthProfile:
    """
    Complete Language Truth Profile.

    This is the foundational specification that defines exactly what
    CodeTruth can and cannot prove about code in this language/stack.

    Without a complete profile, language support is UNDEFINED.
    """

    # Identity
    language_id: str  # "typescript-react", "python", "dockerfile", etc.
    display_name: str
    version: str  # Profile version, not language version

    # Stack context
    stack_tier: int  # 1-5, from the tiered model
    parent_language: str | None = None  # e.g., "typescript" for "typescript-react"
    extends_profiles: list[str] = field(default_factory=list)

    # File patterns
    file_extensions: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)  # Glob patterns

    # Capabilities
    parse: ParseCapability | None = None
    semantics: SemanticCapability | None = None
    wiring: WiringCapability | None = None
    runtime: RuntimeCapability | None = None

    # Evidence artifacts this profile can produce
    evidence_artifacts: list[EvidenceArtifact] = field(default_factory=list)

    # CRITICAL: Known blindspots
    blindspots: list[KnownBlindspot] = field(default_factory=list)

    # Cross-language boundaries
    boundaries: list[CrossLanguageBoundary] = field(default_factory=list)

    # Tool dependencies
    required_tools: list[str] = field(default_factory=list)
    optional_tools: list[str] = field(default_factory=list)

    # Completeness metrics
    profile_completeness: float = 0.0  # 0.0-1.0, how complete is THIS profile
    implementation_completeness: float = 0.0  # 0.0-1.0, how much is actually implemented

    # Metadata
    author: str = "CodeTruth"
    created_at: str | None = None
    updated_at: str | None = None

    def get_overall_proof_level(self) -> ProofLevel:
        """Get the weakest proof level across all capabilities."""
        levels = []
        if self.wiring:
            levels.append(self.wiring.call_graph_proof_level)
            levels.append(self.wiring.unreachability_proof_level)

        if not levels:
            return ProofLevel.IMPOSSIBLE

        # Order from strongest to weakest
        order = [
            ProofLevel.FORMAL,
            ProofLevel.STATIC_COMPLETE,
            ProofLevel.STATIC_PARTIAL,
            ProofLevel.DYNAMIC_VERIFIED,
            ProofLevel.DYNAMIC_SAMPLED,
            ProofLevel.HEURISTIC,
            ProofLevel.ASSUMPTION,
            ProofLevel.IMPOSSIBLE,
        ]

        # Return weakest
        for level in reversed(order):
            if level in levels:
                return level
        return ProofLevel.IMPOSSIBLE

    def get_critical_blindspots(self) -> list[KnownBlindspot]:
        """Get all critical severity blindspots."""
        return [b for b in self.blindspots if b.severity == "critical"]

    def can_prove_completeness(self) -> bool:
        """Can this profile prove feature completeness?"""
        if not self.wiring:
            return False
        return (
            self.wiring.can_prove_reachable and
            self.wiring.can_prove_unreachable and
            self.wiring.unreachability_proof_level != ProofLevel.IMPOSSIBLE
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LanguageTruthProfile":
        """Deserialize from dictionary."""
        # Handle nested dataclasses
        if "parse" in data and data["parse"]:
            data["parse"] = ParseCapability(**data["parse"])
        if "semantics" in data and data["semantics"]:
            data["semantics"] = SemanticCapability(**data["semantics"])
        if "wiring" in data and data["wiring"]:
            data["wiring"] = WiringCapability(**data["wiring"])
        if "runtime" in data and data["runtime"]:
            data["runtime"] = RuntimeCapability(**data["runtime"])

        if "evidence_artifacts" in data:
            data["evidence_artifacts"] = [
                EvidenceArtifact(**a) for a in data["evidence_artifacts"]
            ]
        if "blindspots" in data:
            data["blindspots"] = [
                KnownBlindspot(**b) for b in data["blindspots"]
            ]
        if "boundaries" in data:
            data["boundaries"] = [
                CrossLanguageBoundary(**b) for b in data["boundaries"]
            ]

        return cls(**data)
