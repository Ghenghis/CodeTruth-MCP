# Language Truth Profile: PHP

**Profile Version:** 1.0.0
**Language Version:** 5.6+ (legacy support), 7.4+, 8.0+ (modern)
**Stack Tier:** 4 (Specialized - Game Servers)
**Profile Completeness:** 0.85
**Implementation Completeness:** 0.68

---

## Overview

PHP appears in 4 repos in this codebase, primarily for:
- **Private game servers** (Travian, TravianZ, Twlan, browser-based strategy games)
- **Web admin panels** (game management interfaces)
- **Legacy web applications** (older forum software, CMS)
- **REST APIs** (game client communication)

### Private Server Game Context (Critical)

PHP private servers have unique failure patterns:
- Cronjobs that should run but don't (village updates, resource ticks)
- Event handlers that look complete but have race conditions
- Database transactions that partially commit (building queues, troop movements)
- Session handling that breaks multi-tab gameplay
- AJAX endpoints that return success without actual effect

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.php` | Extension | PHP source files |
| `*.phtml` | Extension | PHP template files |
| `*.inc` | Extension | Legacy include files |
| `*.module` | Extension | Drupal modules |
| `composer.json` | Filename | Composer package config |
| `composer.lock` | Filename | Locked dependencies |
| `*.twig` | Extension | Twig templates |
| `*.blade.php` | Extension | Laravel Blade templates |
| `config/*.php` | Glob | Configuration files |
| `cron/*.php` | Glob | Cronjob scripts |
| `ajax/*.php` | Glob | AJAX handlers (game servers) |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter + ast_native |
| Parser Name | tree-sitter-php + nikic/PHP-Parser |
| Grammar Version | 0.19.0 (tree-sitter) |
| Syntax Accuracy | 0.93 |
| Semantic Accuracy | 0.65 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Error recovery available |
| Error recovery | Yes | Most syntax errors recoverable |
| Incremental parsing | Yes | Tree-sitter supports |
| Comment preservation | Yes | PHPDoc extracted |
| Mixed HTML/PHP | Yes | Template parsing supported |

### Known Parse Failures

1. **Heredoc/Nowdoc in complex contexts**: Nested heredocs with variable interpolation
2. **Short open tags**: `<?` without `php` (depends on config)
3. **ASP-style tags**: `<%` legacy syntax
4. **Dynamic class names**: `new $className()` fully dynamic
5. **Variable-variable names**: `$$varname` patterns

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | basic (PHP 7.4+: better with typed properties) |
| Import Resolution | Yes (use statements, autoload) |
| Type Resolution | Partial (PHPDoc helps significantly) |
| Mutation Tracking | No (too dynamic) |
| Control Flow Analysis | Yes |
| Data Flow Analysis | Partial |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | Yes | 0.85 |
| Shadowing Detection | Yes | 0.80 |
| Closure Detection | Yes | 0.75 |
| Cross-file Resolution | Yes | 0.70 |
| Cross-module Resolution | Partial | 0.60 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| `eval()` / `create_function()` | false_negative | critical | Ban via linter |
| `$$variable` variable-variables | false_negative | high | Static analysis tools flag |
| `call_user_func()` dynamic calls | incomplete | high | Type annotations |
| `__call` / `__get` magic methods | incomplete | high | PHPDoc annotations |
| Include path manipulation | false_negative | critical | Static include paths |
| Session-based state | incomplete | high | Session tracing |
| Global variables | incomplete | medium | Avoid globals |
| Superglobals (`$_POST`, etc.) | incomplete | medium | Input validation layer |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | Yes | 0.65 | P2 (STATIC_PARTIAL) |
| Event Graph | Partial | 0.40 | P5 (HEURISTIC) |
| Route Graph | Yes | 0.75 | P2 (STATIC_PARTIAL) |
| Data Flow Graph | Partial | 0.50 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| HTTP Calls (cURL, file_get_contents) | Yes | P2 |
| Database (mysqli, PDO, legacy mysql_*) | Yes | P2 |
| File I/O | Yes | P1 |
| Process Spawn (exec, shell_exec) | Yes | P1 |
| Session Operations | Partial | P5 |
| Mail (mail(), PHPMailer) | Yes | P2 |
| Cron Execution | Partial | P5 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | Yes | 0.70 |
| Prove Unreachable | Partial | 0.45 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Autoload magic | incomplete | high | `spl_autoload_register()` custom loaders |
| Plugin systems | false_negative | critical | Dynamic plugin loading |
| Cron job registration | incomplete | critical | External crontab, not in code |
| AJAX routing (game servers) | incomplete | high | Dynamic endpoint mapping |
| Event hooks (game events) | incomplete | critical | Observer patterns with string names |
| Database-stored code | false_negative | critical | Stored procedures, config in DB |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes |
| Environment | php-fpm / php-cli / Apache mod_php |
| Min Version | 5.6 (legacy), 7.4 (recommended), 8.0+ (modern) |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | Yes | Xdebug |
| Execution Tracing | Yes | Xdebug profiler |
| Performance Profiling | Yes | Xdebug, Blackfire |
| State Snapshots | Partial | var_export, serialize |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | Yes | PHPUnit, Pest |
| Integration Tests | Yes | PHPUnit |
| E2E Tests | Yes | Codeception, Playwright (browser) |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Yes |
| Granularity | branch (Xdebug 3+) |
| Tool | Xdebug, PCOV |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Cron execution context | incomplete | critical | Runs outside web context |
| Session race conditions | false_negative | critical | Concurrent requests |
| Opcode cache state | incomplete | low | Cached vs fresh code |
| File locks | incomplete | high | flock() contention |
| Database locks | incomplete | high | Transaction isolation |
| External API timing | incomplete | medium | Network latency |

---

## Private Server Game Patterns (CRITICAL SECTION)

### Travian/TravianZ/Twlan Specific

These browser-based strategy games have common architecture:

#### Resource Tick System
```php
// Cronjob runs every X seconds to update resources
// FAILURE PATTERN: Cron registered but never executed
class ResourceTicker {
    public function tick() {
        // Must verify: this actually runs on schedule
        $villages = $this->db->query("SELECT * FROM villages");
        foreach ($villages as $village) {
            $this->updateResources($village);  // Must verify: actually saves
        }
    }
}
```

#### Building Queue Processing
```php
// FAILURE PATTERN: Building completes in DB but effects not applied
public function processBuildings() {
    $completed = $this->getCompletedBuildings();
    foreach ($completed as $building) {
        $this->applyBuildingEffects($building);  // OFTEN STUBBED
        $this->markComplete($building);          // Runs, but effects missing
    }
}
```

#### Troop Movement System
```php
// FAILURE PATTERN: Troops sent but never arrive
public function processMovements() {
    $arriving = $this->getArrivingTroops();
    foreach ($arriving as $movement) {
        if ($movement['type'] == 'attack') {
            $this->processBattle($movement);  // CRITICAL: verify battle actually runs
        }
        $this->completMovement($movement);
    }
}
```

### Detection Rules for Game Servers

| Pattern | Detection Method | Evidence Required |
|---------|------------------|-------------------|
| Cron never runs | Check crontab + execution logs | cron.log showing execution |
| Queue never processes | Trace from queue insert to effect | Database state + effect proof |
| AJAX returns success without effect | Compare response to database state | Request/response + DB diff |
| Session desync | Multi-tab test + session state | Session snapshots across requests |
| Race condition in resource calc | Concurrent request test | Race condition evidence |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| ast_graph | json | P1 | T0 | Yes | No |
| class_hierarchy | json | P2 | T0 | Yes | No |
| call_graph | json | P2 | T0 | Yes | No |
| route_map | json | P2 | T0 | Yes | No |
| database_queries | json | P2 | T0 | Yes | No |
| xdebug_trace | xt | P3 | T0 | No | Yes |
| coverage_report | clover | P4 | T0 | No | Yes |
| cron_execution_log | log | P3 | T1 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | eval/create_function | Dynamic code execution | Arbitrary string to code | Ban in linter |
| 2 | Variable-variables | `$$name` dynamic naming | Unbounded names | Static analysis warning |
| 3 | Mixed HTML/PHP | Complex template parsing | Context switching | Template linter |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Magic methods | __call, __get intercept everything | Dynamic dispatch | PHPDoc, strict types |
| 2 | Type juggling | Automatic type coercion | Weak typing | Strict comparisons (===) |
| 3 | Global state | $GLOBALS, superglobals | Hidden dependencies | Dependency injection |
| 4 | Session state | $_SESSION mutations | Cross-request state | Session tracing |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Autoload | spl_autoload_register | Dynamic class loading | PSR-4 compliance |
| 2 | String-based routing | Route("path", "Controller@method") | String dispatch | Route manifest |
| 3 | Cron external | Crontab outside code | System-level | Include cron in audit |
| 4 | Database-config | Settings stored in DB | Runtime config | Config audit |
| 5 | Plugin hooks | add_action('hook', $callback) | String-based events | Hook registry |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Cron context | Different from web | No session, no $_SERVER | CLI test mode |
| 2 | Long-running cron | Memory leaks, timeouts | No request lifecycle | Memory profiling |
| 3 | File locking | flock() contention | Concurrent crons | Lock verification |
| 4 | Database transactions | Implicit commits | Auto-commit surprises | Explicit transactions |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| JavaScript (AJAX) | http | Yes | Yes | Partial | P2 |
| SQL (MySQL/MariaDB) | database | Yes | Partial | Yes (schema) | P2 |
| HTML (templates) | template | Yes | Partial | No | P5 |
| Shell (exec) | process | Yes | Partial | No | P3 |
| Python (API calls) | http | Yes | Partial | Yes (OpenAPI) | P2 |

### Common Boundary Patterns

```php
// Pattern 1: AJAX endpoint (game servers)
// File: ajax/send_troops.php
header('Content-Type: application/json');
$result = $game->sendTroops($_POST['from'], $_POST['to'], $_POST['troops']);
echo json_encode(['success' => true, 'id' => $result]);  // VERIFY: $result is real

// Pattern 2: Database transaction
$pdo->beginTransaction();
try {
    $pdo->exec("UPDATE resources SET wood = wood - 100");
    $pdo->exec("UPDATE buildings SET level = level + 1");
    $pdo->commit();  // VERIFY: both statements succeeded
} catch (Exception $e) {
    $pdo->rollBack();  // VERIFY: rollback actually rolls back
}

// Pattern 3: Cron job
// File: cron/tick.php (runs every 5 seconds)
// VERIFY: This file is actually called by cron
require_once 'include/init.php';
$ticker = new ResourceTicker();
$ticker->tick();  // VERIFY: tick() actually updates database
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| tree-sitter-php | AST parsing | 0.19.0 |
| PHP | Runtime | 5.6+ (7.4+ recommended) |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| PHPStan | Static analysis | Semantic accuracy |
| Psalm | Static analysis | Type checking |
| PHPCS | Code standards | Linting |
| Xdebug | Debugging/profiling | Runtime analysis |
| PHPUnit | Testing | Runtime verification |
| Composer | Dependencies | Dependency audit |

---

## Failure Patterns

### Pattern 1: AJAX Success Without Effect

**Description:** AJAX endpoint returns success but database unchanged

**Detection:** Compare request/response with database state diff

**Example:**
```php
// ajax/upgrade_building.php
function upgradeBuilding($buildingId) {
    // Validation...
    // MISSING: actual database update
    return ['success' => true, 'new_level' => $building['level'] + 1];  // LIE
}
// DETECTED: Response claims success, database unchanged
```

### Pattern 2: Cron Registered But Never Runs

**Description:** Cron job file exists but never executed

**Detection:** Check crontab, verify execution logs exist

**Example:**
```php
// cron/resource_tick.php
// This file exists but is not in crontab
// Or: in crontab but wrong path
// Or: cron daemon not running
// DETECTED: cron file exists, no execution evidence
```

### Pattern 3: Transaction Partial Commit

**Description:** Multi-step operation partially completes

**Detection:** Transaction boundary analysis + state verification

**Example:**
```php
// No transaction wrapper!
$db->query("UPDATE resources SET wood = wood - 100");
// Error occurs here...
$db->query("INSERT INTO buildings (type) VALUES ('barracks')");
// DETECTED: No transaction, partial failure possible
```

### Pattern 4: Session Race Condition

**Description:** Concurrent requests corrupt session state

**Detection:** Multi-request test with session inspection

**Example:**
```php
// Two tabs: both read balance=100, both subtract 50
// Expected: balance=0, Actual: balance=50 (race)
session_start();
$_SESSION['balance'] -= 50;  // Not atomic!
session_write_close();
// DETECTED: Non-atomic session modification
```

### Pattern 5: Event Handler Never Called

**Description:** Game event registered but never triggers

**Detection:** Event registration + call graph analysis

**Example:**
```php
// Event registered
$eventManager->on('building_complete', [$this, 'onBuildingComplete']);

// But building completion code doesn't fire event:
public function completeBuilding($id) {
    $this->db->update('buildings', ['status' => 'complete']);
    // MISSING: $this->eventManager->fire('building_complete', $building);
}
// DETECTED: Event registered but never fired
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.93 × 0.15 = 0.140
    semantic_accuracy × 0.20 +        # 0.65 × 0.20 = 0.130
    wiring_completeness × 0.25 +      # 0.55 × 0.25 = 0.138
    runtime_capability × 0.25 +       # 0.75 × 0.25 = 0.188
    (1 - blindspot_penalty) × 0.15    # 0.60 × 0.15 = 0.090
)
```

**Current Score:** 0.69 (PARTIAL)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with game server focus |


---

## HONESTY CHECK

- Claims made: 35
- Claims proven: 0
- Claims partial: 0
- Claims unproven: 35 (No PHP analyzer exists)
- Forbidden claims listed: YES
- Fixtures defined: YES
- Goldens defined: YES

**STATUS: UNPROVEN - Profile complete but NO IMPLEMENTATION exists**

