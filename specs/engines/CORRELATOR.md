# Runtime Truth Correlator

**Version:** 1.0.0
**Status:** PARTIAL
**Proof Level:** P5 (HEURISTIC)
**Overall Confidence:** 0.62

---

## Purpose

The Runtime Truth Correlator resolves the fundamental problem:

> **"When different tools give conflicting answers, what's the truth?"**

This is where "fake completeness" hides:
- Linter says OK
- Type checker says OK
- Tests pass
- But UI does nothing

The Correlator:
1. Collects evidence from all sources
2. Detects contradictions
3. Applies evidence priority rules
4. Produces a unified truth assessment

---

## Evidence Sources

### Static Analysis Sources

| Source | What It Provides | Trust Level |
|--------|------------------|-------------|
| Linter (ESLint, Ruff) | Code quality issues | T1 (TOOL_OUTPUT) |
| Type checker (tsc, mypy) | Type errors | T1 (TOOL_OUTPUT) |
| SAST (Semgrep) | Security findings | T1 (TOOL_OUTPUT) |
| Reachability Engine | Dead code detection | T0 (VERIFIED) |
| Dependency Audit | Vulnerability info | T1 (TOOL_OUTPUT) |

### Dynamic Analysis Sources

| Source | What It Provides | Trust Level |
|--------|------------------|-------------|
| Unit Tests | Passing/failing assertions | T0 (VERIFIED) |
| Integration Tests | Cross-component behavior | T0 (VERIFIED) |
| E2E Tests (Playwright) | User flow verification | T0 (VERIFIED) |
| UI No-Op Detector | Button effect verification | T0 (VERIFIED) |
| Coverage Report | Executed lines/branches | T0 (VERIFIED) |
| Network HAR | Actual API calls | T0 (VERIFIED) |

### Runtime Sources

| Source | What It Provides | Trust Level |
|--------|------------------|-------------|
| Application logs | Execution evidence | T1 (TOOL_OUTPUT) |
| Error tracking | Crash/exception data | T1 (TOOL_OUTPUT) |
| APM traces | Request flow | T1 (TOOL_OUTPUT) |
| Database queries | Data access patterns | T0 (VERIFIED) |

---

## Contradiction Types

### Type 1: Static OK, Dynamic Fails

**Scenario:**
```
- Linter: ✓ No errors
- Type checker: ✓ No errors
- Tests: ✓ All pass
- UI click: ✗ No effect observed
```

**Resolution:** Dynamic evidence wins (P3 > P5)

**Finding:**
```json
{
  "contradiction_type": "STATIC_OK_DYNAMIC_FAILS",
  "feature": "Save Settings button",
  "static_evidence": {
    "linter": "PASS",
    "type_check": "PASS",
    "tests": "PASS"
  },
  "dynamic_evidence": {
    "ui_verification": "NO_OP",
    "network_requests": [],
    "state_changes": []
  },
  "resolution": "FEATURE_INCOMPLETE",
  "confidence": 0.85,
  "explanation": "All static analysis passes, but runtime testing shows the button produces no observable effect. Static analysis is insufficient to prove feature completeness."
}
```

### Type 2: Tests Pass, Coverage Low

**Scenario:**
```
- Tests: ✓ All 50 tests pass
- Coverage: 23% line coverage
```

**Resolution:** Tests are testing the wrong things

**Finding:**
```json
{
  "contradiction_type": "TESTS_PASS_COVERAGE_LOW",
  "feature": "Authentication module",
  "test_evidence": {
    "tests_run": 50,
    "tests_passed": 50,
    "tests_failed": 0
  },
  "coverage_evidence": {
    "line_coverage": 0.23,
    "branch_coverage": 0.15,
    "uncovered_files": [
      "src/auth/login.ts",
      "src/auth/logout.ts",
      "src/auth/refresh.ts"
    ]
  },
  "resolution": "TESTS_INSUFFICIENT",
  "confidence": 0.90,
  "explanation": "Tests pass but only cover 23% of code. Critical authentication paths are untested."
}
```

### Type 3: Code Exists, Never Executed

**Scenario:**
```
- Route defined: ✓ /api/admin
- Reachability: ✓ Handler is reachable
- Coverage: ✗ 0% coverage on handler
- Access logs: ✗ No requests to /api/admin
```

**Resolution:** Feature exists but is never used

**Finding:**
```json
{
  "contradiction_type": "EXISTS_NEVER_EXECUTED",
  "feature": "Admin API endpoint",
  "static_evidence": {
    "route_defined": true,
    "reachable": true
  },
  "runtime_evidence": {
    "coverage": 0.0,
    "request_count": 0
  },
  "resolution": "FEATURE_UNUSED",
  "confidence": 0.75,
  "explanation": "Admin endpoint is defined and reachable but has never been executed. Either dead code or missing integration."
}
```

### Type 4: Type Says OK, Runtime Crashes

**Scenario:**
```
- Type check: ✓ No errors
- Runtime: ✗ TypeError at line 45
```

**Resolution:** Types are lying (likely `as any` or type assertion)

**Finding:**
```json
{
  "contradiction_type": "TYPES_LIE",
  "location": "src/api/handler.ts:45",
  "type_evidence": {
    "type_check": "PASS",
    "has_any_cast": true,
    "cast_location": "src/api/handler.ts:42"
  },
  "runtime_evidence": {
    "error": "TypeError: Cannot read property 'id' of undefined",
    "stack_trace": "..."
  },
  "resolution": "RUNTIME_TYPE_ERROR",
  "confidence": 0.95,
  "explanation": "Type system shows no errors, but runtime throws TypeError. Found `as any` cast at line 42 that masks the type error."
}
```

### Type 5: Security Scan Clean, Vuln Exists

**Scenario:**
```
- SAST: ✓ No vulnerabilities
- Dependency audit: ✓ No known CVEs
- Manual review: ✗ SQL injection found
```

**Resolution:** SAST has blindspots

**Finding:**
```json
{
  "contradiction_type": "SAST_BLINDSPOT",
  "location": "src/db/queries.py:78",
  "static_evidence": {
    "sast_result": "CLEAN",
    "dependency_audit": "CLEAN"
  },
  "manual_evidence": {
    "finding": "SQL injection via string concatenation",
    "code": "f\"SELECT * FROM users WHERE name = '{user_input}'\"",
    "sast_missed_because": "Dynamic string not recognized as SQL"
  },
  "resolution": "SECURITY_VULNERABILITY",
  "confidence": 0.99,
  "explanation": "SAST tools missed SQL injection because query is built with f-string, not a known SQL builder pattern."
}
```

---

## Evidence Priority Rules

### Rule 1: Runtime > Static

```
IF static_analysis.result == "OK" AND runtime.result == "FAIL"
THEN trust runtime
BECAUSE runtime is ground truth, static is prediction
```

### Rule 2: Verified > Tool Output

```
IF verified_evidence.result != tool_output.result
THEN trust verified_evidence
BECAUSE verified has reproducible proof, tool may have bugs
```

### Rule 3: Specific > General

```
IF file_level.result != line_level.result
THEN trust line_level
BECAUSE line-level is more precise
```

### Rule 4: Recent > Stale

```
IF evidence.age > 7 days
THEN mark as STALE, require re-verification
BECAUSE code may have changed
```

### Rule 5: Conservative Resolution

```
IF evidence_1.result == "OK" AND evidence_2.result == "FAIL"
THEN result = "FAIL" (with contradiction noted)
BECAUSE false negatives are worse than false positives
```

---

## Confidence Computation

### Formula

```python
def compute_feature_confidence(feature: Feature, evidence: List[Evidence]) -> float:
    """
    Compute confidence score for a feature's completeness.

    Formula:
    confidence = (
        static_confidence * 0.30 +
        dynamic_confidence * 0.40 +
        coverage_factor * 0.20 +
        contradiction_penalty * 0.10
    )
    """
    static_confidence = compute_static_confidence(evidence)
    dynamic_confidence = compute_dynamic_confidence(evidence)
    coverage_factor = compute_coverage_factor(evidence)
    contradiction_penalty = compute_contradiction_penalty(evidence)

    confidence = (
        static_confidence * 0.30 +
        dynamic_confidence * 0.40 +
        coverage_factor * 0.20 +
        (1.0 - contradiction_penalty) * 0.10
    )

    return min(confidence, 1.0)
```

### Static Confidence

```python
def compute_static_confidence(evidence: List[Evidence]) -> float:
    """
    Confidence from static analysis.

    Weight by proof level:
    - P1 (STATIC_COMPLETE): 1.0
    - P2 (STATIC_PARTIAL): 0.8
    - P5 (HEURISTIC): 0.5
    """
    weights = {"P1": 1.0, "P2": 0.8, "P5": 0.5}
    static_evidence = [e for e in evidence if e.is_static]

    if not static_evidence:
        return 0.0

    weighted_sum = sum(weights.get(e.proof_level, 0.3) for e in static_evidence if e.passed)
    total_weight = sum(weights.get(e.proof_level, 0.3) for e in static_evidence)

    return weighted_sum / total_weight if total_weight > 0 else 0.0
```

### Dynamic Confidence

```python
def compute_dynamic_confidence(evidence: List[Evidence]) -> float:
    """
    Confidence from runtime verification.

    Dynamic evidence is gold standard:
    - P3 (DYNAMIC_VERIFIED): 1.0
    - P4 (DYNAMIC_SAMPLED): 0.7
    """
    dynamic_evidence = [e for e in evidence if e.is_dynamic]

    if not dynamic_evidence:
        return 0.5  # No dynamic evidence = uncertain

    passed = sum(1 for e in dynamic_evidence if e.passed)
    return passed / len(dynamic_evidence)
```

### Coverage Factor

```python
def compute_coverage_factor(evidence: List[Evidence]) -> float:
    """
    Factor based on code coverage.

    Coverage thresholds:
    - 80%+ line coverage: 1.0
    - 60-80%: 0.8
    - 40-60%: 0.5
    - <40%: 0.3
    """
    coverage_evidence = [e for e in evidence if e.type == "COVERAGE"]

    if not coverage_evidence:
        return 0.5

    coverage = coverage_evidence[0].line_coverage

    if coverage >= 0.80:
        return 1.0
    elif coverage >= 0.60:
        return 0.8
    elif coverage >= 0.40:
        return 0.5
    else:
        return 0.3
```

### Contradiction Penalty

```python
def compute_contradiction_penalty(evidence: List[Evidence]) -> float:
    """
    Penalty for contradicting evidence.

    Each contradiction reduces confidence.
    """
    contradictions = find_contradictions(evidence)

    if not contradictions:
        return 0.0

    # Each contradiction adds 0.15 penalty, max 0.6
    return min(len(contradictions) * 0.15, 0.6)
```

---

## Output Schema

### Correlation Report

```json
{
  "repo_path": "/path/to/repo",
  "analysis_timestamp": "2024-01-18T12:00:00Z",
  "evidence_sources": {
    "static": ["linter", "type_checker", "sast", "reachability"],
    "dynamic": ["unit_tests", "e2e_tests", "ui_verification"],
    "runtime": ["coverage"]
  },
  "features_analyzed": 25,
  "results": {
    "working": 18,
    "partial": 4,
    "broken": 2,
    "unknown": 1
  },
  "contradictions_found": 3,
  "contradictions": [
    {
      "type": "STATIC_OK_DYNAMIC_FAILS",
      "feature": "Save Settings",
      "resolution": "FEATURE_INCOMPLETE",
      "confidence": 0.85
    }
  ],
  "overall_confidence": 0.72,
  "recommendation": "2 features require immediate attention due to contradicting evidence"
}
```

---

## Temporal Truth

### Evidence Staleness

| Evidence Type | Staleness Threshold | Action |
|---------------|---------------------|--------|
| Static analysis | 7 days | Re-run if code changed |
| Unit tests | Code change | Re-run on change |
| E2E tests | 24 hours | Re-run daily |
| Coverage | Code change | Re-run on change |
| UI verification | 24 hours | Re-run daily |

### Time-Based Confidence Decay

```python
def apply_staleness_decay(confidence: float, evidence_age_days: float) -> float:
    """
    Confidence decays over time.

    Decay formula: confidence * (0.95 ^ days)
    After 7 days, confidence is ~70% of original
    After 14 days, confidence is ~50% of original
    """
    decay_factor = 0.95 ** evidence_age_days
    return confidence * decay_factor
```

---

## Limitations (MANDATORY)

### What This Engine CANNOT Do

1. **Resolve all contradictions automatically**
   - Some require human judgment
   - Flagged for review, not auto-resolved

2. **Verify external system effects**
   - Can't verify email sent
   - Can't verify payment processed

3. **Handle flaky tests**
   - Inconsistent test results
   - Need multiple runs to detect

4. **Correlate across long time spans**
   - Evidence from weeks ago is stale
   - Time-based correlation limited

5. **Weight evidence perfectly**
   - Weights are heuristic
   - May need tuning per project

### What MUST Be Labeled UNKNOWN

- Features with no dynamic evidence: `UNKNOWN (runtime not verified)`
- Features with 100% contradicting evidence: `UNKNOWN (conflicting evidence)`
- Features with stale evidence (>14 days): `UNKNOWN (evidence stale)`
- Features with only P5+ evidence: `UNKNOWN (heuristic only)`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial specification |
