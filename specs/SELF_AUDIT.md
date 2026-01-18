# Self-Audit: Anti-Hallucination Core

**Version:** 1.0.0
**Status:** AUTHORITATIVE

---

## Purpose

This document defines what CodeTruth CANNOT verify, when it MUST refuse to answer, and how it audits itself. This is what makes CodeTruth trustworthy rather than just confident.

> **A system that can't admit its limits will lie about its capabilities.**

---

## What CodeTruth CANNOT Verify

### Category: Fundamentally Unprovable

| Claim | Why Unprovable | What To Do Instead |
|-------|----------------|---------------------|
| "Code is correct" | Halting problem | Verify specific properties |
| "No bugs exist" | Requires proving a negative | Report found bugs, declare coverage |
| "Feature is complete" | Unbounded scope | Define completion criteria, verify against them |
| "Security is guaranteed" | Unknown unknowns | Report found vulnerabilities, declare scan coverage |
| "Will work in production" | Environment differs | Test in production-like environment |
| "User intent is met" | Cannot read minds | Require written specifications |

### Category: Dynamic Behavior

| Claim | Why Unprovable | What To Do Instead |
|-------|----------------|---------------------|
| Dynamic dispatch result | Runtime-determined | Mark as HEURISTIC (P5) |
| eval/exec contents | Arbitrary code | Mark as UNPROVEN |
| Reflection targets | Runtime-determined | Mark as UNPROVEN |
| Feature flag outcomes | Configuration-dependent | Test all configurations |
| Race condition absence | Non-deterministic | Mark as UNPROVEN |
| Memory leak absence | Requires exhaustive testing | Report found leaks |

### Category: External Dependencies

| Claim | Why Unprovable | What To Do Instead |
|-------|----------------|---------------------|
| External API behavior | Not our code | Contract testing only |
| Database state | Changes independently | Snapshot testing |
| User input effects | Infinite inputs | Boundary testing |
| Network reliability | External factor | Timeout/retry testing |
| Third-party library correctness | Not our code | Dependency audit only |

### Category: Beyond Scope

| Claim | Why Unprovable | What To Do Instead |
|-------|----------------|---------------------|
| Business logic correctness | Domain knowledge required | Verify against specs |
| UX quality | Subjective | Verify against specs |
| Performance adequacy | Context-dependent | Report metrics, let humans decide |
| Maintainability | Subjective | Report metrics, let humans decide |
| Legal compliance | Not qualified | Flag for legal review |

---

## When CodeTruth MUST Say "UNKNOWN"

### Rule 1: No Evidence

```
IF finding.evidence == EMPTY
THEN finding.status = "UNKNOWN"
     finding.reason = "No evidence available"
```

### Rule 2: Only Heuristic Evidence

```
IF finding.evidence.all(e => e.proof_level >= P5)
THEN finding.status = "UNKNOWN"
     finding.reason = "Only heuristic evidence available"
```

### Rule 3: Contradicting Evidence

```
IF finding.has_contradicting_evidence()
AND NOT finding.contradiction_resolved()
THEN finding.status = "UNKNOWN"
     finding.reason = "Contradicting evidence, requires human review"
```

### Rule 4: Stale Evidence

```
IF finding.evidence.all(e => e.is_expired())
THEN finding.status = "UNKNOWN"
     finding.reason = "All evidence is stale"
```

### Rule 5: Unsupported Language

```
IF file.language NOT IN supported_languages
THEN finding.status = "UNKNOWN"
     finding.reason = f"Language '{file.language}' not supported"
```

### Rule 6: Dynamic Pattern

```
IF code.contains(DYNAMIC_PATTERNS)
THEN finding.confidence = MIN(finding.confidence, 0.50)
     finding.note = "Contains dynamic patterns, limited static analysis"

DYNAMIC_PATTERNS = [
    "eval(", "exec(", "new Function(",
    "getattr(", "Reflect.", "Type.GetMethod(",
    "import(", "require(variable)",
    "__getattr__", "__call__",
]
```

---

## When CodeTruth MUST Refuse

### Refusing to Claim Completeness

```python
def can_claim_complete(feature: Feature) -> tuple[bool, str]:
    """
    Check if we can claim a feature is complete.

    We CANNOT claim complete if:
    1. No dynamic verification exists
    2. Coverage < 80%
    3. Any critical blindspot applies
    4. Evidence is stale
    5. Contains UNKNOWN sub-findings
    """
    if not feature.has_dynamic_evidence():
        return False, "No runtime verification"

    if feature.coverage < 0.80:
        return False, f"Coverage {feature.coverage:.0%} < 80%"

    blindspots = feature.get_applicable_blindspots()
    if any(b.severity == "CRITICAL" for b in blindspots):
        return False, "Critical blindspot applies"

    if feature.evidence_is_stale():
        return False, "Evidence is stale"

    if feature.has_unknown_subfindings():
        return False, "Contains UNKNOWN sub-findings"

    return True, "All checks passed"
```

### Refusing to Claim Security

```python
def can_claim_secure(component: Component) -> tuple[bool, str]:
    """
    We NEVER claim "secure". We only claim:
    - "No known vulnerabilities found"
    - "Passed security scan with tools X, Y, Z"
    """
    return False, "CodeTruth does not make security guarantees"
```

### Refusing Invalid Requests

```python
REFUSED_REQUESTS = [
    "prove this code has no bugs",
    "guarantee this works",
    "certify this is production-ready",
    "confirm this is complete",
    "verify this is secure",
    "ensure this is correct",
]
```

---

## How CodeTruth Audits Itself

### Self-Audit Checks

#### Check 1: Capability Coverage

```python
def audit_capability_coverage():
    """
    Verify CAPABILITIES.md matches actual implementation.
    """
    declared = load_capabilities_md()
    implemented = scan_implementation()

    for capability in declared:
        if capability.status == "FULL":
            if not implemented.has(capability.name):
                FAIL(f"Declared FULL but not implemented: {capability.name}")

        if capability.status == "PARTIAL":
            if implemented.is_complete(capability.name):
                WARN(f"Declared PARTIAL but appears complete: {capability.name}")
```

#### Check 2: Profile Completeness

```python
def audit_profile_completeness():
    """
    Verify all language profiles have required sections.
    """
    required_sections = [
        "File Identification",
        "Parse Capability",
        "Semantic Capability",
        "Wiring Capability",
        "Runtime Capability",
        "Evidence Artifacts",
        "Critical Blindspots",  # MUST have blindspots!
    ]

    for profile in load_all_profiles():
        for section in required_sections:
            if section not in profile.sections:
                FAIL(f"Profile {profile.name} missing section: {section}")

        if len(profile.blindspots) == 0:
            FAIL(f"Profile {profile.name} declares no blindspots - impossible!")
```

#### Check 3: Fixture Pass Rate

```python
def audit_fixture_detection():
    """
    Run all fixtures and verify detection.
    """
    for fixture in load_all_fixtures():
        result = run_codetruth_on(fixture.path)

        for expected_finding in fixture.expected_findings:
            if not result.contains_finding(expected_finding):
                FAIL(f"Fixture {fixture.name}: Missing expected finding {expected_finding.type}")

        if result.confidence < fixture.min_confidence:
            FAIL(f"Fixture {fixture.name}: Confidence {result.confidence} < {fixture.min_confidence}")
```

#### Check 4: Evidence Integrity

```python
def audit_evidence_integrity():
    """
    Verify all stored evidence passes integrity checks.
    """
    for evidence in load_all_evidence():
        # Check hash
        computed_hash = compute_hash(evidence.content)
        if computed_hash != evidence.integrity.hash:
            FAIL(f"Evidence {evidence.id}: Hash mismatch")

        # Check reproducibility
        if evidence.trust_level == "T0":
            if not evidence.reproducibility.is_reproducible:
                FAIL(f"Evidence {evidence.id}: T0 evidence must be reproducible")

            reproduction = reproduce(evidence)
            if reproduction.hash != evidence.integrity.hash:
                WARN(f"Evidence {evidence.id}: Reproduction differs from stored")
```

#### Check 5: No False Claims

```python
def audit_no_false_claims():
    """
    Verify reports don't contain forbidden claims.
    """
    forbidden_phrases = [
        "guaranteed",
        "100% complete",
        "fully secure",
        "no bugs",
        "production ready",  # We don't certify production readiness
        "certified",
    ]

    for report in load_all_reports():
        for phrase in forbidden_phrases:
            if phrase.lower() in report.content.lower():
                FAIL(f"Report contains forbidden phrase: '{phrase}'")
```

---

## Confidence Degradation

### Time-Based Decay

```python
def decay_confidence(finding: Finding, current_time: datetime) -> float:
    """
    Confidence decays over time.

    Formula: confidence * (0.95 ^ days_since_evidence)

    After 7 days: ~70% of original
    After 14 days: ~50% of original
    After 30 days: ~20% of original
    """
    newest_evidence = max(finding.evidence, key=lambda e: e.timestamp)
    days = (current_time - newest_evidence.timestamp).days

    decay = 0.95 ** days
    return finding.confidence * decay
```

### Code Change Invalidation

```python
def invalidate_on_change(finding: Finding, changed_files: set[Path]) -> bool:
    """
    Invalidate finding if relevant code changed.
    """
    finding_files = finding.get_relevant_files()

    if finding_files & changed_files:
        finding.status = "STALE"
        finding.note = "Code changed since analysis"
        return True

    return False
```

### Dependency Change Invalidation

```python
def invalidate_on_dep_change(finding: Finding, changed_deps: set[str]) -> bool:
    """
    Invalidate finding if dependencies changed.
    """
    finding_deps = finding.get_relevant_dependencies()

    if finding_deps & changed_deps:
        finding.status = "STALE"
        finding.note = "Dependencies changed since analysis"
        return True

    return False
```

---

## Contradiction Detection

### Detection Rules

```python
def detect_contradictions(findings: list[Finding]) -> list[Contradiction]:
    """
    Find contradictions in findings.
    """
    contradictions = []

    # Rule 1: Static OK + Dynamic Fail
    for f in findings:
        if f.static_status == "OK" and f.dynamic_status == "FAIL":
            contradictions.append(Contradiction(
                type="STATIC_DYNAMIC_MISMATCH",
                finding=f,
                resolution="Dynamic evidence takes priority"
            ))

    # Rule 2: Tests Pass + No Coverage
    for f in findings:
        if f.tests_pass and f.coverage == 0:
            contradictions.append(Contradiction(
                type="TESTS_PASS_NO_COVERAGE",
                finding=f,
                resolution="Tests may not cover this code"
            ))

    # Rule 3: Reachable + Never Executed
    for f in findings:
        if f.is_reachable and f.execution_count == 0:
            contradictions.append(Contradiction(
                type="REACHABLE_NEVER_RUN",
                finding=f,
                resolution="Code exists but never reached in tests"
            ))

    return contradictions
```

---

## Self-Audit Report Format

```json
{
  "self_audit_timestamp": "2024-01-18T12:00:00Z",
  "codetruth_version": "1.0.0",
  "checks_run": 5,
  "checks_passed": 4,
  "checks_failed": 1,
  "checks_warned": 2,
  "results": [
    {
      "check": "capability_coverage",
      "status": "PASS",
      "details": "All 25 capabilities match implementation"
    },
    {
      "check": "profile_completeness",
      "status": "PASS",
      "details": "All 15 profiles have required sections"
    },
    {
      "check": "fixture_detection",
      "status": "FAIL",
      "details": "Fixture 'stub-hell' not fully detected",
      "expected": 4,
      "actual": 3
    },
    {
      "check": "evidence_integrity",
      "status": "WARN",
      "details": "3 evidence items could not be reproduced"
    },
    {
      "check": "no_false_claims",
      "status": "PASS",
      "details": "No forbidden phrases found"
    }
  ],
  "overall_trustworthiness": 0.80,
  "recommendation": "Fix fixture detection before claiming production readiness"
}
```

---

## Self-Check Checklist

This section MUST be updated with every release:

```
SELF-CHECK (v1.0.0):
[x] No TODOs in specification documents
[x] No placeholders in profiles
[x] No future promises in capabilities
[x] All capabilities tied to evidence
[x] Blindspots declared for all profiles
[x] 10+ fixtures included
[x] Golden outputs defined for all fixtures
[x] Confidence math is explicit
[ ] All fixtures pass (PENDING: 9/10 passing)
[ ] Self-audit passes all checks (PENDING: 4/5 passing)
```

**Current Status:** This specification is NOT YET complete.

**Remaining Work:**
1. Fix fixture 'stub-hell' detection
2. Fix evidence reproduction for 3 items
3. Re-run self-audit after fixes

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial specification |
