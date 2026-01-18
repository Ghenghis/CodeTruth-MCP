# CodeTruth-MCP

**The Evidence-Based Code Auditing MCP Server**

> "No claims without proof" - Every finding backed by verifiable evidence

CodeTruth-MCP is a comprehensive Model Context Protocol (MCP) server that performs exhaustive, evidence-based code audits. It systematically discovers everything wrong with a codebase and provides irrefutable proof for each finding.

## Core Philosophy

Traditional code review focuses on correctness of what's present. CodeTruth focuses on **completeness verification**:
- Does the feature exist end-to-end?
- Is it reachable from entry points?
- Does it actually do something observable?
- Can we prove it with tests/logs/traces?

**A feature is only "complete" if:**
1. It's reachable from UI/entrypoints
2. It performs observable side-effects
3. It has tests (or reproducible verification steps)
4. It passes CI gates
5. It has no critical lint/type/security blockers

Everything else is "implemented but unverified" or "stubbed/unwired".

## 30 Milestone Features

### Infrastructure (1-4)
1. **Core MCP Server** - STDIO/SSE transport, tool routing, policy enforcement
2. **Evidence Vault** - SQLite + SARIF storage for all audit findings with proof
3. **Multi-language AST Parsing** - tree-sitter support for 160+ languages
4. **Reachability Analysis** - Call graph generation and dead path detection

### Static Analysis (5-12)
5. **Dead Code Detection** - Unreachable functions, unused exports, orphan components
6. **UI Wiring Audit** - Dead buttons, unbound handlers, missing routes
7. **API Contract Validation** - OpenAPI/JSON Schema/Zod compliance
8. **Secret Scanning** - gitleaks/trufflehog integration for credential detection
9. **Dependency Vulnerability Scanning** - npm audit, pip-audit, trivy, OSV
10. **Multi-language Linting** - eslint, ruff, prettier, clippy orchestration
11. **Type Checking** - tsc, mypy, pyright verification
12. **SAST Integration** - semgrep, CodeQL security scanning

### Runtime Verification (13-16)
13. **Playwright E2E Testing** - Automated UI flow verification with trace capture
14. **Visual Regression Testing** - Screenshot comparison and semantic diffing
15. **Code Coverage Analysis** - Istanbul/nyc, coverage.py integration
16. **Trace ID Correlation** - Request tracing from UI to DB

### AI & Storage (17-18)
17. **Mem0 AI Memory** - Persistent audit context across sessions
18. **Supabase Local Storage** - Self-hosted audit data persistence

### Execution Environment (19-21)
19. **Docker Sandbox** - Isolated, reproducible analysis environment
20. **Quality Gate Ladder** - 7-tier verification system (Gate 0-6)
21. **Multi-Agent Orchestration** - Specialized audit agents with cross-checks

### Reporting & Tracking (22-24)
22. **Fix Plan Generator** - Acceptance test-driven remediation plans
23. **Feature Truth Table** - Status tracking for every feature surface
24. **Feature Registry** - Spec source to implementation mapping

### Language Specialization (25-27)
25. **HTML/Web Auditing** - Accessibility, SEO, performance analysis
26. **React/TypeScript Auditing** - Hook rules, component lifecycle, type safety
27. **Python Auditing** - Import analysis, async patterns, type hints

### Platform (28-30)
28. **Offline-First Architecture** - Local AI models, no network required
29. **Real-time Dashboard** - Web UI for audit monitoring
30. **CI/CD Integration** - GitHub Actions, GitLab CI support

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ (for JavaScript/TypeScript analysis)
- Docker (for sandboxed execution)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/CodeTruth-MCP.git
cd CodeTruth-MCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Initialize the database
codetruth init

# Run the MCP server
codetruth serve
```

### Docker Installation

```bash
docker build -t codetruth-mcp .
docker run -v /path/to/repos:/repos codetruth-mcp audit /repos/my-project
```

## Usage

### As MCP Server (Claude Desktop, VS Code, etc.)

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "codetruth": {
      "command": "codetruth",
      "args": ["serve"],
      "env": {
        "CODETRUTH_DB_PATH": "~/.codetruth/evidence.db"
      }
    }
  }
}
```

### CLI Usage

```bash
# Full audit of a repository
codetruth audit /path/to/repo

# Quick scan (static only)
codetruth audit /path/to/repo --profile fast

# Deep forensics (includes E2E)
codetruth audit /path/to/repo --profile forensics

# Generate Feature Truth Table
codetruth truth-table /path/to/repo

# Run specific analyzers
codetruth analyze /path/to/repo --analyzers lint,types,security
```

## MCP Tools

CodeTruth exposes the following MCP tools:

| Tool | Description |
|------|-------------|
| `discover_repos` | Scan directories for repositories |
| `inventory` | Generate repo inventory (languages, packages, entrypoints) |
| `run_gates` | Execute quality gate ladder |
| `ui_wiring_audit` | Detect dead UI elements |
| `api_contract_audit` | Validate API contracts |
| `reachability_graph` | Build call graph, find dead code |
| `run_e2e` | Execute Playwright tests with tracing |
| `generate_truth_table` | Create Feature Truth Table |
| `create_fix_plan` | Generate remediation plan |
| `search_evidence` | Query the evidence vault |

## Quality Gate Ladder

| Gate | Name | Checks |
|------|------|--------|
| 0 | Build & Boot | Install, start, health endpoint |
| 1 | Lint/Type | eslint, ruff, tsc, mypy |
| 2 | Unit Tests | Core module coverage |
| 3 | Contract Tests | API schema validation |
| 4 | Integration/E2E | Playwright click flows |
| 5 | Security | SAST, secrets, dependencies |
| 6 | Release | Reproducible build, docs |

## Feature Truth Table

For every discovered feature surface:

| Column | Description |
|--------|-------------|
| Feature | Name/identifier |
| Spec Source | Where it's defined |
| Execution Path | UI → API → Service → DB |
| Reachable | Is code path reachable? |
| Observable | Network/state/DB effects? |
| Tested | Test name + assertions |
| Status | Working/Partial/Stubbed/Unwired/Dead/Broken |
| Blockers | Why it's not complete |

### Status Categories

- **WORKING** - Fully functional, tested, gates pass
- **PARTIAL** - Some steps work, others fail
- **STUBBED** - Placeholder/TODO/mock return
- **UNWIRED** - UI exists but no handler/route not registered
- **DEAD** - Unreachable code
- **BROKEN** - Throws/fails tests

## Failure Mode Catalog

CodeTruth detects these common "looks finished but isn't" patterns:

1. UI element exists but no handler bound (dead button)
2. Handler exists but not reachable (not routed/exported)
3. API route defined but not registered
4. Backend returns success but doesn't persist
5. Feature depends on undocumented env/config
6. TODO paths, placeholder returns, hardcoded mocks
7. Async queues not running / no worker
8. Auth/permissions block flow silently
9. Race conditions / state never updates UI
10. Types drift / contract mismatch

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    MCP Host (Claude/VS Code)                  │
└─────────────────────────────┬────────────────────────────────┘
                              │ MCP JSON-RPC
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              CodeTruth MCP Server                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Tool Router + Policy Engine ("no claim without proof") │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────┬──────────────────────────────────────┬────────────┘
           │                                      │
           ▼                                      ▼
┌────────────────────┐              ┌─────────────────────────┐
│   Repo Loader      │              │    Evidence Vault       │
│  - Local clones    │◄────────────►│  - SQLite + SARIF       │
│  - Inventory       │              │  - Traces, snapshots    │
│  - AST parsing     │              │  - Mem0 context         │
└─────────┬──────────┘              └────────────┬────────────┘
          │                                      │
          ▼                                      ▼
┌──────────────────────────────────────────────────────────────┐
│                 Analyzer Orchestrator                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Static   │ │ Runtime  │ │ Security │ │ Language-Specific│ │
│  │ Analyzers│ │ Analyzers│ │ Scanners │ │ Analyzers        │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Report Generator                           │
│  - Feature Truth Table    - Fix Plans with acceptance tests   │
│  - SARIF reports          - CI/CD gate results                │
│  - Evidence citations     - Trace correlations                │
└──────────────────────────────────────────────────────────────┘
```

## Configuration

Create `codetruth.toml` in your repo root:

```toml
[codetruth]
# Analysis profile: fast, standard, deep, forensics
profile = "standard"

[codetruth.gates]
# Which gates to run
enabled = [0, 1, 2, 3, 4, 5]

[codetruth.analyzers]
# Language-specific settings
python.enabled = true
python.type_checker = "mypy"

typescript.enabled = true
typescript.strict = true

[codetruth.e2e]
# Playwright settings
browser = "chromium"
trace = "on-first-retry"
video = "retain-on-failure"

[codetruth.security]
# Secret scanning
gitleaks.enabled = true
semgrep.enabled = true
semgrep.rulesets = ["p/default", "p/owasp-top-ten"]
```

## Research Foundation

CodeTruth is built on research from:

- [ReachCheck: Compositional Library-Aware Call Graph Reachability Analysis](https://dl.acm.org/doi/10.1145/3767166) (ACM TOSEM 2025)
- [Insights from Running 24 Static Analysis Tools](https://purs3lab.github.io/files/sastiss.pdf)
- [LLM-based Agents Suffer from Hallucinations](https://arxiv.org/html/2509.18970v1) - Evidence-based mitigation
- [SARIF 2.1.0 Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
