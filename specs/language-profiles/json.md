# Language Truth Profile: JSON (Config)

**Profile Version:** 1.0.0
**Language Version:** JSON (RFC 8259), JSON5, JSONC
**Stack Tier:** 3 (Configuration)
**Profile Completeness:** 0.70
**Implementation Completeness:** 0.00

---

## Overview

JSON defines configuration, data exchange, and schema definitions. In the user's 589+ repos, JSON appears in:
- package.json (Node.js)
- tsconfig.json (TypeScript)
- .eslintrc.json (ESLint)
- API responses
- Game data files

JSON verification focuses on **schema validation**, **reference resolution**, **unused config detection**, and **format compliance**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.json` | Extension | JSON files |
| `*.jsonc` | Extension | JSON with comments |
| `*.json5` | Extension | JSON5 format |
| `package.json` | Filename | Node.js manifest |
| `tsconfig.json` | Filename | TypeScript config |
| `.eslintrc.json` | Filename | ESLint config |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-json |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.99 |
| Semantic Accuracy | 0.40 |

### Known Parse Failures

1. **JSONC comments**: `//, /* */` in JSON
2. **JSON5 features**: Trailing commas, unquoted keys
3. **Large numbers**: BigInt beyond JS safe integer

---

## Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Schema unknown | incomplete | high | Schema detection |
| References | incomplete | medium | Ref resolution |
| Usage context | incomplete | critical | Cross-file analysis |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level |
|----------|--------|-------------|-------------|
| parse_result | json | P1 | T0 |
| schema_validation | json | P2 | T1 |
| key_inventory | json | P1 | T0 |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Comments | JSONC/JSON5 comments | Not standard JSON | Comment-aware parser |
| 2 | Schema | Unknown schema | Context dependent | Schema inference |

### Category: Semantic
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Usage | How config is used | Cross-file | Usage tracking |
| 2 | Defaults | Missing vs default | App-specific | Schema analysis |

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "Config is complete" | Schema dependent | Schema validation |
| "All keys used" | Requires app analysis | Usage tracking |
| "Valid for runtime" | App-specific | Integration test |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Schema Violation

**Purpose:** Tests detection of invalid JSON against schema

**File:** `fixtures/json/schema-violation/`

### Fixture 2: Unused Config

**Purpose:** Tests detection of config keys never read

**File:** `fixtures/json/unused-config/`

---

## HONESTY CHECK

- Claims made: 8
- Claims proven: 0
- Claims unproven: 8
- Forbidden claims listed: YES
- Fixtures defined: YES
- Goldens defined: YES

**STATUS: UNPROVEN - No JSON analyzer implemented**
