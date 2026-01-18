# Reachability Proof Engine

**Version:** 1.0.0
**Status:** PRODUCTION
**Proof Level:** P2 (STATIC_PARTIAL)
**Overall Confidence:** 0.75

---

## Purpose

The Reachability Proof Engine answers the fundamental question:

> **"Can this code be executed from any entry point?"**

More critically, it can answer the inverse:

> **"Can we prove this code is NEVER executed?"**

This is the killer feature. Non-reachability proofs expose:
- Dead code that appears functional
- Features that exist but are never triggered
- Routes that are defined but never mounted
- Handlers that are registered but never called

---

## Graph Model

### Node Types

| Node Type | Description | Detection Method |
|-----------|-------------|------------------|
| `ENTRY_POINT` | Application entry (main, app.listen, CLI) | Framework detection |
| `ROUTE` | HTTP/RPC route handler | Decorator/router detection |
| `FUNCTION` | Regular function/method | AST extraction |
| `EVENT_HANDLER` | Event callback (onClick, on('event')) | Event binding detection |
| `SCHEDULED_JOB` | Cron/timer/scheduler | Scheduler detection |
| `UI_COMPONENT` | React/Vue/Angular component | Framework detection |
| `UI_ELEMENT` | Interactive DOM element | JSX/template parsing |
| `DATABASE_OP` | Database query/mutation | ORM/query detection |
| `EXTERNAL_CALL` | HTTP/IPC/process spawn | Call pattern detection |
| `EXPORT` | Exported symbol | Export statement |
| `IMPORT` | Imported symbol | Import statement |

### Edge Types

| Edge Type | Description | Proof Level |
|-----------|-------------|-------------|
| `CALLS` | Direct function call | P1 (STATIC_COMPLETE) |
| `IMPORTS` | Module import | P1 (STATIC_COMPLETE) |
| `EXPORTS` | Module export | P1 (STATIC_COMPLETE) |
| `DISPATCHES` | Event dispatch (static) | P2 (STATIC_PARTIAL) |
| `DISPATCHES_DYNAMIC` | Dynamic dispatch | P5 (HEURISTIC) |
| `BINDS` | UI element to handler | P2-P5 (varies) |
| `ROUTES_TO` | Route to handler | P2 (STATIC_PARTIAL) |
| `SPAWNS` | Process/subprocess | P2 (STATIC_PARTIAL) |
| `HTTP_CALLS` | HTTP request | P2 (STATIC_PARTIAL) |
| `QUERIES` | Database query | P2 (STATIC_PARTIAL) |
| `PUBLISHES` | Message queue publish | P3-P5 (varies) |
| `SUBSCRIBES` | Message queue subscribe | P3-P5 (varies) |

### Graph Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "name", "location"],
        "properties": {
          "id": { "type": "string" },
          "type": { "enum": ["ENTRY_POINT", "ROUTE", "FUNCTION", "EVENT_HANDLER", "SCHEDULED_JOB", "UI_COMPONENT", "UI_ELEMENT", "DATABASE_OP", "EXTERNAL_CALL", "EXPORT", "IMPORT"] },
          "name": { "type": "string" },
          "location": {
            "type": "object",
            "properties": {
              "file": { "type": "string" },
              "line": { "type": "integer" },
              "column": { "type": "integer" }
            }
          },
          "metadata": { "type": "object" }
        }
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source", "target", "type", "proof_level"],
        "properties": {
          "source": { "type": "string" },
          "target": { "type": "string" },
          "type": { "type": "string" },
          "proof_level": { "enum": ["P1", "P2", "P3", "P4", "P5", "P6", "P7"] },
          "evidence": { "type": "string" }
        }
      }
    }
  }
}
```

---

## Algorithm

### Phase 1: Graph Construction

```python
def build_reachability_graph(repo_path: Path) -> Graph:
    """
    Build complete reachability graph from repository.

    Steps:
    1. Parse all files with tree-sitter
    2. Extract nodes (functions, classes, components, etc.)
    3. Build import/export graph
    4. Trace call relationships
    5. Detect event bindings
    6. Identify entry points
    """
    graph = Graph()

    # Step 1: Parse all source files
    for file in discover_source_files(repo_path):
        ast = parse_file(file)

        # Step 2: Extract nodes
        for node in extract_declarations(ast):
            graph.add_node(node)

        # Step 3: Build import/export edges
        for import_stmt in extract_imports(ast):
            graph.add_edge(Edge(
                source=file,
                target=import_stmt.module,
                type="IMPORTS",
                proof_level="P1"
            ))

        # Step 4: Trace call relationships
        for call in extract_calls(ast):
            target = resolve_call_target(call, graph)
            if target:
                graph.add_edge(Edge(
                    source=call.containing_function,
                    target=target,
                    type="CALLS",
                    proof_level="P1" if target.is_static else "P5"
                ))

    # Step 5: Detect event bindings
    for binding in extract_event_bindings(graph):
        graph.add_edge(Edge(
            source=binding.element,
            target=binding.handler,
            type="BINDS",
            proof_level=binding.proof_level
        ))

    # Step 6: Identify entry points
    for entry in detect_entry_points(repo_path):
        graph.mark_entry_point(entry)

    return graph
```

### Phase 2: Reachability Analysis

```python
def compute_reachability(graph: Graph) -> ReachabilityResult:
    """
    Compute which nodes are reachable from entry points.

    Returns:
    - reachable: set of node IDs reachable from any entry point
    - unreachable: set of node IDs NOT reachable
    - proofs: for each unreachable node, proof of non-reachability
    """
    entry_points = graph.get_entry_points()

    # BFS/DFS from all entry points
    reachable = set()
    for entry in entry_points:
        reachable.update(bfs_reachable(graph, entry))

    # Everything else is unreachable
    all_nodes = set(graph.nodes.keys())
    unreachable = all_nodes - reachable

    # Generate proofs for unreachable nodes
    proofs = {}
    for node_id in unreachable:
        proofs[node_id] = generate_non_reachability_proof(graph, node_id)

    return ReachabilityResult(
        reachable=reachable,
        unreachable=unreachable,
        proofs=proofs,
        confidence=compute_confidence(graph)
    )
```

### Phase 3: Non-Reachability Proof Generation

```python
def generate_non_reachability_proof(graph: Graph, node_id: str) -> NonReachabilityProof:
    """
    Generate a proof that a node is not reachable.

    This is the critical feature. We must show WHY the code cannot run.
    """
    node = graph.get_node(node_id)

    # Find all potential callers
    potential_callers = graph.get_nodes_that_could_call(node)

    # For each potential caller, explain why it doesn't call this node
    missing_edges = []
    for caller in potential_callers:
        if not graph.has_edge(caller.id, node_id):
            missing_edges.append(MissingEdge(
                from_node=caller,
                to_node=node,
                reason=determine_missing_reason(caller, node, graph)
            ))

    # Check if node is exported but never imported
    if node.type == "EXPORT":
        importers = graph.get_importers(node)
        if not importers:
            return NonReachabilityProof(
                node=node,
                proof_type="EXPORTED_BUT_NEVER_IMPORTED",
                evidence=ExportEvidence(
                    export_location=node.location,
                    searched_files=graph.get_all_files(),
                    found_imports=[]
                ),
                confidence=0.95
            )

    # Check if node is a handler that's never bound
    if node.type == "EVENT_HANDLER":
        bindings = graph.get_bindings_to(node)
        if not bindings:
            return NonReachabilityProof(
                node=node,
                proof_type="HANDLER_NEVER_BOUND",
                evidence=HandlerEvidence(
                    handler_location=node.location,
                    searched_ui_elements=graph.get_ui_elements(),
                    found_bindings=[]
                ),
                confidence=0.85
            )

    # Check if node is a route that's never mounted
    if node.type == "ROUTE":
        mounts = graph.get_route_mounts(node)
        if not mounts:
            return NonReachabilityProof(
                node=node,
                proof_type="ROUTE_NEVER_MOUNTED",
                evidence=RouteEvidence(
                    route_location=node.location,
                    route_pattern=node.metadata.get("pattern"),
                    searched_app_configs=graph.get_app_configs(),
                    found_mounts=[]
                ),
                confidence=0.90
            )

    # Generic unreachable proof
    return NonReachabilityProof(
        node=node,
        proof_type="NO_PATH_FROM_ENTRY",
        evidence=PathEvidence(
            node_location=node.location,
            entry_points=graph.get_entry_points(),
            missing_edges=missing_edges,
            nearest_reachable=find_nearest_reachable(graph, node)
        ),
        confidence=compute_proof_confidence(missing_edges)
    )
```

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `repo_path` | Path | Yes | Repository root path |
| `entry_points` | List[str] | No | Override entry point detection |
| `include_patterns` | List[str] | No | Glob patterns to include |
| `exclude_patterns` | List[str] | No | Glob patterns to exclude |
| `language_profiles` | List[str] | No | Which language profiles to use |
| `max_depth` | int | No | Maximum call chain depth (default: 50) |
| `timeout_seconds` | int | No | Analysis timeout (default: 300) |

---

## Outputs

### Primary Output: Reachability Report

```json
{
  "repo_path": "/path/to/repo",
  "analysis_timestamp": "2024-01-18T12:00:00Z",
  "analysis_duration_seconds": 45.2,
  "graph_stats": {
    "total_nodes": 1234,
    "total_edges": 5678,
    "entry_points": 12
  },
  "reachability": {
    "reachable_count": 1100,
    "unreachable_count": 134,
    "reachable_percentage": 89.1
  },
  "unreachable_nodes": [
    {
      "id": "node_123",
      "type": "FUNCTION",
      "name": "handleUnusedClick",
      "location": {
        "file": "src/components/Button.tsx",
        "line": 45,
        "column": 3
      },
      "proof": {
        "type": "HANDLER_NEVER_BOUND",
        "confidence": 0.85,
        "evidence": {
          "handler_location": "src/components/Button.tsx:45",
          "searched_ui_elements": ["src/**/*.tsx"],
          "found_bindings": []
        }
      }
    }
  ],
  "graph_file": ".codetruth/graphs/reachability.json",
  "overall_confidence": 0.78
}
```

### Secondary Output: Graph File

The full graph is saved to `.codetruth/graphs/reachability.json` in the schema defined above.

### Tertiary Output: SARIF Findings

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "CodeTruth-Reachability",
          "version": "1.0.0"
        }
      },
      "results": [
        {
          "ruleId": "UNREACHABLE_CODE",
          "level": "warning",
          "message": {
            "text": "Function 'handleUnusedClick' is never called from any entry point"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": { "uri": "src/components/Button.tsx" },
                "region": { "startLine": 45, "startColumn": 3 }
              }
            }
          ],
          "properties": {
            "proof_type": "HANDLER_NEVER_BOUND",
            "confidence": 0.85
          }
        }
      ]
    }
  ]
}
```

---

## Proof Rules

### Rule 1: Transitive Reachability

```
IF edge(A, B) exists AND A is reachable
THEN B is reachable

Proof level: MIN(edge.proof_level, A.reachability_proof_level)
```

### Rule 2: Entry Point Reachability

```
IF node is an ENTRY_POINT
THEN node is reachable with proof_level P1

Entry points:
- main() functions
- HTTP server entry (app.listen, uvicorn.run)
- CLI entry (__main__, argparse main)
- Test entry (pytest, jest)
- Cron entry (scheduled task)
```

### Rule 3: Non-Reachability

```
IF node has no incoming edges from reachable nodes
AND node is not an ENTRY_POINT
THEN node is UNREACHABLE

Proof strength:
- P1: Static analysis complete, no dynamic dispatch possible
- P2: Static analysis complete, dynamic dispatch unlikely
- P5: Static analysis incomplete, dynamic dispatch possible
```

### Rule 4: Conditional Reachability

```
IF edge(A, B) is conditional (inside if/switch/ternary)
THEN B.reachability = CONDITIONAL

Conditional reachability does NOT count as "working" for feature verification.
Must have runtime evidence of execution.
```

### Rule 5: Cross-Language Boundaries

```
IF call crosses language boundary (Node → Python, etc.)
THEN proof_level = MAX(P5, existing_level)

Boundary types:
- HTTP/REST (can verify with contract)
- IPC/subprocess (can verify with spawn detection)
- FFI (very limited verification)
- File handoff (can verify file existence)
```

---

## Failure Cases

### False Positives (Claims unreachable but isn't)

| Case | Detection | Mitigation |
|------|-----------|------------|
| Dynamic import | `import()`, `require()` with variable | Mark as P5, flag for manual review |
| Reflection | `getattr()`, `Reflect.get()` | Mark as P5, flag for manual review |
| Event delegation | `document.on('click', handler)` | Pattern detection for delegation |
| Plugin loading | Dynamic module loading | Plugin manifest parsing |
| String-based dispatch | `handlers[name]()` | Pattern detection, flag as P5 |
| Test-only code | Code only reachable from tests | Separate test reachability |

### False Negatives (Claims reachable but isn't)

| Case | Detection | Mitigation |
|------|-----------|------------|
| Dead branch | `if (false) { code }` | Dead branch elimination |
| Feature flag | `if (process.env.FEATURE) {}` | Flag as CONDITIONAL |
| Error-only path | Only reachable on error | Mark as ERROR_PATH |
| Deprecated code | Marked deprecated but still in graph | Check for deprecation markers |

---

## Determinism Guarantees

| Guarantee | Status | Notes |
|-----------|--------|-------|
| Same input → same output | YES | No randomness in algorithm |
| Order-independent | YES | Node ordering normalized |
| Parallelizable | YES | Per-file analysis is independent |
| Incremental | PARTIAL | Can update graph incrementally |
| Reproducible | YES | All inputs are deterministic |

---

## Performance Characteristics

| Metric | Typical Value | Worst Case |
|--------|---------------|------------|
| Nodes per 1K LOC | 50-100 | 500+ (macro-heavy code) |
| Edges per node | 2-5 | 50+ (highly connected) |
| Analysis time per 10K LOC | 5-10 seconds | 60+ seconds |
| Memory per 10K nodes | 100 MB | 1+ GB (large graphs) |
| Graph file size | 1 MB / 10K nodes | 10+ MB |

---

## Integration with Other Engines

### UI No-Op Detector

Reachability feeds into UI verification:
- Element is reachable ✓
- Element binding is reachable ✓
- Handler produces observable effect ← needs UI No-Op Detector

### Runtime Truth Correlator

Reachability provides static baseline:
- Static says reachable → verify with runtime
- Static says unreachable → if runtime shows execution, contradiction!

### Boundary Contract Verifier

Reachability detects cross-boundary calls:
- HTTP calls: traced to OpenAPI contract
- IPC calls: traced to process spawn
- Database calls: traced to schema

---

## Limitations (MANDATORY)

### What This Engine CANNOT Prove

1. **Dynamic dispatch resolution**: `obj[method]()` cannot be resolved statically
2. **Eval/exec contents**: Dynamic code execution is opaque
3. **External triggers**: Webhooks, cron, external events
4. **Runtime conditions**: Feature flags, environment variables
5. **User input paths**: Code reachable only with specific input
6. **Reflection**: `getattr()`, `Reflect`, `Type.GetMethod()`
7. **Plugin systems**: Dynamically loaded code
8. **Generated code**: Code generated at build/runtime

### What MUST Be Labeled UNPROVEN

- Any node with only P5+ edges to it: `UNPROVEN (dynamic dispatch)`
- Any node behind feature flag: `UNPROVEN (conditional)`
- Any cross-language call: `UNPROVEN (boundary crossing)`
- Any node only reachable via reflection: `UNPROVEN (reflection)`

---

## Acceptance Tests

### Test 1: Detect Unused Function

**Fixture:**
```javascript
// src/utils.js
export function usedFunction() { return 1; }
export function unusedFunction() { return 2; }  // Never imported

// src/main.js
import { usedFunction } from './utils.js';
console.log(usedFunction());
```

**Expected Finding:**
```json
{
  "node": "unusedFunction",
  "proof_type": "EXPORTED_BUT_NEVER_IMPORTED",
  "confidence": 0.95
}
```

### Test 2: Detect Unbound Handler

**Fixture:**
```tsx
// src/Button.tsx
function handleClick() { console.log('clicked'); }
function handleHover() { console.log('hovered'); }  // Never bound

export function Button() {
  return <button onClick={handleClick}>Click</button>;
}
```

**Expected Finding:**
```json
{
  "node": "handleHover",
  "proof_type": "HANDLER_NEVER_BOUND",
  "confidence": 0.85
}
```

### Test 3: Detect Unmounted Route

**Fixture:**
```python
# routes.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/users")
def get_users(): pass

@router.get("/admin")  # Never mounted
def admin_panel(): pass

# main.py
from fastapi import FastAPI
from routes import router

app = FastAPI()
app.include_router(router, prefix="/api")
# Note: admin router not included
```

**Expected Finding:**
```json
{
  "node": "admin_panel",
  "proof_type": "ROUTE_NEVER_MOUNTED",
  "confidence": 0.90
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial specification |
