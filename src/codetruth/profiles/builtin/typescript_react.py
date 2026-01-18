"""
Language Truth Profile: TypeScript + React

This is the most complex and common web stack.
It requires understanding:
- TypeScript type system
- React component lifecycle
- JSX transformation
- Event handler binding
- State management
- Hook rules
- DOM interaction

HONEST ASSESSMENT:
- Static analysis can catch many issues
- But React's dynamic nature creates fundamental blindspots
- Runtime verification (Playwright) is required for completeness proof
"""

from ..schema import (
    LanguageTruthProfile,
    ParseCapability,
    SemanticCapability,
    WiringCapability,
    RuntimeCapability,
    EvidenceArtifact,
    KnownBlindspot,
    CrossLanguageBoundary,
    ProofLevel,
    TrustLevel,
    ParserType,
)

TYPESCRIPT_REACT_PROFILE = LanguageTruthProfile(
    # Identity
    language_id="typescript-react",
    display_name="TypeScript + React",
    version="1.0.0",

    # Stack context
    stack_tier=1,  # Critical Core
    parent_language="typescript",
    extends_profiles=["typescript"],

    # File patterns
    file_extensions=[".tsx"],
    file_patterns=["**/*.tsx"],

    # ============================================================
    # PARSE CAPABILITY
    # ============================================================
    parse=ParseCapability(
        parser_type=ParserType.TREE_SITTER,
        parser_name="tree-sitter-typescript",
        grammar_version="0.20.3",

        syntax_accuracy=0.99,  # Very high - tree-sitter is excellent
        semantic_accuracy=0.70,  # JSX adds complexity

        can_parse_partial=True,
        can_recover_errors=True,
        supports_incremental=True,

        known_parse_failures=[
            "Complex generic type expressions with conditional types",
            "Template literal types with dynamic expressions",
            "Decorators with computed property names",
            "JSX spread with complex expressions",
        ],
    ),

    # ============================================================
    # SEMANTIC CAPABILITY
    # ============================================================
    semantics=SemanticCapability(
        type_inference_level="full",  # TypeScript provides full type inference
        can_resolve_imports=True,
        can_resolve_types=True,
        can_track_mutations=False,  # Limited - React state is tricky
        can_track_control_flow=True,
        can_track_data_flow=False,  # Partial - props drilling is complex

        can_resolve_scopes=True,
        can_detect_shadowing=True,
        can_detect_closures=True,

        symbol_resolution_accuracy=0.90,  # High but not perfect
        cross_file_resolution=True,
        cross_module_resolution=True,

        semantic_blindspots=[
            "eval() and new Function() contents",
            "Dynamic imports with computed paths",
            "Reflected property access (obj[key])",
            "Type assertions that lie (as any)",
            "Generic type inference in complex callbacks",
            "HOC wrapped component props",
            "Context value types at runtime",
            "Render props pattern inference",
        ],
    ),

    # ============================================================
    # WIRING CAPABILITY
    # ============================================================
    wiring=WiringCapability(
        can_build_call_graph=True,
        call_graph_completeness=0.75,  # React lifecycle complicates this
        call_graph_proof_level=ProofLevel.STATIC_PARTIAL,

        can_build_event_graph=True,  # onClick, onChange, etc.
        event_graph_completeness=0.60,  # Many dynamic patterns
        event_graph_proof_level=ProofLevel.HEURISTIC,

        can_build_route_graph=True,  # React Router detection
        route_graph_completeness=0.70,
        route_graph_proof_level=ProofLevel.STATIC_PARTIAL,

        can_detect_ipc=False,
        can_detect_http=True,  # fetch, axios, etc.
        can_detect_file_io=False,  # Client-side
        can_detect_process_spawn=False,

        can_prove_reachable=True,
        can_prove_unreachable=False,  # CRITICAL: Cannot prove negative
        unreachability_proof_level=ProofLevel.HEURISTIC,

        wiring_blindspots=[
            "Dynamic event handler binding: element.onclick = fn",
            "Event delegation: e.target analysis",
            "Conditional rendering with runtime values",
            "React.lazy and code splitting",
            "Dynamic imports: import(variable)",
            "Higher-order component wrapping",
            "Render props patterns",
            "Context.Provider value changes",
            "useEffect dependency array correctness",
            "Redux/Zustand action dispatching",
            "React Query/SWR cache invalidation",
            "Portal rendering to different DOM trees",
            "Ref forwarding chains",
            "Error boundary catch scope",
        ],
    ),

    # ============================================================
    # RUNTIME CAPABILITY
    # ============================================================
    runtime=RuntimeCapability(
        can_execute=True,
        execution_environment="browser",
        min_runtime_version="chromium:90",

        can_instrument=True,  # Via Playwright
        can_trace=True,
        can_profile=True,
        can_snapshot=True,

        can_dom_inspect=True,
        can_network_intercept=True,
        can_storage_inspect=True,
        can_console_capture=True,

        can_run_unit_tests=True,  # Jest, Vitest
        can_run_integration_tests=True,
        can_run_e2e_tests=True,  # Playwright

        can_measure_coverage=True,
        coverage_granularity="branch",

        runtime_blindspots=[
            "Web Workers: separate execution context",
            "Service Workers: async lifecycle",
            "SharedArrayBuffer: concurrent access",
            "WebAssembly: opaque execution",
            "iframe content: cross-origin blocked",
            "Browser extensions: injected scripts",
            "Native module calls: via bridge",
            "IndexedDB transactions: async timing",
            "WebSocket server push: external trigger",
            "SSE events: external trigger",
        ],
    ),

    # ============================================================
    # EVIDENCE ARTIFACTS
    # ============================================================
    evidence_artifacts=[
        EvidenceArtifact(
            name="ast_graph",
            format="json",
            proof_level=ProofLevel.STATIC_COMPLETE,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=True,
            requires_runtime=False,
            requires_network=False,
            generator="tree-sitter-typescript",
        ),
        EvidenceArtifact(
            name="component_tree",
            format="json",
            proof_level=ProofLevel.STATIC_PARTIAL,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=True,
            requires_runtime=False,
            requires_network=False,
            generator="codetruth.analyzers.react_components",
        ),
        EvidenceArtifact(
            name="event_handler_map",
            format="json",
            proof_level=ProofLevel.HEURISTIC,
            trust_level=TrustLevel.TOOL_OUTPUT,
            is_deterministic=True,
            requires_runtime=False,
            requires_network=False,
            generator="codetruth.analyzers.ui_wiring",
        ),
        EvidenceArtifact(
            name="call_graph",
            format="json",
            proof_level=ProofLevel.STATIC_PARTIAL,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=True,
            requires_runtime=False,
            requires_network=False,
            generator="codetruth.analyzers.call_graph",
        ),
        EvidenceArtifact(
            name="type_coverage",
            format="json",
            proof_level=ProofLevel.STATIC_COMPLETE,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=True,
            requires_runtime=False,
            requires_network=False,
            generator="typescript",
        ),
        EvidenceArtifact(
            name="playwright_trace",
            format="zip",
            proof_level=ProofLevel.DYNAMIC_VERIFIED,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=False,  # Runtime state varies
            requires_runtime=True,
            requires_network=False,
            generator="playwright",
            generation_timeout_seconds=300,
        ),
        EvidenceArtifact(
            name="coverage_report",
            format="lcov",
            proof_level=ProofLevel.DYNAMIC_SAMPLED,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=False,
            requires_runtime=True,
            requires_network=False,
            generator="v8-coverage",
        ),
        EvidenceArtifact(
            name="network_log",
            format="har",
            proof_level=ProofLevel.DYNAMIC_VERIFIED,
            trust_level=TrustLevel.VERIFIED,
            is_deterministic=False,
            requires_runtime=True,
            requires_network=True,
            generator="playwright",
        ),
    ],

    # ============================================================
    # KNOWN BLINDSPOTS - THE MOST IMPORTANT SECTION
    # ============================================================
    blindspots=[
        KnownBlindspot(
            category="semantic",
            name="Dynamic Type Assertions",
            description=(
                "TypeScript 'as' casts and 'any' types bypass the type system. "
                "Code can claim to be typed but have runtime type mismatches."
            ),
            reason="language_design",
            impact="false_negative",
            severity="high",
            mitigation="Lint rules against 'any', runtime type validation (zod, io-ts)",
            requires_human_review=True,
            examples=[
                "const data = response as UserData  // May not be UserData",
                "function handler(e: any) { ... }  // Unknown type",
            ],
        ),
        KnownBlindspot(
            category="wiring",
            name="Conditional Rendering Logic",
            description=(
                "React components can conditionally render UI based on runtime state. "
                "Static analysis cannot determine which code paths will execute."
            ),
            reason="dynamic_behavior",
            impact="incomplete_analysis",
            severity="critical",
            mitigation="E2E testing with state permutations, storybook stories",
            requires_human_review=True,
            examples=[
                "{isAdmin && <AdminPanel />}  // Only renders for admins",
                "{loading ? <Spinner /> : <Content />}  // Depends on async state",
            ],
        ),
        KnownBlindspot(
            category="wiring",
            name="Dynamic Event Handler Binding",
            description=(
                "Event handlers can be assigned dynamically or through indirection. "
                "Static analysis may miss the binding."
            ),
            reason="dynamic_behavior",
            impact="false_negative",
            severity="high",
            mitigation="Runtime click testing, coverage verification",
            requires_human_review=True,
            examples=[
                "onClick={handlers[actionType]}  // Dynamic lookup",
                "onClick={useMemo(() => handleClick, [])}  // Memoized handler",
            ],
        ),
        KnownBlindspot(
            category="wiring",
            name="Effect Dependency Correctness",
            description=(
                "useEffect dependency arrays can be wrong without TypeScript errors. "
                "Missing dependencies cause stale closures, extra dependencies cause loops."
            ),
            reason="language_design",
            impact="false_negative",
            severity="critical",
            mitigation="eslint-plugin-react-hooks, runtime behavior testing",
            requires_human_review=True,
            examples=[
                "useEffect(() => { doThing(value) }, [])  // value not in deps",
                "useEffect(() => { }, [obj])  // obj recreated each render",
            ],
        ),
        KnownBlindspot(
            category="runtime",
            name="Async State Race Conditions",
            description=(
                "Multiple async operations can race, causing state inconsistencies. "
                "Static analysis cannot detect these timing issues."
            ),
            reason="concurrency",
            impact="false_negative",
            severity="high",
            mitigation="AbortController usage, race condition testing",
            requires_human_review=True,
            examples=[
                "Multiple rapid clicks triggering overlapping fetches",
                "Component unmount during pending async operation",
            ],
        ),
        KnownBlindspot(
            category="wiring",
            name="Higher-Order Component Wrapping",
            description=(
                "HOCs transform components in ways that obscure the original props and behavior. "
                "Static analysis sees the wrapper, not the wrapped component."
            ),
            reason="metaprogramming",
            impact="incomplete_analysis",
            severity="medium",
            mitigation="Prefer hooks over HOCs, explicit typing",
            requires_human_review=False,
            examples=[
                "export default withAuth(withTheme(MyComponent))",
                "connect(mapState, mapDispatch)(Component)",
            ],
        ),
        KnownBlindspot(
            category="wiring",
            name="Context Value Propagation",
            description=(
                "React Context values flow through the component tree invisibly. "
                "Static analysis cannot fully trace context consumption."
            ),
            reason="framework_magic",
            impact="incomplete_analysis",
            severity="medium",
            mitigation="Explicit context typing, context usage documentation",
            requires_human_review=False,
            examples=[
                "const theme = useContext(ThemeContext)  // Where does this come from?",
                "Provider nesting order affects which value is consumed",
            ],
        ),
        KnownBlindspot(
            category="semantic",
            name="Server vs Client Code Mixing",
            description=(
                "Next.js, Remix, and other frameworks mix server and client code. "
                "Static analysis may not distinguish execution contexts."
            ),
            reason="framework_magic",
            impact="false_negative",
            severity="critical",
            mitigation="'use client' / 'use server' directives, framework-aware analysis",
            requires_human_review=True,
            examples=[
                "Accessing browser APIs in server components",
                "Exposing secrets in client bundles",
            ],
        ),
    ],

    # ============================================================
    # CROSS-LANGUAGE BOUNDARIES
    # ============================================================
    boundaries=[
        CrossLanguageBoundary(
            target_language="http-api",
            boundary_type="http",
            can_detect_calls=True,  # fetch, axios
            can_trace_data=False,  # Response is opaque
            can_verify_contracts=True,  # If OpenAPI spec exists
            detection_proof_level=ProofLevel.STATIC_PARTIAL,
            common_patterns=[
                "fetch('/api/endpoint')",
                "axios.get('/api/data')",
                "useSWR('/api/resource')",
                "useQuery(['key'], fetcher)",
            ],
        ),
        CrossLanguageBoundary(
            target_language="css",
            boundary_type="file",
            can_detect_calls=True,  # import './styles.css'
            can_trace_data=False,  # CSS is styling, not data
            can_verify_contracts=False,
            detection_proof_level=ProofLevel.STATIC_COMPLETE,
            common_patterns=[
                "import './Component.css'",
                "import styles from './Component.module.css'",
                "styled.div`...`",
                "className={styles.container}",
            ],
        ),
        CrossLanguageBoundary(
            target_language="html",
            boundary_type="transform",
            can_detect_calls=True,  # JSX -> HTML
            can_trace_data=True,  # Props -> attributes
            can_verify_contracts=False,
            detection_proof_level=ProofLevel.STATIC_COMPLETE,
            common_patterns=[
                "<div className={...}>",
                "<img src={...} />",
                "dangerouslySetInnerHTML={{__html: ...}}",
            ],
        ),
        CrossLanguageBoundary(
            target_language="nodejs",
            boundary_type="ipc",
            can_detect_calls=True,  # API routes
            can_trace_data=False,  # Serialization boundary
            can_verify_contracts=True,  # Type sharing
            detection_proof_level=ProofLevel.HEURISTIC,
            common_patterns=[
                "Next.js API routes",
                "Remix actions/loaders",
                "tRPC procedures",
            ],
        ),
    ],

    # ============================================================
    # TOOL DEPENDENCIES
    # ============================================================
    required_tools=[
        "tree-sitter",
        "typescript",
    ],
    optional_tools=[
        "eslint",
        "prettier",
        "playwright",
        "jest",
        "vitest",
    ],

    # ============================================================
    # COMPLETENESS METRICS
    # ============================================================
    profile_completeness=0.85,  # This profile is well-defined
    implementation_completeness=0.60,  # Actual code is partial

    # Metadata
    author="CodeTruth",
    created_at="2024-01-01",
    updated_at="2024-01-01",
)
