# Language Truth Profile: YAML (CI/CD)

**Profile Version:** 1.0.0
**Language Version:** YAML 1.2
**Stack Tier:** 3 (Infrastructure/Configuration)
**Profile Completeness:** 0.70
**Implementation Completeness:** 0.00

---

## Overview

YAML defines CI/CD pipelines, Kubernetes manifests, and configurations. In the user's 589+ repos, YAML appears in:
- GitHub Actions workflows
- GitLab CI pipelines
- Kubernetes manifests
- Docker Compose files
- Ansible playbooks

YAML verification focuses on **schema validation**, **reference resolution**, **unreachable jobs**, and **workflow validation**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.yml` | Extension | YAML files |
| `*.yaml` | Extension | YAML files |
| `.github/workflows/*.yml` | Glob | GitHub Actions |
| `.gitlab-ci.yml` | Filename | GitLab CI |
| `docker-compose.yml` | Filename | Docker Compose |
| `k8s/*.yaml` | Glob | Kubernetes |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-yaml |
| Grammar Version | 0.5.0 |
| Syntax Accuracy | 0.98 |
| Semantic Accuracy | 0.50 |

### Known Parse Failures

1. **Anchors and aliases**: Complex reference chains
2. **Template expressions**: `${{ }}` in GitHub Actions
3. **Multi-document files**: Multiple `---` separators

---

## Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Template expressions | incomplete | critical | Expression parser |
| Schema variations | incomplete | high | Schema detection |
| Conditional jobs | incomplete | high | Condition evaluation |
| Secrets | impossible | critical | Cannot verify |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level |
|----------|--------|-------------|-------------|
| yamllint_report | sarif | P2 | T1 |
| schema_validation | json | P2 | T1 |
| job_graph | json | P2 | T0 |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Templates | `${{ }}` expressions | Different syntax | Expression parser |
| 2 | Anchors | YAML references | Complex chains | Anchor resolution |

### Category: Semantic
| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Conditions | if: expressions | Runtime evaluation | Condition parser |
| 2 | Secrets | Secret values | Cannot access | Skip verification |

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "Workflow runs successfully" | Needs actual run | Execution log |
| "All jobs reachable" | Conditions unknown | Full condition analysis |
| "No secret leaks" | Cannot verify secrets | Security scan |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Invalid Reference

**Purpose:** Tests detection of invalid job/step references

**File:** `fixtures/yaml/invalid-reference/`

### Fixture 2: Unreachable Job

**Purpose:** Tests detection of jobs with impossible conditions

**File:** `fixtures/yaml/unreachable-job/`

---

## HONESTY CHECK

- Claims made: 10
- Claims proven: 0
- Claims unproven: 10
- Forbidden claims listed: YES
- Fixtures defined: YES
- Goldens defined: YES

**STATUS: UNPROVEN - No YAML analyzer implemented**
