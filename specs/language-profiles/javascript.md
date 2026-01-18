# Language Truth Profile: JavaScript

**Profile Version:** 1.0.0
**Language Version:** ES2022+
**Stack Tier:** 2 (Application Layer)
**Profile Completeness:** 0.88
**Implementation Completeness:** 0.82

---

## Overview

JavaScript is the runtime language for web and Node.js applications. Distinct from TypeScript (no static types). In the user's 589+ repos, JavaScript appears in:
- Legacy codebases without TypeScript
- Node.js scripts and tools
- Browser extensions
- Game server utilities
- Configuration files (webpack, babel, eslint)
- Bookmarklets and userscripts

JavaScript verification focuses on **runtime behavior**, **dynamic dispatch**, **prototype chains**, and **event binding**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.js` | Extension | JavaScript files |
| `*.mjs` | Extension | ES modules |
| `*.cjs` | Extension | CommonJS modules |
| `*.jsx` | Extension | JSX (React without TS) |
| `.eslintrc.js` | Filename | ESLint config |
| `webpack.config.js` | Filename | Webpack config |
| `babel.config.js` | Filename | Babel config |
| `jest.config.js` | Filename | Jest config |
| `rollup.config.js` | Filename | Rollup config |
| `vite.config.js` | Filename | Vite config |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-javascript |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.99 |
| Semantic Accuracy | 0.70 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Excellent recovery |
| Error recovery | Yes | Handles syntax errors |
| Incremental parsing | Yes | Supported |
| Comment preservation | Yes | JSDoc extracted |
| ES modules | Yes | import/export |
| CommonJS | Yes | require/module.exports |

### Known Parse Failures

1. **eval()**: Dynamic code execution
2. **new Function()**: Runtime code generation
3. **with statement**: Scope modification (deprecated)
4. **Non-standard syntax**: Proposed features without Babel
5. **Template literal abuse**: Complex nested templates

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | none (dynamic typing) |
| Import Resolution | Yes |
| Type Resolution | No (no types) |
| Mutation Tracking | Partial |
| Control Flow Analysis | Yes |
| Data Flow Analysis | Partial |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | Yes | 0.90 |
| Shadowing Detection | Yes | 0.85 |
| Closure Detection | Yes | 0.80 |
| Cross-file Resolution | Yes | 0.75 |
| Cross-module Resolution | Yes | 0.70 |
| Hoisting Analysis | Yes | 0.95 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Dynamic property access | false_negative | critical | Property inventory |
| Prototype mutation | false_negative | critical | Runtime tracing |
| eval/Function | impossible | critical | Refuse analysis |
| this binding | incomplete | high | Context tracking |
| Proxy objects | false_negative | high | Runtime inspection |
| Symbol properties | incomplete | medium | Symbol tracking |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | Partial | 0.65 | P5 (HEURISTIC) |
| Event Graph | Partial | 0.55 | P5 (HEURISTIC) |
| Import Graph | Yes | 0.85 | P2 (STATIC_PARTIAL) |
| Data Flow Graph | Partial | 0.50 | P5 (HEURISTIC) |
| Prototype Graph | Partial | 0.40 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| HTTP (fetch/axios) | Yes | P2 |
| DOM Events | Partial | P3 |
| setTimeout/setInterval | Yes | P2 |
| Process spawn | Yes | P2 |
| File I/O (Node) | Yes | P2 |
| WebSocket | Yes | P2 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | Partial | 0.60 |
| Prove Unreachable | Partial | 0.50 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Dynamic dispatch | false_negative | critical | `obj[method]()` |
| Event delegation | incomplete | high | `parent.on('click', '.child')` |
| Callback hell | incomplete | high | Deeply nested callbacks |
| Promise chains | incomplete | medium | Long `.then()` chains |
| Monkey patching | false_negative | critical | `Array.prototype.custom = ...` |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes |
| Environment | Node.js, Browser |
| Min Version | Node 18.0.0 / ES2020 browsers |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | Yes | Istanbul/nyc |
| Execution Tracing | Yes | Node --inspect |
| Performance Profiling | Yes | Chrome DevTools |
| State Snapshots | Partial | Heap snapshots |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | Yes | Jest, Mocha, Vitest |
| Integration Tests | Yes | Jest, Cypress |
| E2E Tests | Yes | Playwright, Cypress |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Yes |
| Granularity | branch |
| Tool | Istanbul/nyc, c8 |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Async timing | incomplete | high | Race conditions |
| Error recovery | incomplete | medium | try/catch swallows |
| Memory leaks | incomplete | medium | GC behavior |
| Event loop | incomplete | high | Microtask ordering |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| ast_dump | json | P1 | T0 | Yes | No |
| import_graph | json | P2 | T0 | Yes | No |
| call_graph | json | P5 | T1 | No | No |
| event_bindings | json | P5 | T1 | No | No |
| coverage_report | json | P4 | T0 | No | Yes |
| runtime_trace | json | P3 | T1 | No | Yes |
| heap_snapshot | binary | P3 | T1 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | eval() | Runtime code execution | Impossible statically | Refuse + warn |
| 2 | new Function() | Dynamic function creation | Impossible statically | Refuse + warn |
| 3 | with statement | Dynamic scope | Deprecated | Lint error |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Dynamic typing | No type information | Language design | Runtime inference |
| 2 | Prototype mutation | Runtime prototype changes | Dynamic | Snapshot analysis |
| 3 | this binding | Context-dependent | Call-site dependent | Call graph |
| 4 | Property access | obj[variable] | Runtime value | Property inventory |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Dynamic dispatch | method names as strings | Runtime resolution | Heuristics |
| 2 | Event delegation | Events bubble to parents | DOM structure | DOM analysis |
| 3 | Higher-order functions | Functions passed as args | Callback identity | Trace analysis |
| 4 | Implicit globals | window.foo = bar | No explicit declaration | Global inventory |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Async ordering | Promise/setTimeout order | Event loop | Sequence testing |
| 2 | Error swallowing | Empty catch blocks | Silent failures | Catch analysis |
| 3 | Memory behavior | GC timing | Non-deterministic | Heap analysis |
| 4 | Browser differences | API variations | Multi-environment | Cross-browser test |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| HTML (DOM) | runtime | Partial | Partial | No | P5 |
| CSS (classList) | runtime | Partial | No | No | P5 |
| JSON (parse/stringify) | data | Yes | Yes | Partial | P2 |
| WebAssembly | ffi | Yes | No | No | P6 |
| Node native addons | ffi | Partial | No | No | P6 |

### Common Boundary Patterns

```javascript
// Pattern 1: DOM Manipulation
document.getElementById('btn').addEventListener('click', handler);
// VERIFICATION: Must verify 'btn' exists in HTML and handler is defined

// Pattern 2: Fetch API
fetch('/api/data').then(res => res.json()).then(processData);
// VERIFICATION: Must verify /api/data endpoint exists

// Pattern 3: Dynamic Import
const module = await import(`./plugins/${name}.js`);
// VERIFICATION: Cannot verify - path is dynamic

// Pattern 4: Event Delegation
container.addEventListener('click', (e) => {
    if (e.target.matches('.item')) handleItem(e.target);
});
// VERIFICATION: Partial - need to verify .item elements exist
```

---

## Game Server Specific Patterns

### Browser Game Utilities

```javascript
// Pattern: Travian bot/helper script
setInterval(() => {
    const resources = document.querySelectorAll('.resource');
    resources.forEach(r => {
        // BLINDSPOT: DOM structure may change
    });
}, 60000);
```

**Detection Rules:**
1. setInterval without clearInterval → potential memory leak
2. DOM queries without null checks → crash risk
3. Global variable pollution → conflict risk

### Node.js Game Tools

```javascript
// Pattern: MapleStory packet analyzer
const net = require('net');
const server = net.createServer((socket) => {
    socket.on('data', (buffer) => {
        const opcode = buffer.readUInt16LE(0);
        handlers[opcode]?.(buffer);  // Dynamic dispatch!
    });
});
// BLINDSPOT: handlers[opcode] is fully dynamic
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| tree-sitter-javascript | Parsing | 0.20.0 |
| Node.js | Runtime | 18.0.0 |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| ESLint | Static analysis | Semantic checks |
| Istanbul/nyc | Coverage | Runtime verification |
| Jest | Testing | Test execution |
| Acorn | Alternative parser | Complex syntax |

---

## Failure Patterns

### Pattern 1: Dead Event Handler

**Description:** Event listener added but never triggered

**Detection:** Event binding without corresponding user action path

**Example:**
```javascript
element.addEventListener('click', handleClick);
// But element has CSS: pointer-events: none
// DETECTED: Event will never fire
```

### Pattern 2: Orphan Function

**Description:** Function defined but never called

**Detection:** No call sites in call graph

**Example:**
```javascript
function unusedHelper() {  // DETECTED: Never called
    return 'helper';
}
```

### Pattern 3: Promise Void

**Description:** Promise created but never awaited or .then'd

**Detection:** Promise without consumption

**Example:**
```javascript
async function save() {
    fetch('/api/save', { method: 'POST', body: data });
    // DETECTED: fetch() returns Promise that is ignored
}
```

### Pattern 4: Callback Never Called

**Description:** Callback parameter never invoked

**Detection:** Callback argument without call site

**Example:**
```javascript
function process(data, callback) {  // DETECTED: callback never called
    const result = transform(data);
    return result;  // callback ignored!
}
```

### Pattern 5: Error Swallowed

**Description:** Catch block that silences errors

**Detection:** Empty or logging-only catch blocks

**Example:**
```javascript
try {
    riskyOperation();
} catch (e) {
    // DETECTED: Error silently swallowed
}
```

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "All code paths covered" | Dynamic dispatch | 100% branch coverage + manual review |
| "No runtime errors possible" | Dynamic typing | Full test suite + fuzzing |
| "All events handled" | Event delegation unknown | DOM + event inventory |
| "Memory safe" | GC is non-deterministic | Heap analysis over time |
| "Complete call graph" | Dynamic dispatch breaks it | Runtime trace correlation |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Promise Void

**Purpose:** Tests detection of unhandled promises

**File:** `fixtures/javascript/promise-void/`

**Expected Findings:**
- CRITICAL: fetch() result ignored at line 12
- HIGH: async function result discarded at line 25

**Forbidden False Positives:**
- Should NOT flag fire-and-forget logging
- Should NOT flag intentionally detached async

### Fixture 2: Dynamic Dispatch Black Hole

**Purpose:** Tests detection of unprovable dynamic calls

**File:** `fixtures/javascript/dynamic-dispatch/`

**Expected Findings:**
- WARNING: Cannot verify handlers[opcode] at line 8
- WARNING: Cannot verify obj[methodName]() at line 15

**Forbidden False Positives:**
- Should NOT flag computed properties with literal keys
- Should NOT flag well-typed Map access

---

## Golden Output Expectations (MANDATORY SECTION)

### Golden 1: Promise Void

```json
{
  "findings": [
    {
      "type": "unhandled_promise",
      "severity": "critical",
      "location": "api.js:12",
      "message": "fetch() returns Promise that is never awaited or handled",
      "proof_level": "P2",
      "evidence": "ast_analysis_20240118_001"
    }
  ],
  "confidence": 0.80,
  "blindspots_acknowledged": [
    "Fire-and-forget patterns may be intentional",
    "Global error handlers not analyzed"
  ]
}
```

### Golden 2: Dynamic Dispatch Black Hole

```json
{
  "findings": [
    {
      "type": "unprovable_dispatch",
      "severity": "warning",
      "location": "handlers.js:8",
      "message": "Cannot statically verify handlers[opcode] resolves to valid function",
      "proof_level": "P7",
      "evidence": "call_graph_20240118_001"
    }
  ],
  "confidence": 0.40,
  "blindspots_acknowledged": [
    "Dynamic dispatch prevents static verification",
    "Runtime tracing required for confidence"
  ]
}
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.99 × 0.15 = 0.149
    semantic_accuracy × 0.20 +        # 0.70 × 0.20 = 0.140
    wiring_completeness × 0.25 +      # 0.55 × 0.25 = 0.138
    runtime_capability × 0.25 +       # 0.80 × 0.25 = 0.200
    (1 - blindspot_penalty) × 0.15    # 0.50 × 0.15 = 0.075
)
```

**Current Score:** 0.70 (PARTIAL - dynamic typing severely limits static analysis)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile |
