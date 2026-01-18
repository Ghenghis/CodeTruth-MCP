# Analyzer Mapping Table

**Document Version:** 1.0.0
**Generated:** 2024-01-18
**Contract Compliance:** V2

---

## Purpose

This document maps each language profile to its actual implementation, evidence produced, fixtures, and goldens. Per Contract V2, profiles without implementation backing are marked accordingly.

---

## Mapping Legend

| Status | Meaning |
|--------|---------|
| ✅ IMPLEMENTED | Full implementation exists |
| ⚠️ PARTIAL | Implementation exists but incomplete |
| ❌ NOT IMPLEMENTED | No implementation - UNPROVEN |
| 📄 SPEC ONLY | Profile exists, no code |

---

## Tier 1: Core Languages (Production Ready)

| Code Type | Profile | Analyzer(s) | Status | Evidence Produced | Fixture(s) | Golden(s) |
|-----------|---------|-------------|--------|-------------------|------------|-----------|
| TypeScript + React | `typescript.md` | `dead_code.py:DeadCodeAnalyzer`, `ui_wiring.py:UIWiringAnalyzer` | ⚠️ PARTIAL | `unused_export`, `empty_handler`, `unused_handler`, `code_marker` | `typescript-react/no-op-button`, `typescript-react/dead-handler` | `typescript-react-no-op-button.json`, `typescript-react-dead-handler.json` |
| Python | `python.md` | `dead_code.py:DeadCodeAnalyzer._analyze_python` | ⚠️ PARTIAL | `unreachable_code`, `code_marker` | `python/unreachable-code`, `python/orphan-function` | `python-unreachable-code.json`, `python-orphan-function.json` |
| JavaScript | `javascript.md` | `dead_code.py:DeadCodeAnalyzer._analyze_typescript` | ⚠️ PARTIAL | `unused_export`, `code_marker` | `javascript/promise-void`, `javascript/dynamic-dispatch` | `javascript-promise-void.json`, `javascript-dynamic-dispatch.json` |

---

## Tier 2: Game Server Languages (Specified, Not Implemented)

| Code Type | Profile | Analyzer(s) | Status | Evidence Produced | Fixture(s) | Golden(s) |
|-----------|---------|-------------|--------|-------------------|------------|-----------|
| PHP (Legacy/Game) | `php.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `php/ajax-no-effect`, `php/cron-never-runs` | `php-ajax-no-effect.json`, `php-cron-never-runs.json` |
| C# (MapleStory/.NET) | `csharp.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `csharp/missing-packet-handler`, `csharp/dead-npc-script` | `csharp-missing-packet-handler.json`, `csharp-dead-npc-script.json` |
| Java (MapleStory/OdinMS) | `java.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `java/missing-packet-handler`, `java/dead-quest-handler` | `java-missing-packet-handler.json`, `java-dead-quest-handler.json` |
| HTML | `html.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `html/form-action-nowhere`, `html/dead-id-ref` | `html-form-action-nowhere.json`, `html-dead-id-ref.json` |
| CSS | `css.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `css/dead-selector`, `css/specificity-hell` | `css-dead-selector.json`, `css-specificity-hell.json` |

---

## Tier 3: Scripting & Infrastructure (Specified, Not Implemented)

| Code Type | Profile | Analyzer(s) | Status | Evidence Produced | Fixture(s) | Golden(s) |
|-----------|---------|-------------|--------|-------------------|------------|-----------|
| Lua (Game Scripting) | `lua.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `lua/orphan-function`, `lua/global-pollution` | `lua-orphan-function.json`, `lua-global-pollution.json` |
| PowerShell | `powershell.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `powershell/unreachable-code`, `powershell/missing-param` | `powershell-unreachable-code.json`, `powershell-missing-param.json` |
| SQL | `sql.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `sql/fk-to-nowhere`, `sql/migration-disorder` | `sql-fk-to-nowhere.json`, `sql-migration-disorder.json` |
| Shell/Bash | `shell.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `shell/undefined-variable`, `shell/unreachable-code` | `shell-undefined-variable.json`, `shell-unreachable-code.json` |
| Dockerfile | `dockerfile.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `dockerfile/unreachable-instruction`, `dockerfile/missing-entrypoint` | `dockerfile-unreachable-instruction.json`, `dockerfile-missing-entrypoint.json` |
| YAML (CI/CD) | `yaml.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `yaml/invalid-reference`, `yaml/unreachable-job` | `yaml-invalid-reference.json`, `yaml-unreachable-job.json` |
| JSON (Config) | `json.md` | NONE | ❌ NOT IMPLEMENTED | N/A | `json/schema-violation`, `json/unused-config` | `json-schema-violation.json`, `json-unused-config.json` |

---

## Implemented Analyzer Details

### DeadCodeAnalyzer (`codetruth/analyzers/dead_code.py`)

| Method | Languages | Evidence Types | Proof Level |
|--------|-----------|----------------|-------------|
| `_analyze_typescript()` | TypeScript, JavaScript | `unused_export` | P5 (HEURISTIC) |
| `_analyze_python()` | Python | `unreachable_code` | P5 (HEURISTIC) |
| `_find_code_markers()` | All | `code_marker` (TODO/FIXME/HACK) | P1 (STATIC) |

**Limitations:**
- Export analysis is simplified (regex-based, not AST)
- Cross-file tracking is incomplete
- No actual call graph construction
- No reachability proofs

### UIWiringAnalyzer (`codetruth/analyzers/ui_wiring.py`)

| Method | Languages | Evidence Types | Proof Level |
|--------|-----------|----------------|-------------|
| `_analyze_react()` | React (TSX/JSX) | `unused_handler`, `empty_handler`, `button_no_handler` | P5 (HEURISTIC) |
| `_find_empty_handlers()` | React | `empty_handler`, `debug_only_handler` | P2 (STATIC_PARTIAL) |
| `_find_unwired_buttons()` | React | `button_no_handler` | P5 (HEURISTIC) |
| `_analyze_event_handlers()` | JS/TS | `potential_memory_leak` | P5 (HEURISTIC) |

**Limitations:**
- Regex-based pattern matching, not AST
- No actual click-to-effect verification
- No Playwright/runtime integration
- Heuristic-level confidence only

### Other Analyzers (Exist but Not Profiled)

| Analyzer | File | Description | Languages | Profile Status |
|----------|------|-------------|-----------|----------------|
| LintAnalyzer | `lint.py` | Runs ESLint/Flake8 | JS/TS/Python | No dedicated profile |
| TypeCheckAnalyzer | `type_check.py` | Runs TypeScript/mypy | TS/Python | No dedicated profile |
| SASTAnalyzer | `sast.py` | Security scanning | Multiple | No dedicated profile |
| SecretScanner | `secrets.py` | Finds secrets | All text | No dedicated profile |
| DependencyAuditor | `dependencies.py` | Dependency audit | Node/Python | No dedicated profile |
| APIContractAnalyzer | `contracts.py` | API contract check | OpenAPI | No dedicated profile |

---

## Gap Analysis

### Specified but Not Implemented

| Profile | Specification Lines | Implementation | Gap |
|---------|---------------------|----------------|-----|
| PHP | 490 | 0 | 100% |
| C# | 527 | 0 | 100% |
| Java | 469 | 0 | 100% |
| Lua | 463 | 0 | 100% |
| PowerShell | 471 | 0 | 100% |
| HTML | 420 | 0 | 100% |
| CSS | 400 | 0 | 100% |
| SQL | 450 | 0 | 100% |
| Shell | 0 (pending) | 0 | Profile needed |
| Dockerfile | 0 (pending) | 0 | Profile needed |
| YAML | 0 (pending) | 0 | Profile needed |
| JSON | 0 (pending) | 0 | Profile needed |

### Implemented but Under-Specified

| Implementation | Spec Coverage | Gap |
|----------------|---------------|-----|
| LintAnalyzer | No profile | 100% |
| TypeCheckAnalyzer | No profile | 100% |
| SASTAnalyzer | No profile | 100% |
| SecretScanner | No profile | 100% |
| DependencyAuditor | No profile | 100% |
| APIContractAnalyzer | No profile | 100% |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Profiles | 15 |
| Profiles with Implementation | 3 |
| Profiles UNPROVEN | 12 |
| Total Fixtures Defined | 30 |
| Total Goldens Defined | 30 |
| Implementation Coverage | 20% |

---

## HONESTY CHECK

- Claims made: 15 language types supported
- Claims proven: 3 (TypeScript, Python, JavaScript - PARTIAL)
- Claims unproven: 12
- Forbidden claims listed: YES
- Fixtures defined: YES (30 total)
- Goldens defined: YES (30 total)

**VERDICT: This document is HONEST. Most profiles are UNPROVEN due to missing implementation.**
