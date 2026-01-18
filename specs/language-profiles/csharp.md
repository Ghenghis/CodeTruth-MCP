# Language Truth Profile: C# (.NET)

**Profile Version:** 1.0.0
**Language Version:** C# 8.0+ / .NET Core 3.1+ / .NET 5+
**Stack Tier:** 1 (Critical Core - Game Servers)
**Profile Completeness:** 0.88
**Implementation Completeness:** 0.81

---

## Overview

C# appears in 21 repos in this codebase (19 user-owned), primarily for:
- **Game servers** (MapleStory private servers - MapleSolaxia, etc.)
- **Game modding tools** (Bannerlord Launcher Manager, save editors)
- **Unity game projects** (Rust Base Builder, Auto Base Builder)
- **Desktop applications** (Windows tools, flash browsers)
- **Bot automation** (Catchem-PoGo, game bots)

### Game Server Context (Critical)

C# game servers (especially MapleStory-style) have unique patterns:
- Packet handlers that must be registered AND implemented
- Event scripts that reference non-existent handlers
- NPC scripts with broken quest logic
- Item/skill definitions with incomplete effects
- Database operations with transaction issues
- Socket handlers that silently drop packets

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.cs` | Extension | C# source files |
| `*.csx` | Extension | C# script files |
| `*.csproj` | Extension | Project files |
| `*.sln` | Extension | Solution files |
| `*.razor` | Extension | Razor components |
| `*.cshtml` | Extension | Razor views |
| `packages.config` | Filename | Legacy NuGet |
| `Directory.Build.props` | Filename | Build configuration |
| `global.json` | Filename | SDK version |
| `nuget.config` | Filename | NuGet sources |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter + language_server |
| Parser Name | tree-sitter-c-sharp + OmniSharp/Roslyn |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.95 |
| Semantic Accuracy | 0.85 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Error recovery good |
| Error recovery | Yes | Roslyn provides excellent recovery |
| Incremental parsing | Yes | Both tree-sitter and Roslyn |
| Comment preservation | Yes | XML docs extracted |
| Generic parsing | Yes | Full generic support |
| Nullable reference types | Yes | C# 8+ annotations |

### Known Parse Failures

1. **Top-level statements**: C# 9+ top-level programs parsing
2. **Record types**: Complex record inheritance
3. **Pattern matching**: Deeply nested patterns
4. **Source generators**: Generated code not visible

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | full (Roslyn provides complete type info) |
| Import Resolution | Yes |
| Type Resolution | Yes |
| Mutation Tracking | Yes (for value types, limited for references) |
| Control Flow Analysis | Yes |
| Data Flow Analysis | Yes |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | Yes | 0.98 |
| Shadowing Detection | Yes | 0.95 |
| Closure Detection | Yes | 0.90 |
| Cross-file Resolution | Yes | 0.95 |
| Cross-assembly Resolution | Yes | 0.90 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Reflection | false_negative | critical | Minimize use, document |
| dynamic keyword | false_negative | high | Avoid dynamic |
| Expression trees | incomplete | medium | Static analysis |
| Source generators | incomplete | medium | Include generated code |
| Unsafe code | incomplete | high | Code review |
| P/Invoke | incomplete | high | Interface documentation |
| COM interop | incomplete | high | Wrapper analysis |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | Yes | 0.85 | P2 (STATIC_PARTIAL) |
| Event Graph | Yes | 0.75 | P2 (STATIC_PARTIAL) |
| Route Graph | Yes | 0.80 | P2 (STATIC_PARTIAL) |
| Data Flow Graph | Yes | 0.80 | P2 (STATIC_PARTIAL) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| HTTP Calls (HttpClient) | Yes | P2 |
| Database (EF Core, Dapper) | Yes | P2 |
| File I/O | Yes | P1 |
| Process Spawn | Yes | P1 |
| Socket Operations | Yes | P2 |
| Interprocess (Named Pipes) | Yes | P2 |
| P/Invoke (Native) | Partial | P5 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | Yes | 0.85 |
| Prove Unreachable | Partial | 0.60 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Reflection invoke | false_negative | critical | `Type.GetMethod().Invoke()` |
| Event handlers (string) | incomplete | high | `button.Click += handler` via reflection |
| Dynamic dispatch | false_negative | high | `dynamic obj; obj.Method()` |
| Attribute-based routing | incomplete | medium | `[Route("path")]` |
| Dependency injection | incomplete | high | Constructor injection resolution |
| Game packet handlers | incomplete | critical | Opcode → handler mapping |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes |
| Environment | .NET Runtime (Core/5+/Framework) |
| Min Version | .NET Core 3.1+ (recommended), Framework 4.7.2+ |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | Yes | DiagnosticSource, ActivitySource |
| Execution Tracing | Yes | dotnet-trace, PerfView |
| Performance Profiling | Yes | dotnet-counters, BenchmarkDotNet |
| State Snapshots | Yes | Debugger, memory dumps |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | Yes | xUnit, NUnit, MSTest |
| Integration Tests | Yes | xUnit + TestServer |
| E2E Tests | Yes | Playwright, Selenium |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Yes |
| Granularity | branch |
| Tool | Coverlet, dotCover |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Native code (P/Invoke) | incomplete | high | Binary, not .NET IL |
| Multi-threaded races | false_negative | critical | Non-deterministic |
| Async timing | incomplete | medium | Task scheduling |
| GC behavior | incomplete | low | Non-deterministic |
| JIT compilation | incomplete | low | Runtime optimization |

---

## Game Server Patterns (CRITICAL SECTION)

### MapleStory Private Server Specific

MapleStory servers (MapleSolaxia, etc.) have specific patterns:

#### Packet Handler Registration
```csharp
// Packet handlers must be registered AND implemented
public class PacketProcessor {
    private Dictionary<short, Action<Client, InPacket>> _handlers;

    public void RegisterHandlers() {
        // VERIFY: Every opcode has a handler
        _handlers[RecvOps.PLAYER_MOVE] = HandlePlayerMove;
        _handlers[RecvOps.ATTACK] = HandleAttack;
        // MISSING: RecvOps.USE_SKILL not registered!
    }

    // VERIFY: Handler actually does something
    private void HandleAttack(Client c, InPacket p) {
        // NOT: empty or stub
    }
}
```

#### NPC Script System
```csharp
// NPC scripts reference quest/item IDs that may not exist
public class NpcScript {
    public void Start() {
        if (HasQuest(1234)) {  // VERIFY: Quest 1234 exists
            GiveItem(4001234);  // VERIFY: Item 4001234 exists
            CompleteQuest(1234);
        }
    }
}
```

#### Skill Effect System
```csharp
// Skills must have complete effect implementations
public class Skill {
    public int SkillId { get; set; }
    public SkillEffect Effect { get; set; }

    public void Use(Character user, Character target) {
        // VERIFY: Effect is not null/stub
        Effect?.Apply(user, target);  // Often null!
    }
}
```

#### Item Effect System
```csharp
// Items with effects that don't work
public class ItemEffect {
    public void UseItem(Character c, int itemId) {
        switch (itemId) {
            case 2000000:  // HP Potion
                c.HP += 100;  // VERIFY: Actually saves
                break;
            case 2000001:  // MP Potion
                // STUB: Not implemented!
                break;
        }
    }
}
```

### Detection Rules for Game Servers

| Pattern | Detection Method | Evidence Required |
|---------|------------------|-------------------|
| Missing packet handler | Opcode enum vs handler registry | Registration proof |
| Empty handler | Handler method body analysis | Non-trivial code |
| Missing quest data | Script ID references vs data files | Data file presence |
| Missing item data | Item ID references vs wz/data | Data file presence |
| Skill stub | Skill ID vs effect implementation | Effect code presence |
| Database desync | Entity change vs database write | Transaction proof |

---

## Unity Game Patterns

### MonoBehaviour Lifecycle
```csharp
public class PlayerController : MonoBehaviour {
    void Start() {
        // VERIFY: Initialization actually happens
    }

    void Update() {
        // VERIFY: Called every frame
        // DETECT: Empty Update() is a performance issue
    }

    void OnCollisionEnter(Collision c) {
        // VERIFY: Actually handles collision
        // DETECT: Empty collision handler
    }
}
```

### Event System
```csharp
public class GameEvents : MonoBehaviour {
    public static event Action<int> OnScoreChanged;

    // VERIFY: Event is actually invoked somewhere
    // VERIFY: Event has subscribers
    public void AddScore(int points) {
        score += points;
        OnScoreChanged?.Invoke(score);  // Check: is anything listening?
    }
}
```

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| ast_graph | json | P1 | T0 | Yes | No |
| type_info | json | P1 | T0 | Yes | No |
| call_graph | json | P2 | T0 | Yes | No |
| dependency_graph | json | P1 | T0 | Yes | No |
| packet_handler_map | json | P2 | T0 | Yes | No |
| npc_script_refs | json | P2 | T0 | Yes | No |
| test_coverage | cobertura | P4 | T0 | No | Yes |
| runtime_trace | nettrace | P3 | T0 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Source generators | Generated code not in source | Build-time generation | Include generated files |
| 2 | Conditional compilation | #if blocks depend on build | Build configuration | Analyze all configs |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Reflection | Type.GetMethod(), Activator | Dynamic type discovery | Minimize, document |
| 2 | dynamic keyword | Runtime binding | No static type | Avoid dynamic |
| 3 | Expression trees | Compiled at runtime | Deferred execution | Static analysis |
| 4 | Attributes | May affect behavior | Metadata-driven | Attribute analysis |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | DI containers | Constructor injection | Container-resolved | Analyze DI config |
| 2 | Event handlers | Multicast delegates | Runtime subscription | Event tracing |
| 3 | Packet handlers | Opcode → method mapping | Dictionary lookup | Handler registry |
| 4 | Script systems | String-based script loading | Dynamic loading | Script manifest |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | P/Invoke | Native code calls | Binary, not IL | Interface docs |
| 2 | Unsafe code | Pointer manipulation | Memory unsafe | Code review |
| 3 | Async races | Task scheduling | Non-deterministic | Race testing |
| 4 | Socket state | Network timing | External dependency | Integration tests |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| SQL (EF Core, Dapper) | database | Yes | Partial | Yes (schema) | P2 |
| C/C++ (P/Invoke) | ffi | Partial | No | No | P5 |
| JavaScript (Blazor) | interop | Yes | Partial | Partial | P3 |
| TypeScript (SignalR client) | websocket | Yes | Partial | Yes (hub contract) | P2 |
| WZ/Data files (MapleStory) | file | Yes | Yes | Partial | P2 |

### Common Boundary Patterns

```csharp
// Pattern 1: Database (Entity Framework)
await _context.Characters.AddAsync(character);
await _context.SaveChangesAsync();  // VERIFY: Actually persists

// Pattern 2: Packet handling (game server)
public void HandlePacket(Client client, byte[] data) {
    short opcode = BitConverter.ToInt16(data, 0);
    if (_handlers.TryGetValue(opcode, out var handler)) {
        handler(client, new InPacket(data));  // VERIFY: handler exists
    }
    // MISSING: else case - unknown packet silently dropped!
}

// Pattern 3: WZ data loading (MapleStory)
var itemData = DataProvider.GetItem(itemId);
if (itemData == null) {
    // DETECTED: Item referenced but not in data files
    return;
}

// Pattern 4: P/Invoke (native code - BLINDSPOT)
[DllImport("native.dll")]
private static extern int ProcessData(IntPtr data);  // Cannot trace inside
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| tree-sitter-c-sharp | AST parsing | 0.20.0 |
| .NET SDK | Compilation/analysis | 6.0+ |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| OmniSharp | Language server | Semantic analysis |
| Roslyn Analyzers | Static analysis | Code quality |
| Coverlet | Coverage | Runtime analysis |
| xUnit | Testing | Test execution |
| dotnet-trace | Profiling | Runtime tracing |

---

## Failure Patterns

### Pattern 1: Unregistered Packet Handler

**Description:** Packet opcode exists but no handler registered

**Detection:** Compare opcode enum with handler registry

**Example:**
```csharp
public enum RecvOps : short {
    PLAYER_MOVE = 0x01,
    ATTACK = 0x02,
    USE_SKILL = 0x03,  // DETECTED: No handler for 0x03
}

// Handler registration missing USE_SKILL
```

### Pattern 2: Empty Handler Body

**Description:** Handler exists but does nothing

**Detection:** Method body analysis - empty or only logging

**Example:**
```csharp
private void HandleUseSkill(Client c, InPacket p) {
    // TODO: Implement
}  // DETECTED: Empty handler

private void HandleAttack(Client c, InPacket p) {
    Log.Debug("Attack received");  // Only logs, no effect
}  // DETECTED: No game effect
```

### Pattern 3: Missing Data Reference

**Description:** Code references ID that doesn't exist in data

**Detection:** Cross-reference code IDs with data files

**Example:**
```csharp
GiveItem(4001234);  // DETECTED: Item 4001234 not in ItemData.wz
StartQuest(9999);   // DETECTED: Quest 9999 not in Quest.wz
```

### Pattern 4: Database Write Without SaveChanges

**Description:** Entity modified but changes never saved

**Detection:** Track entity modifications vs SaveChanges calls

**Example:**
```csharp
var character = await _context.Characters.FindAsync(id);
character.Level += 1;
character.Exp = 0;
// MISSING: await _context.SaveChangesAsync();
// DETECTED: Entity modified, no save
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.95 × 0.15 = 0.143
    semantic_accuracy × 0.20 +        # 0.85 × 0.20 = 0.170
    wiring_completeness × 0.25 +      # 0.70 × 0.25 = 0.175
    runtime_capability × 0.25 +       # 0.85 × 0.25 = 0.213
    (1 - blindspot_penalty) × 0.15    # 0.70 × 0.15 = 0.105
)
```

**Current Score:** 0.81 (PRODUCTION)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with game server focus |
