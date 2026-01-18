# Evidence Integrity Model

**Version:** 1.0.0
**Status:** AUTHORITATIVE

---

## Purpose

This document defines the legal standard for evidence in CodeTruth. Evidence is not just data—it's proof that must meet specific criteria to be admissible.

> **Evidence that cannot be reproduced is not evidence.**

---

## Evidence Schema

### Core Evidence Object

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://codetruth.dev/schemas/evidence.json",
  "type": "object",
  "required": ["id", "type", "timestamp", "source", "content", "integrity"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this evidence"
    },
    "type": {
      "type": "string",
      "enum": [
        "AST_ANALYSIS",
        "LINT_RESULT",
        "TYPE_CHECK",
        "SAST_FINDING",
        "TEST_RESULT",
        "COVERAGE_REPORT",
        "E2E_TRACE",
        "UI_VERIFICATION",
        "NETWORK_HAR",
        "REACHABILITY_GRAPH",
        "BOUNDARY_CHECK",
        "MANUAL_REVIEW"
      ]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "When evidence was collected"
    },
    "source": {
      "type": "object",
      "required": ["tool", "version", "command"],
      "properties": {
        "tool": { "type": "string" },
        "version": { "type": "string" },
        "command": { "type": "string" },
        "config": { "type": "object" }
      }
    },
    "content": {
      "type": "object",
      "description": "The actual evidence data (varies by type)"
    },
    "integrity": {
      "type": "object",
      "required": ["hash", "algorithm"],
      "properties": {
        "hash": { "type": "string" },
        "algorithm": { "enum": ["sha256", "sha384", "sha512"] }
      }
    },
    "proof_level": {
      "type": "string",
      "enum": ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    },
    "trust_level": {
      "type": "string",
      "enum": ["T0", "T1", "T2", "T3", "T4"]
    },
    "reproducibility": {
      "type": "object",
      "properties": {
        "is_reproducible": { "type": "boolean" },
        "reproduction_command": { "type": "string" },
        "required_environment": { "type": "object" }
      }
    },
    "expiry": {
      "type": "string",
      "format": "date-time",
      "description": "When this evidence becomes stale"
    },
    "linked_findings": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" }
    }
  }
}
```

---

## Trust Levels

### T0: VERIFIED

**Definition:** Evidence independently verified and reproducible.

**Requirements:**
- Hash of content matches stored hash
- Reproduction command produces same result
- No external dependencies that could change

**Examples:**
- AST from deterministic parser
- Test results with seed
- Coverage from instrumented run

### T1: TOOL_OUTPUT

**Definition:** Output from trusted tool, not independently verified.

**Requirements:**
- Tool is in approved tool list
- Tool version is recorded
- Command is recorded
- Output format is valid

**Examples:**
- ESLint results
- mypy type check
- Semgrep findings

### T2: INFERRED

**Definition:** Derived from other evidence through documented logic.

**Requirements:**
- Source evidence is documented
- Derivation logic is explicit
- Derivation is deterministic

**Examples:**
- Unreachability proof from call graph
- Feature status from multiple sources
- Confidence scores

### T3: CLAIMED

**Definition:** Stated but not verified.

**Requirements:**
- Source is documented
- Marked for verification
- Not used for release decisions

**Examples:**
- Documentation claims
- Comments in code
- External reports

### T4: UNKNOWN

**Definition:** Source or validity unknown.

**Requirements:**
- Must not be used as evidence
- Must block release if referenced
- Requires investigation

**Examples:**
- Old reports without source
- Corrupted data
- Third-party claims

---

## Proof Levels

| Level | Name | Definition | Admissibility |
|-------|------|------------|---------------|
| P0 | FORMAL | Mathematical proof | Fully admissible |
| P1 | STATIC_COMPLETE | Static analysis, complete scope | Fully admissible |
| P2 | STATIC_PARTIAL | Static analysis, known gaps | Admissible with caveats |
| P3 | DYNAMIC_VERIFIED | Runtime verified | Fully admissible |
| P4 | DYNAMIC_SAMPLED | Runtime sampled | Admissible with caveats |
| P5 | HEURISTIC | Pattern-based | Advisory only |
| P6 | ASSUMPTION | Cannot prove | Not admissible |
| P7 | IMPOSSIBLE | Unprovable | Not admissible |

---

## Evidence Types

### AST_ANALYSIS

```json
{
  "type": "AST_ANALYSIS",
  "source": {
    "tool": "tree-sitter",
    "version": "0.20.0",
    "parser": "tree-sitter-typescript"
  },
  "content": {
    "file": "src/Button.tsx",
    "nodes_count": 156,
    "functions": ["handleClick", "render"],
    "exports": ["Button"],
    "imports": ["react", "./utils"]
  },
  "proof_level": "P1",
  "trust_level": "T0"
}
```

### TEST_RESULT

```json
{
  "type": "TEST_RESULT",
  "source": {
    "tool": "jest",
    "version": "29.0.0",
    "command": "npx jest --json"
  },
  "content": {
    "total": 150,
    "passed": 148,
    "failed": 2,
    "skipped": 0,
    "failures": [
      {
        "name": "Button.test.tsx > should handle click",
        "message": "Expected 1 but received 0"
      }
    ]
  },
  "proof_level": "P3",
  "trust_level": "T0"
}
```

### E2E_TRACE

```json
{
  "type": "E2E_TRACE",
  "source": {
    "tool": "playwright",
    "version": "1.40.0",
    "command": "npx playwright test --trace on"
  },
  "content": {
    "test_name": "Save settings flow",
    "trace_file": ".codetruth/traces/save-settings.zip",
    "video_file": ".codetruth/videos/save-settings.webm",
    "har_file": ".codetruth/har/save-settings.har",
    "duration_ms": 4500,
    "status": "passed"
  },
  "proof_level": "P3",
  "trust_level": "T0"
}
```

### UI_VERIFICATION

```json
{
  "type": "UI_VERIFICATION",
  "source": {
    "tool": "codetruth-ui-verifier",
    "version": "1.0.0"
  },
  "content": {
    "element": "button#save-settings",
    "action": "click",
    "before_state": { "...": "..." },
    "after_state": { "...": "..." },
    "effects_observed": [],
    "verdict": "NO_OP"
  },
  "proof_level": "P3",
  "trust_level": "T0"
}
```

### REACHABILITY_GRAPH

```json
{
  "type": "REACHABILITY_GRAPH",
  "source": {
    "tool": "codetruth-reachability",
    "version": "1.0.0"
  },
  "content": {
    "graph_file": ".codetruth/graphs/reachability.json",
    "nodes_count": 1234,
    "edges_count": 5678,
    "reachable": 1100,
    "unreachable": 134
  },
  "proof_level": "P2",
  "trust_level": "T0"
}
```

---

## Expiry Rules

### Evidence Staleness

| Evidence Type | Default Expiry | Trigger for Refresh |
|---------------|----------------|---------------------|
| AST_ANALYSIS | 7 days | File modification |
| LINT_RESULT | 7 days | File modification |
| TYPE_CHECK | 7 days | File modification |
| TEST_RESULT | 24 hours | Any code change |
| COVERAGE_REPORT | 24 hours | Any code change |
| E2E_TRACE | 24 hours | Any code change |
| UI_VERIFICATION | 24 hours | Any code change |
| REACHABILITY_GRAPH | 7 days | File add/remove |
| SAST_FINDING | 7 days | File modification |

### Expiry Computation

```python
def compute_expiry(evidence: Evidence, repo_state: RepoState) -> datetime:
    """
    Compute when evidence expires.

    Rules:
    1. Start with default expiry for type
    2. If source file modified, expire immediately
    3. If dependency changed, expire in 24 hours
    4. Cap at 30 days maximum
    """
    default_expiry = DEFAULT_EXPIRY[evidence.type]
    created_at = evidence.timestamp

    # Check if source files changed
    for file in evidence.get_source_files():
        if repo_state.file_modified_after(file, created_at):
            return created_at  # Already expired

    # Check dependencies
    for dep in evidence.get_dependencies():
        if repo_state.dependency_changed_after(dep, created_at):
            return created_at + timedelta(hours=24)

    # Default expiry
    return min(
        created_at + default_expiry,
        created_at + timedelta(days=30)  # Max 30 days
    )
```

---

## Reproducibility Requirements

### Required Fields

```json
{
  "reproducibility": {
    "is_reproducible": true,
    "reproduction_command": "npx jest --json --testPathPattern='Button'",
    "required_environment": {
      "node_version": "18.x",
      "packages": ["jest@29.0.0", "typescript@5.0.0"],
      "env_vars": ["CI=true"]
    },
    "expected_output_hash": "sha256:abc123...",
    "tolerance": {
      "timing_variance_ms": 100,
      "order_independent": true
    }
  }
}
```

### Reproduction Verification

```python
def verify_reproduction(evidence: Evidence) -> ReproductionResult:
    """
    Verify that evidence can be reproduced.

    Steps:
    1. Set up required environment
    2. Run reproduction command
    3. Compare output hash
    4. Check within tolerance
    """
    if not evidence.reproducibility.is_reproducible:
        return ReproductionResult(
            success=False,
            reason="Evidence marked as non-reproducible"
        )

    # Set up environment
    env = setup_environment(evidence.reproducibility.required_environment)

    # Run command
    output = run_command(
        evidence.reproducibility.reproduction_command,
        env=env
    )

    # Compute hash
    output_hash = hash_output(output, evidence.reproducibility.tolerance)

    # Compare
    if output_hash == evidence.reproducibility.expected_output_hash:
        return ReproductionResult(success=True)
    else:
        return ReproductionResult(
            success=False,
            reason="Output hash mismatch",
            expected=evidence.reproducibility.expected_output_hash,
            actual=output_hash
        )
```

---

## Hashing Requirements

### Content Hashing

```python
def hash_evidence_content(content: dict, tolerance: Tolerance) -> str:
    """
    Hash evidence content for integrity verification.

    Rules:
    1. Normalize JSON (sorted keys, no whitespace)
    2. Remove non-deterministic fields (timestamps, IDs)
    3. Apply tolerance rules
    4. Compute SHA-256
    """
    normalized = normalize_content(content, tolerance)
    canonical = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()
```

### Non-Deterministic Field Handling

| Field Pattern | Handling |
|---------------|----------|
| `*timestamp*` | Remove or normalize to epoch |
| `*_id`, `*Id` | Replace with placeholder |
| `duration*` | Remove or bin to ranges |
| `random*` | Remove |
| `pid`, `port` | Remove |
| File paths | Normalize to relative |

---

## Conflict Resolution

### When Evidence Conflicts

```python
def resolve_conflict(evidence_a: Evidence, evidence_b: Evidence) -> Evidence:
    """
    Resolve conflicting evidence.

    Priority (highest to lowest):
    1. Trust level (T0 > T1 > T2 > T3)
    2. Proof level (P0 > P1 > ... > P7)
    3. Recency (newer > older)
    4. Specificity (line-level > file-level)
    """
    # Compare trust levels
    if evidence_a.trust_level < evidence_b.trust_level:
        return evidence_a
    if evidence_b.trust_level < evidence_a.trust_level:
        return evidence_b

    # Compare proof levels
    if evidence_a.proof_level < evidence_b.proof_level:
        return evidence_a
    if evidence_b.proof_level < evidence_a.proof_level:
        return evidence_b

    # Compare recency
    if evidence_a.timestamp > evidence_b.timestamp:
        return evidence_a
    if evidence_b.timestamp > evidence_a.timestamp:
        return evidence_b

    # Compare specificity
    if is_more_specific(evidence_a, evidence_b):
        return evidence_a

    return evidence_b
```

### Conflict Recording

All conflicts must be recorded:

```json
{
  "conflict": {
    "evidence_a_id": "uuid-a",
    "evidence_b_id": "uuid-b",
    "conflict_type": "CONTRADICTING_RESULTS",
    "resolution": "TRUST_LEVEL",
    "resolved_to": "uuid-a",
    "timestamp": "2024-01-18T12:00:00Z"
  }
}
```

---

## Inadmissible Evidence

### What Is NOT Admissible

| Type | Reason | Alternative |
|------|--------|-------------|
| Comments claiming completion | No verification | Require tests |
| "It works on my machine" | Not reproducible | Require CI pass |
| Test names without assertions | No actual test | Require assertions |
| Coverage without assertions | Execution != correctness | Require meaningful tests |
| Type assertions (`as any`) | Bypasses type system | Runtime validation |
| Manual claims without proof | Subjective | Require evidence |
| Old evidence (>30 days) | May be stale | Re-run analysis |
| T4 (UNKNOWN) evidence | Cannot verify | Investigate source |

### Automatic Rejection

```python
def is_admissible(evidence: Evidence) -> tuple[bool, str]:
    """
    Check if evidence is admissible.

    Returns: (is_admissible, reason)
    """
    # T4 evidence is never admissible
    if evidence.trust_level == "T4":
        return False, "UNKNOWN trust level"

    # P6/P7 evidence is never admissible
    if evidence.proof_level in ["P6", "P7"]:
        return False, f"Proof level {evidence.proof_level} not admissible"

    # Expired evidence
    if evidence.expiry < datetime.now():
        return False, "Evidence expired"

    # Missing integrity
    if not verify_integrity(evidence):
        return False, "Integrity check failed"

    # Non-reproducible T0 evidence
    if evidence.trust_level == "T0" and not evidence.reproducibility.is_reproducible:
        return False, "T0 evidence must be reproducible"

    return True, "Admissible"
```

---

## Storage Requirements

### Evidence Storage

```
.codetruth/
├── evidence/
│   ├── index.json              # Evidence index
│   ├── by-type/
│   │   ├── ast_analysis/
│   │   ├── test_result/
│   │   └── ...
│   ├── by-finding/
│   │   └── {finding-id}/
│   │       └── evidence.json
│   └── artifacts/
│       ├── traces/
│       ├── videos/
│       ├── har/
│       └── graphs/
├── integrity/
│   └── checksums.json          # All evidence hashes
└── conflicts/
    └── log.json                # Conflict resolution log
```

### Index Schema

```json
{
  "version": "1.0.0",
  "last_updated": "2024-01-18T12:00:00Z",
  "evidence_count": 156,
  "by_type": {
    "AST_ANALYSIS": 45,
    "TEST_RESULT": 50,
    "COVERAGE_REPORT": 1,
    "E2E_TRACE": 10,
    "UI_VERIFICATION": 20,
    "REACHABILITY_GRAPH": 1,
    "SAST_FINDING": 29
  },
  "by_trust_level": {
    "T0": 100,
    "T1": 50,
    "T2": 5,
    "T3": 1
  },
  "expired": 3,
  "conflicts": 2
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial specification |
