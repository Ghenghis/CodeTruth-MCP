# Language Truth Profile: [LANGUAGE_NAME]

**Profile Version:** 1.0.0
**Language Version:** [version or "any"]
**Stack Tier:** [1-5]
**Profile Completeness:** [0.00-1.00]
**Implementation Completeness:** [0.00-1.00]

---

## Overview

[Brief description of the language/stack and its common use cases]

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.ext` | Extension | Primary file extension |
| `pattern/*` | Glob | Additional patterns |
| `filename` | Filename | Specific filenames |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | [tree_sitter / language_server / ast_native / regex / custom] |
| Parser Name | [specific parser name] |
| Grammar Version | [version or N/A] |
| Syntax Accuracy | [0.00-1.00] |
| Semantic Accuracy | [0.00-1.00] |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | [Yes/No] | [notes] |
| Error recovery | [Yes/No] | [notes] |
| Incremental parsing | [Yes/No] | [notes] |
| Comment preservation | [Yes/No] | [notes] |

### Known Parse Failures

1. [Specific syntax that fails to parse correctly]
2. [Another parse failure case]
3. [...]

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | [none / basic / full / dependent] |
| Import Resolution | [Yes/No] |
| Type Resolution | [Yes/No] |
| Mutation Tracking | [Yes/No] |
| Control Flow Analysis | [Yes/No] |
| Data Flow Analysis | [Yes/No] |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | [Yes/No] | [0.00-1.00] |
| Shadowing Detection | [Yes/No] | [0.00-1.00] |
| Closure Detection | [Yes/No] | [0.00-1.00] |
| Cross-file Resolution | [Yes/No] | [0.00-1.00] |
| Cross-module Resolution | [Yes/No] | [0.00-1.00] |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| [dynamic feature] | [false_negative/false_positive/incomplete] | [critical/high/medium/low] | [workaround] |
| [...] | [...] | [...] | [...] |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | [Yes/No] | [0.00-1.00] | [P0-P7] |
| Event Graph | [Yes/No] | [0.00-1.00] | [P0-P7] |
| Route Graph | [Yes/No] | [0.00-1.00] | [P0-P7] |
| Data Flow Graph | [Yes/No] | [0.00-1.00] | [P0-P7] |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| HTTP Calls | [Yes/No] | [P0-P7] |
| IPC | [Yes/No] | [P0-P7] |
| File I/O | [Yes/No] | [P0-P7] |
| Process Spawn | [Yes/No] | [P0-P7] |
| Database | [Yes/No] | [P0-P7] |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | [Yes/No] | [0.00-1.00] |
| Prove Unreachable | [Yes/No] | [0.00-1.00] |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| [dynamic dispatch pattern] | [impact] | [severity] | [code example] |
| [...] | [...] | [...] | [...] |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | [Yes/No] |
| Environment | [node / browser / python / etc.] |
| Min Version | [version] |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | [Yes/No] | [tool] |
| Execution Tracing | [Yes/No] | [tool] |
| Performance Profiling | [Yes/No] | [tool] |
| State Snapshots | [Yes/No] | [tool] |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | [Yes/No] | [frameworks] |
| Integration Tests | [Yes/No] | [frameworks] |
| E2E Tests | [Yes/No] | [frameworks] |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | [Yes/No] |
| Granularity | [none / line / branch / condition / mcdc] |
| Tool | [coverage tool] |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| [runtime limitation] | [impact] | [severity] | [why unprovable] |
| [...] | [...] | [...] | [...] |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| [artifact_name] | [json/sarif/etc] | [P0-P7] | [T0-T4] | [Yes/No] | [Yes/No] |
| [...] | [...] | [...] | [...] | [...] | [...] |

---

## Critical Blindspots (MANDATORY SECTION)

> Every language has blindspots. This section MUST be completed honestly.

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | [name] | [what cannot be parsed] | [why] | [workaround or "none"] |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | [name] | [what cannot be understood] | [why] | [workaround or "none"] |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | [name] | [what cannot be traced] | [why] | [workaround or "none"] |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | [name] | [what cannot be verified at runtime] | [why] | [workaround or "none"] |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| [language] | [http/ipc/ffi/file/process] | [Yes/No] | [Yes/No] | [Yes/No] | [P0-P7] |
| [...] | [...] | [...] | [...] | [...] | [...] |

### Common Boundary Patterns

```[language]
// Pattern 1: [description]
[code example]

// Pattern 2: [description]
[code example]
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| [tool] | [what it does] | [version] |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| [tool] | [what it does] | [what capability] |

---

## Failure Patterns

> Common ways this language exhibits "fake completeness"

### Pattern 1: [Name]

**Description:** [What it looks like]

**Detection:** [How CodeTruth detects it]

**Example:**
```[language]
[code that exhibits this pattern]
```

### Pattern 2: [Name]

**Description:** [What it looks like]

**Detection:** [How CodeTruth detects it]

**Example:**
```[language]
[code that exhibits this pattern]
```

---

## Forbidden Claims (MANDATORY SECTION)

> Claims that CodeTruth MUST NEVER make for this language without explicit evidence

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "All code paths verified" | [reason cannot guarantee] | [what would be needed] |
| "No dead code exists" | [reason cannot guarantee] | [what would be needed] |
| "All events handled" | [reason cannot guarantee] | [what would be needed] |
| "100% coverage means complete" | [reason misleading] | [what would be needed] |
| [additional forbidden claim] | [reason] | [evidence needed] |

---

## Required Fixtures (MANDATORY SECTION)

> Every profile MUST define at least 2 intentionally broken fixtures

### Fixture 1: [Name]

**Purpose:** [What failure pattern this tests]

**File:** `fixtures/[language]/[fixture_name]/`

**Expected Findings:**
- [Finding 1 with severity]
- [Finding 2 with severity]

**Forbidden False Positives:**
- [What should NOT be flagged]

### Fixture 2: [Name]

**Purpose:** [What failure pattern this tests]

**File:** `fixtures/[language]/[fixture_name]/`

**Expected Findings:**
- [Finding 1 with severity]
- [Finding 2 with severity]

**Forbidden False Positives:**
- [What should NOT be flagged]

---

## Golden Output Expectations (MANDATORY SECTION)

> Exact expected output for fixtures to enable regression testing

### Golden 1: [Fixture Name]

```json
{
  "findings": [
    {
      "type": "[finding_type]",
      "severity": "[critical/high/medium/low]",
      "location": "[file:line]",
      "message": "[exact message]",
      "proof_level": "[P0-P7]",
      "evidence": "[evidence reference]"
    }
  ],
  "confidence": [0.00-1.00],
  "blindspots_acknowledged": ["[blindspot1]", "[blindspot2]"]
}
```

### Golden 2: [Fixture Name]

```json
{
  "findings": [...],
  "confidence": [0.00-1.00],
  "blindspots_acknowledged": [...]
}
```

---

## Confidence Computation

For this language profile, overall confidence is computed as:

```
confidence = (
    parse_accuracy × 0.15 +
    semantic_accuracy × 0.20 +
    wiring_completeness × 0.25 +
    runtime_capability × 0.25 +
    (1 - critical_blindspot_penalty) × 0.15
)
```

**Current Score:** [X.XX]

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | [date] | Initial profile |
