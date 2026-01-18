# Language Truth Profile: Lua

**Profile Version:** 1.0.0
**Language Version:** Lua 5.1+ (LuaJIT), 5.3+, 5.4+
**Stack Tier:** 4 (Specialized - Game Scripting)
**Profile Completeness:** 0.75
**Implementation Completeness:** 0.59

---

## Overview

Lua appears in game-related repositories for:
- **Game engine scripting** (Beyond All Reason, Spring RTS mods)
- **Game mod scripting** (WoW addons, Garry's Mod, Roblox)
- **Embedded scripting** (Redis, Nginx, Neovim)
- **Game AI and behavior trees**
- **Configuration as code**

### Game Scripting Context (Critical)

Lua in games has unique challenges:
- Scripts called from C/C++ engine (cross-boundary)
- Callback registration that may never trigger
- Event handlers with string-based event names
- Unit definitions with missing ability references
- Widget/UI code that may not be loaded

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.lua` | Extension | Lua source files |
| `*.luac` | Extension | Compiled Lua bytecode |
| `*.rockspec` | Extension | LuaRocks package |
| `.luacheckrc` | Filename | Luacheck config |
| `init.lua` | Filename | Module entry point |
| `units/*.lua` | Glob | Unit definitions (RTS games) |
| `widgets/*.lua` | Glob | UI widgets (Spring RTS) |
| `gadgets/*.lua` | Glob | Game logic (Spring RTS) |
| `LuaUI/*.lua` | Glob | UI scripts |
| `LuaRules/*.lua` | Glob | Rule scripts |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-lua |
| Grammar Version | 0.19.0 |
| Syntax Accuracy | 0.92 |
| Semantic Accuracy | 0.60 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Tree-sitter recovers |
| Error recovery | Yes | Moderate recovery |
| Incremental parsing | Yes | Supported |
| Comment preservation | Yes | Doc comments extracted |
| Metatables in AST | Partial | Structure visible, semantics not |

### Known Parse Failures

1. **Long string edge cases**: `[[` nested incorrectly
2. **Goto labels**: Older parsers miss goto
3. **Binary operators**: Custom operators via metatables
4. **Vararg expressions**: Complex `...` patterns

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | none (dynamically typed) |
| Import Resolution | Partial (require paths) |
| Type Resolution | No (no static types) |
| Mutation Tracking | No |
| Control Flow Analysis | Yes |
| Data Flow Analysis | Partial |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | Yes | 0.80 |
| Shadowing Detection | Yes | 0.75 |
| Closure Detection | Yes | 0.70 |
| Cross-file Resolution | Partial | 0.50 |
| Module Resolution | Partial | 0.55 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Metatables | false_negative | critical | Metatable tracing |
| Dynamic require | false_negative | high | Static require paths |
| loadstring/loadfile | false_negative | critical | Ban in linter |
| setfenv (5.1) | false_negative | critical | Avoid |
| _G manipulation | false_negative | high | Explicit globals |
| Coroutine state | incomplete | high | Coroutine tracing |
| Weak tables | incomplete | medium | Document usage |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | Partial | 0.55 | P5 (HEURISTIC) |
| Event Graph | Partial | 0.40 | P5 (HEURISTIC) |
| Route Graph | No | 0.00 | P7 (IMPOSSIBLE) |
| Data Flow Graph | Partial | 0.40 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| C/C++ Host Calls | Partial | P5 |
| File I/O | Yes | P2 |
| Network (LuaSocket) | Yes | P2 |
| Coroutines | Partial | P5 |
| Engine Callbacks | Partial | P5 |
| Event System | Partial | P5 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | Partial | 0.50 |
| Prove Unreachable | Partial | 0.35 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| C/C++ callbacks | false_negative | critical | Engine calls Lua function |
| String event names | incomplete | high | `RegisterEvent("EVENT_NAME", func)` |
| Metatable dispatch | false_negative | critical | `obj:method()` via `__index` |
| Dynamic function calls | false_negative | high | `_G[funcName]()` |
| Coroutine resume | incomplete | high | `coroutine.resume(co)` |
| Module lazy loading | incomplete | medium | On-demand require |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes (standalone) / Partial (embedded) |
| Environment | Lua interpreter / LuaJIT / Game engine |
| Min Version | Lua 5.1 |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | Partial | debug library |
| Execution Tracing | Yes | debug.sethook |
| Performance Profiling | Partial | LuaJIT profiler |
| State Snapshots | Partial | Serialization |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | Yes | Busted, LuaUnit |
| Integration Tests | Partial | Depends on host |
| E2E Tests | Partial | Host-dependent |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Partial |
| Granularity | line |
| Tool | luacov |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Host engine calls | incomplete | critical | C/C++ side |
| Metatable magic | false_negative | critical | Runtime interception |
| Coroutine timing | incomplete | high | Async execution |
| Sandbox escapes | false_negative | critical | Host-dependent |
| JIT compilation | incomplete | low | LuaJIT optimizations |

---

## Game Scripting Patterns (CRITICAL SECTION)

### Spring RTS / Beyond All Reason

#### Unit Definition
```lua
-- units/armcom.lua
local unitDef = {
    name = "Arm Commander",
    description = "Basic Commander",
    maxHealth = 5000,
    weapons = {
        {name = "armcomlaser"},  -- VERIFY: weapon definition exists
        {name = "armcomdgun"},   -- VERIFY: weapon definition exists
    },
    abilities = {
        "nanobuild",  -- VERIFY: ability script exists
        "cloak",      -- VERIFY: ability script exists
    },
}
return unitDef
```

#### Widget (UI Script)
```lua
-- LuaUI/Widgets/my_widget.lua
function widget:GetInfo()
    return {
        name = "My Widget",
        layer = 0,
        enabled = true,  -- VERIFY: actually loads
    }
end

function widget:Initialize()
    -- VERIFY: This runs on game start
end

function widget:DrawScreen()
    -- VERIFY: This is called every frame
end

-- MISSING: widget:Shutdown() - cleanup not implemented
```

#### Gadget (Game Logic)
```lua
-- LuaRules/Gadgets/my_gadget.lua
function gadget:UnitCreated(unitID, unitDefID, teamID)
    -- VERIFY: Event handler registered AND called
    -- VERIFY: Handler does something
end

function gadget:GameFrame(frame)
    if frame % 30 == 0 then
        -- VERIFY: Scheduled logic runs
    end
end
```

### WoW Addon Patterns

```lua
-- MyAddon.lua
local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_LOGIN")  -- VERIFY: Event exists
frame:RegisterEvent("FAKE_EVENT")    -- DETECTED: Event doesn't exist

frame:SetScript("OnEvent", function(self, event, ...)
    if event == "PLAYER_LOGIN" then
        -- VERIFY: Handler does something
    elseif event == "PLAYER_LOGOUT" then
        -- DETECTED: Event registered but not handled here
    end
end)
```

### Detection Rules for Game Scripts

| Pattern | Detection Method | Evidence Required |
|---------|------------------|-------------------|
| Missing weapon/ability | Unit def references vs definitions | Definition file presence |
| Widget not loading | enabled=true vs load log | Load confirmation |
| Event never fires | Event registration vs host events | Valid event list |
| Callback not called | Callback registration vs engine | Host callback inventory |
| Unhandled event | Registered events vs handler cases | Handler coverage |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| ast_graph | json | P1 | T0 | Yes | No |
| require_graph | json | P2 | T0 | Yes | No |
| function_defs | json | P2 | T0 | Yes | No |
| event_handlers | json | P5 | T1 | Yes | No |
| unit_references | json | P2 | T0 | Yes | No |
| coverage_report | json | P4 | T0 | No | Yes |
| debug_trace | log | P3 | T1 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | loadstring | Dynamic code execution | Arbitrary string | Ban in linter |
| 2 | Metatable syntax | `setmetatable` effects | Runtime behavior | Document metatables |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Dynamic typing | No static types | Language design | Emmylua annotations |
| 2 | Metatables | `__index`, `__call` intercept | Arbitrary behavior | Metatable inventory |
| 3 | Global namespace | `_G` manipulation | Implicit globals | Local everything |
| 4 | Coroutines | Execution pauses | Non-linear flow | Coroutine tracing |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | C/C++ calls | Host engine invocations | Binary boundary | Host API manifest |
| 2 | String events | `RegisterEvent(name, fn)` | String dispatch | Event registry |
| 3 | Dynamic dispatch | `_G[name]()` | Variable names | Static dispatch |
| 4 | Module paths | `require` with variables | Dynamic loading | Static requires |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Host sandbox | Engine limits Lua | Host-controlled | Sandbox documentation |
| 2 | Coroutine state | `yield`/`resume` timing | Non-deterministic | State tracking |
| 3 | GC timing | Weak table collection | Non-deterministic | Explicit cleanup |
| 4 | LuaJIT compilation | Trace compilation | Optimization | Profile mode |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| C/C++ (host) | ffi | Partial | No | No | P5 |
| JSON (config) | file | Yes | Yes | Yes (schema) | P2 |
| SQL (lsqlite3) | database | Yes | Partial | Partial | P3 |
| HTTP (LuaSocket) | network | Yes | Partial | No | P3 |

### Common Boundary Patterns

```lua
-- Pattern 1: Engine callback (BLINDSPOT)
function gadget:UnitCreated(unitID, unitDefID, teamID)
    -- Called from C++ engine - cannot trace caller
end

-- Pattern 2: Event registration
frame:RegisterEvent("PLAYER_LOGIN")  -- String-based
frame:SetScript("OnEvent", handler)  -- Callback registration

-- Pattern 3: Require chain
local utils = require("mymod.utils")  -- Traceable
local dynamic = require(moduleName)   -- BLINDSPOT: variable path

-- Pattern 4: C function call (LuaJIT FFI)
local ffi = require("ffi")
ffi.cdef[[int printf(const char *fmt, ...);]]
ffi.C.printf("Hello")  -- BLINDSPOT: native call
```

---

## Failure Patterns

### Pattern 1: Event Never Handled

**Description:** Event registered but handler doesn't process it

**Detection:** Match registered events with handler cases

**Example:**
```lua
frame:RegisterEvent("PLAYER_LOGOUT")
frame:SetScript("OnEvent", function(self, event)
    if event == "PLAYER_LOGIN" then
        -- handle login
    end
    -- DETECTED: PLAYER_LOGOUT registered but not handled
end)
```

### Pattern 2: Missing Definition Reference

**Description:** Unit/item references non-existent definition

**Detection:** Cross-reference with definition files

**Example:**
```lua
local unitDef = {
    weapons = {
        {name = "nonexistent_weapon"},  -- DETECTED: weapon not defined
    },
}
```

### Pattern 3: Widget Never Loads

**Description:** Widget defined but never initialized

**Detection:** Check GetInfo().enabled and load mechanism

**Example:**
```lua
function widget:GetInfo()
    return {
        enabled = false,  -- DETECTED: disabled by default
    }
end
```

### Pattern 4: Callback Never Called

**Description:** Callback registered but host never triggers it

**Detection:** Compare registered callbacks with engine documentation

**Example:**
```lua
function gadget:FakeCallback()  -- DETECTED: not a valid engine callback
    -- never called
end
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.92 × 0.15 = 0.138
    semantic_accuracy × 0.20 +        # 0.60 × 0.20 = 0.120
    wiring_completeness × 0.25 +      # 0.45 × 0.25 = 0.113
    runtime_capability × 0.25 +       # 0.60 × 0.25 = 0.150
    (1 - blindspot_penalty) × 0.15    # 0.50 × 0.15 = 0.075
)
```

**Current Score:** 0.60 (PARTIAL)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with game scripting focus |
