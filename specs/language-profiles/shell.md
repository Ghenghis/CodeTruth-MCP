# Language Truth Profile: Shell/Bash

**Profile Version:** 1.0.0
**Language Version:** Bash 4.0+, POSIX sh
**Stack Tier:** 3 (Infrastructure/Automation)
**Profile Completeness:** 0.75
**Implementation Completeness:** 0.00

---

## Overview

Shell scripts automate system tasks, CI/CD pipelines, and deployment. In the user's 589+ repos, shell appears in:
- Build scripts (build.sh, deploy.sh)
- CI/CD workflows (GitHub Actions, GitLab CI)
- Docker entrypoints
- Installation scripts
- Game server launchers

Shell verification focuses on **syntax validity**, **undefined variables**, **unreachable code**, and **shellcheck integration**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.sh` | Extension | Shell scripts |
| `*.bash` | Extension | Bash scripts |
| `Makefile` | Filename | Make recipes (shell) |
| `.bashrc` | Filename | Bash config |
| `.zshrc` | Filename | Zsh config |
| `entrypoint.sh` | Filename | Docker entrypoint |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-bash |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.90 |
| Semantic Accuracy | 0.60 |

### Known Parse Failures

1. **Heredocs with interpolation**: Complex variable expansion
2. **Process substitution**: `<(command)` patterns
3. **eval statements**: Dynamic code execution
4. **source/dot commands**: External file inclusion

---

## Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| eval | impossible | critical | Refuse analysis |
| source/dot | incomplete | high | File tracing |
| Environment variables | incomplete | high | env inventory |
| Subshells | incomplete | medium | Scope tracking |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level |
|----------|--------|-------------|-------------|
| shellcheck_report | sarif | P2 | T1 |
| variable_inventory | json | P2 | T0 |
| function_graph | json | P2 | T0 |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | eval | Dynamic execution | Impossible | Refuse |
| 2 | source | External includes | Path resolution | File tracking |

### Category: Runtime
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Environment | Runtime env vars | Unknown values | Env inventory |
| 2 | Exit codes | Command success | Runtime only | Test execution |

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "Script always succeeds" | Depends on runtime | Execution trace |
| "All variables defined" | Environment dependent | Full env inventory |
| "No security issues" | Complex to verify | Security audit |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Undefined Variable

**Purpose:** Tests detection of undefined variable usage

**File:** `fixtures/shell/undefined-variable/`

**Expected Findings:**
- HIGH: Variable $UNDEFINED used but never set

### Fixture 2: Unreachable Code

**Purpose:** Tests detection of code after exit

**File:** `fixtures/shell/unreachable-code/`

**Expected Findings:**
- MEDIUM: Code after unconditional exit

---

## Golden Output Expectations (MANDATORY SECTION)

See: `specs/goldens/shell-undefined-variable.json`, `specs/goldens/shell-unreachable-code.json`

---

## HONESTY CHECK

- Claims made: 12
- Claims proven: 0
- Claims unproven: 12
- Forbidden claims listed: YES
- Fixtures defined: YES
- Goldens defined: YES

**STATUS: UNPROVEN - No Shell analyzer implemented**
