# Language Truth Profile: Dockerfile

**Profile Version:** 1.0.0
**Language Version:** Dockerfile syntax 1.4+
**Stack Tier:** 3 (Infrastructure)
**Profile Completeness:** 0.75
**Implementation Completeness:** 0.00

---

## Overview

Dockerfiles define container images for deployment. In the user's 589+ repos, Dockerfiles appear in:
- Application deployments
- Development environments
- CI/CD build steps
- Game server containers

Dockerfile verification focuses on **instruction validity**, **base image verification**, **unreachable instructions**, and **hadolint integration**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `Dockerfile` | Filename | Docker image definition |
| `Dockerfile.*` | Glob | Variant Dockerfiles |
| `*.dockerfile` | Extension | Alternative naming |
| `docker-compose.yml` | Filename | Compose (related) |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-dockerfile |
| Grammar Version | 0.1.0 |
| Syntax Accuracy | 0.95 |
| Semantic Accuracy | 0.70 |

### Known Parse Failures

1. **Build args in FROM**: `FROM ${BASE_IMAGE}` dynamic
2. **Multi-stage references**: Complex stage dependencies
3. **Shell form commands**: RUN without exec form

---

## Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Build args | incomplete | high | Arg tracking |
| Multi-stage | incomplete | medium | Stage graph |
| Base image content | impossible | critical | Image inspection |
| Runtime behavior | impossible | critical | Container test |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level |
|----------|--------|-------------|-------------|
| hadolint_report | sarif | P2 | T1 |
| instruction_list | json | P1 | T0 |
| stage_graph | json | P2 | T0 |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Build args | Dynamic values | Build-time | Arg inventory |
| 2 | Base image | Image contents | External | Image scan |

### Category: Runtime
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Container runtime | Actual execution | Different from build | Container test |
| 2 | Network | External downloads | Flaky | Offline test |

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "Image builds successfully" | Needs actual build | Build output |
| "Container runs correctly" | Runtime different | Container test |
| "No vulnerabilities" | Base image dependent | Image scan |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Unreachable Instruction

**Purpose:** Tests detection of instructions after final FROM

**File:** `fixtures/dockerfile/unreachable-instruction/`

### Fixture 2: Missing Entrypoint

**Purpose:** Tests detection of no CMD/ENTRYPOINT

**File:** `fixtures/dockerfile/missing-entrypoint/`

---

## HONESTY CHECK

- Claims made: 10
- Claims proven: 0
- Claims unproven: 10
- Forbidden claims listed: YES
- Fixtures defined: YES
- Goldens defined: YES

**STATUS: UNPROVEN - No Dockerfile analyzer implemented**
