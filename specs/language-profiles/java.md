# Language Truth Profile: Java

**Profile Version:** 1.0.0
**Language Version:** Java 8+ (LTS: 8, 11, 17, 21)
**Stack Tier:** 4 (Specialized - Game Servers)
**Profile Completeness:** 0.85
**Implementation Completeness:** 0.82

---

## Overview

Java appears in 2 repos in this codebase, primarily for:
- **MapleStory private servers** (MapleSolaxia, OdinMS forks)
- **APK tools** (Apktool for Android reverse engineering)
- **Legacy game servers** (various MMORPG emulators)

### Game Server Context (Critical)

Java MapleStory servers (OdinMS lineage) have specific patterns:
- Packet handlers with opcode registration
- NPC scripts (JavaScript/Nashorn embedded)
- Quest handlers with state machines
- Scheduled tasks (mob respawns, events)
- Database access patterns (JDBC)

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.java` | Extension | Java source files |
| `*.jar` | Extension | Java archives |
| `*.class` | Extension | Compiled bytecode |
| `pom.xml` | Filename | Maven configuration |
| `build.gradle` | Filename | Gradle configuration |
| `build.gradle.kts` | Filename | Gradle Kotlin DSL |
| `settings.gradle` | Filename | Gradle settings |
| `*.properties` | Extension | Properties files |
| `META-INF/MANIFEST.MF` | Path | Manifest file |
| `scripts/*.js` | Glob | Embedded scripts (Nashorn) |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter + language_server |
| Parser Name | tree-sitter-java + Eclipse JDT LS |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.97 |
| Semantic Accuracy | 0.85 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Tree-sitter recovers |
| Error recovery | Yes | Good recovery |
| Incremental parsing | Yes | JDT provides incremental |
| Comment preservation | Yes | Javadoc extracted |
| Generic parsing | Yes | Full generics support |
| Annotation parsing | Yes | Runtime/compile annotations |

### Known Parse Failures

1. **Complex generics**: Deeply nested wildcards
2. **Annotation processors**: Generated code not visible
3. **Lombok**: Generates code at compile time
4. **Records (Java 16+)**: Newer syntax in older parsers

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | full (strong static typing) |
| Import Resolution | Yes |
| Type Resolution | Yes |
| Mutation Tracking | Partial (final helps) |
| Control Flow Analysis | Yes |
| Data Flow Analysis | Yes |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | Yes | 0.98 |
| Shadowing Detection | Yes | 0.95 |
| Closure Detection | Yes | 0.85 |
| Cross-file Resolution | Yes | 0.95 |
| Cross-package Resolution | Yes | 0.90 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Reflection | false_negative | critical | Minimize, document |
| Dynamic proxies | false_negative | high | Interface analysis |
| Annotation processors | incomplete | medium | Include generated |
| Service loaders | incomplete | high | Service manifest |
| Classloader magic | false_negative | critical | Standard loaders only |
| Embedded scripts (Nashorn) | false_negative | critical | Script analysis |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | Yes | 0.85 | P2 (STATIC_PARTIAL) |
| Event Graph | Yes | 0.70 | P2 (STATIC_PARTIAL) |
| Route Graph | Yes | 0.80 | P2 (STATIC_PARTIAL) |
| Data Flow Graph | Yes | 0.75 | P2 (STATIC_PARTIAL) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| HTTP Calls (HttpClient, OkHttp) | Yes | P2 |
| Database (JDBC, Hibernate) | Yes | P2 |
| File I/O | Yes | P1 |
| Process Spawn | Yes | P1 |
| Socket Operations | Yes | P2 |
| RMI | Partial | P5 |
| JNI | Partial | P5 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | Yes | 0.85 |
| Prove Unreachable | Partial | 0.60 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Reflection invoke | false_negative | critical | `Method.invoke()` |
| Spring DI | incomplete | high | `@Autowired` injection |
| Servlet mapping | incomplete | medium | web.xml / annotation routing |
| Script engine | false_negative | critical | `ScriptEngine.eval()` |
| Message queues | incomplete | high | JMS listeners |
| Timer tasks | incomplete | medium | `ScheduledExecutorService` |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes |
| Environment | JVM |
| Min Version | Java 8 (LTS) |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | Yes | Java agents, ByteBuddy |
| Execution Tracing | Yes | JFR, async-profiler |
| Performance Profiling | Yes | JFR, VisualVM |
| State Snapshots | Yes | Heap dumps |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | Yes | JUnit, TestNG |
| Integration Tests | Yes | JUnit + containers |
| E2E Tests | Yes | Selenium, Playwright |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Yes |
| Granularity | branch |
| Tool | JaCoCo, Cobertura |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| JNI native code | incomplete | high | Native binary |
| Reflection calls | false_negative | critical | Dynamic dispatch |
| Thread races | false_negative | critical | Non-deterministic |
| GC timing | incomplete | low | JVM managed |
| Classloader isolation | incomplete | medium | Separate namespaces |

---

## MapleStory Server Patterns (CRITICAL SECTION)

### OdinMS Architecture

MapleStory Java servers (OdinMS and forks) have these patterns:

#### Packet Handler Registration
```java
public class PacketProcessor {
    private static Map<Short, MaplePacketHandler> handlers = new HashMap<>();

    static {
        // VERIFY: All opcodes have handlers
        handlers.put(RecvOpcode.PLAYER_LOGGEDIN.getValue(), new PlayerLoggedinHandler());
        handlers.put(RecvOpcode.CHANGE_MAP.getValue(), new ChangeMapHandler());
        // MISSING: RecvOpcode.USE_CASH_ITEM not registered!
    }

    public void process(SeekableLittleEndianAccessor slea, MapleClient c) {
        short opcode = slea.readShort();
        MaplePacketHandler handler = handlers.get(opcode);
        if (handler != null) {
            handler.handlePacket(slea, c);  // VERIFY: handler does something
        }
        // MISSING: else case - unknown packet dropped silently
    }
}
```

#### NPC Script System (Nashorn)
```java
public class NPCScriptManager {
    private ScriptEngine engine = new ScriptEngineManager().getEngineByName("nashorn");

    public void start(MapleClient c, int npcId) {
        String scriptPath = "scripts/npc/" + npcId + ".js";
        // VERIFY: Script file exists
        // VERIFY: Script doesn't reference missing quests/items
        engine.eval(new FileReader(scriptPath));
    }
}
```

```javascript
// scripts/npc/9000000.js
function start() {
    if (cm.haveItem(4001234)) {  // VERIFY: Item 4001234 exists
        cm.completeQuest(1234);  // VERIFY: Quest 1234 exists
        cm.gainItem(4001235);    // VERIFY: Item 4001235 exists
    }
}
```

#### Quest Handler System
```java
public class MapleQuest {
    private Map<Integer, QuestAction> completeActions = new HashMap<>();

    public void complete(MapleCharacter c, int npcId) {
        QuestAction action = completeActions.get(questId);
        if (action != null) {
            action.execute(c);  // VERIFY: action does something
        }
        // MISSING: Mark quest complete in database!
    }
}
```

#### Scheduled Tasks
```java
public class RespawnWorker implements Runnable {
    @Override
    public void run() {
        // VERIFY: This actually runs on schedule
        for (MapleMap map : maps) {
            map.respawnMonsters();  // VERIFY: respawnMonsters() works
        }
    }
}

// Registration (VERIFY: actually scheduled)
scheduler.scheduleAtFixedRate(new RespawnWorker(), 0, 7000, TimeUnit.MILLISECONDS);
```

### Detection Rules for MapleStory Servers

| Pattern | Detection Method | Evidence Required |
|---------|------------------|-------------------|
| Missing packet handler | Opcode enum vs handler map | Registration proof |
| Empty handler | Handler method body analysis | Non-trivial code |
| Missing NPC script | npcId reference vs script file | Script file existence |
| Script references missing item | Script AST vs item data | Data cross-reference |
| Quest not completing | Quest handler vs DB write | Database write proof |
| Scheduler not running | Scheduler registration vs logs | Execution evidence |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| ast_graph | json | P1 | T0 | Yes | No |
| class_hierarchy | json | P1 | T0 | Yes | No |
| call_graph | json | P2 | T0 | Yes | No |
| packet_handler_map | json | P2 | T0 | Yes | No |
| script_references | json | P2 | T0 | Yes | No |
| jdbc_queries | json | P2 | T0 | Yes | No |
| coverage_report | jacoco | P4 | T0 | No | Yes |
| jfr_recording | jfr | P3 | T0 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Lombok | Generates code at compile time | Annotation processor | Delombok or include generated |
| 2 | Annotation processors | Code generated at build | Build-time generation | Include generated sources |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Reflection | Class.forName(), Method.invoke() | Dynamic loading | Minimize, document |
| 2 | Nashorn scripts | JavaScript embedded in Java | Cross-language | Script analysis |
| 3 | ServiceLoader | META-INF/services discovery | Dynamic discovery | Service manifest |
| 4 | Dynamic proxies | Proxy.newProxyInstance() | Interface-only | Interface analysis |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Spring beans | @Autowired injection | Container-managed | Spring config analysis |
| 2 | Servlet mapping | URL to handler | web.xml/annotations | Deployment descriptor |
| 3 | Timer scheduling | ScheduledExecutorService | Runtime registration | Scheduler audit |
| 4 | Script engine | ScriptEngine.eval() | Dynamic execution | Script inventory |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | JNI code | Native method calls | Binary, not Java | Interface documentation |
| 2 | Thread safety | Concurrent modifications | Non-deterministic | Thread safety analysis |
| 3 | Weak references | GC-dependent behavior | Non-deterministic | Explicit lifecycle |
| 4 | Classloader leaks | Memory leaks | Complex lifecycle | Profiling |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| SQL (JDBC) | database | Yes | Partial | Yes (schema) | P2 |
| JavaScript (Nashorn) | script | Partial | No | No | P5 |
| C/C++ (JNI) | ffi | Partial | No | No | P5 |
| XML (config) | file | Yes | Yes | Yes (XSD) | P2 |
| WZ/Data files | file | Yes | Yes | Partial | P2 |

### Common Boundary Patterns

```java
// Pattern 1: JDBC Database
PreparedStatement ps = con.prepareStatement(
    "UPDATE characters SET level = ? WHERE id = ?"
);
ps.setInt(1, newLevel);
ps.setInt(2, charId);
ps.executeUpdate();  // VERIFY: Actually updates

// Pattern 2: Nashorn Script (BLINDSPOT)
ScriptEngine engine = new ScriptEngineManager().getEngineByName("nashorn");
engine.eval(new FileReader("scripts/npc/" + npcId + ".js"));  // Cannot trace

// Pattern 3: Packet handling
public void handlePacket(SeekableLittleEndianAccessor slea, MapleClient c) {
    int itemId = slea.readInt();
    MapleItemInformationProvider.getInstance().getItem(itemId);  // VERIFY: item exists
}
```

---

## Failure Patterns

### Pattern 1: Unregistered Packet Handler

**Description:** Opcode exists but no handler registered

**Detection:** Compare RecvOpcode enum with handler registrations

**Example:**
```java
public enum RecvOpcode {
    PLAYER_MOVE(0x01),
    ATTACK(0x02),
    USE_CASH_ITEM(0x03);  // DETECTED: No handler for 0x03
}
```

### Pattern 2: Script References Missing Data

**Description:** NPC script references items/quests that don't exist

**Detection:** Parse script, cross-reference with data providers

**Example:**
```javascript
// scripts/npc/9000000.js
cm.gainItem(9999999);  // DETECTED: Item 9999999 not in data
cm.startQuest(99999);  // DETECTED: Quest 99999 not defined
```

### Pattern 3: Database Write Missing

**Description:** Game state changes but database not updated

**Detection:** Track state mutations vs PreparedStatement.execute*

**Example:**
```java
public void levelUp(MapleCharacter chr) {
    chr.setLevel(chr.getLevel() + 1);
    chr.setHp(chr.getMaxHp());
    // MISSING: chr.saveToDB();
}  // DETECTED: State changed, no DB write
```

### Pattern 4: Scheduler Never Starts

**Description:** Scheduled task defined but never registered

**Detection:** Find Runnable implementations, check scheduler registration

**Example:**
```java
public class EventTimer implements Runnable {
    public void run() { /* ... */ }
}
// DETECTED: EventTimer never passed to ScheduledExecutorService
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.97 × 0.15 = 0.146
    semantic_accuracy × 0.20 +        # 0.85 × 0.20 = 0.170
    wiring_completeness × 0.25 +      # 0.70 × 0.25 = 0.175
    runtime_capability × 0.25 +       # 0.85 × 0.25 = 0.213
    (1 - blindspot_penalty) × 0.15    # 0.65 × 0.15 = 0.098
)
```

**Current Score:** 0.80 (PRODUCTION)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with MapleStory server focus |
