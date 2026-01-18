# Language Truth Profile: SQL

**Profile Version:** 1.0.0
**Language Version:** SQL:2016 (with dialect variants)
**Stack Tier:** 4 (Data Layer)
**Profile Completeness:** 0.85
**Implementation Completeness:** 0.78

---

## Overview

SQL defines database schemas, queries, and stored procedures. In the user's 589+ repos, SQL appears in:
- MySQL/MariaDB for game servers (MapleStory, Travian, TWLan)
- PostgreSQL for web applications
- SQLite for local storage and testing
- Migration files (Prisma, Drizzle, raw SQL)
- Stored procedures and triggers

SQL verification focuses on **schema integrity**, **query validity**, **migration safety**, and **injection vulnerability detection**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.sql` | Extension | SQL files |
| `*.mysql` | Extension | MySQL-specific |
| `*.pgsql` | Extension | PostgreSQL-specific |
| `*.sqlite` | Extension | SQLite files |
| `migrations/*.sql` | Glob | Migration files |
| `schema.sql` | Filename | Schema definitions |
| `seed.sql` | Filename | Seed data |
| `*.prisma` | Extension | Prisma schema (SQL-adjacent) |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-sql |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.92 |
| Semantic Accuracy | 0.75 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Statement-level recovery |
| Error recovery | Partial | Complex queries may fail |
| Incremental parsing | Yes | Supported |
| Comment preservation | Yes | -- and /* */ |
| Dialect support | Partial | MySQL, PostgreSQL, SQLite |

### Known Parse Failures

1. **Vendor extensions**: MySQL-specific syntax in PostgreSQL parser
2. **Dynamic SQL**: EXECUTE IMMEDIATE, sp_executesql
3. **JSON operators**: ->>, ->, @> variations
4. **Window functions**: Complex OVER clauses
5. **CTEs with recursion**: Deep recursive structures

---

## Semantic Capability

### Schema Analysis

| Property | Value |
|----------|-------|
| Table Definition | Yes |
| Column Types | Yes |
| Constraint Parsing | Yes |
| Index Analysis | Yes |
| Foreign Key Tracking | Yes |
| View Resolution | Partial |

### Query Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| SELECT parsing | Yes | 0.95 |
| JOIN resolution | Yes | 0.90 |
| WHERE clause analysis | Yes | 0.85 |
| Subquery resolution | Partial | 0.75 |
| Aggregate functions | Yes | 0.90 |
| Window functions | Partial | 0.70 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Dynamic SQL | false_negative | critical | Runtime tracing |
| Stored procedure bodies | incomplete | high | Procedure parsing |
| Triggers | incomplete | high | Trigger analysis |
| Views with complexity | incomplete | medium | View expansion |
| Cross-database references | incomplete | medium | Multi-schema analysis |
| Runtime schema changes | false_negative | critical | Migration tracking |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Schema Graph | Yes | 0.90 | P1 (STATIC_COMPLETE) |
| FK Relationship Graph | Yes | 0.95 | P1 (STATIC_COMPLETE) |
| Query-Table Graph | Yes | 0.85 | P2 (STATIC_PARTIAL) |
| Procedure Call Graph | Partial | 0.60 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| Table references | Yes | P1 |
| Column references | Yes | P1 |
| Foreign keys | Yes | P1 |
| Stored procedure calls | Partial | P3 |
| External data sources | Partial | P5 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Table Exists | Yes | 0.99 |
| Prove Column Exists | Yes | 0.99 |
| Prove FK Valid | Yes | 0.99 |
| Prove Query Valid | Partial | 0.80 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Dynamic table names | false_negative | critical | `EXECUTE 'SELECT * FROM ' || tbl` |
| ORM-generated queries | incomplete | high | Prisma/Sequelize abstractions |
| Migration ordering | incomplete | high | Dependent migrations |
| Soft deletes | incomplete | medium | `deleted_at IS NULL` convention |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes (requires database) |
| Environment | MySQL, PostgreSQL, SQLite |
| Min Version | Varies by dialect |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Query Profiling | Yes | EXPLAIN, EXPLAIN ANALYZE |
| Slow Query Log | Yes | Database logs |
| Query Statistics | Yes | pg_stat_statements, etc. |
| Lock Analysis | Yes | Database tools |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Schema Tests | Yes | pgTAP, SQLAlchemy tests |
| Data Tests | Yes | Great Expectations, dbt |
| Migration Tests | Yes | Test database + rollback |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Partial |
| Granularity | statement |
| Tool | Query logs |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Production data | incomplete | critical | Cannot test with real data |
| Concurrency | incomplete | high | Race conditions |
| Scale behavior | incomplete | high | Performance at scale |
| Lock contention | incomplete | medium | Workload dependent |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| schema_graph | json | P1 | T0 | Yes | No |
| table_inventory | json | P1 | T0 | Yes | No |
| fk_graph | json | P1 | T0 | Yes | No |
| query_analysis | json | P2 | T0 | Yes | No |
| explain_plan | json | P3 | T1 | No | Yes |
| migration_graph | json | P2 | T0 | Yes | No |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Dialect variations | MySQL vs PostgreSQL vs SQLite | Different grammars | Dialect detection |
| 2 | Dynamic SQL | String-built queries | Impossible statically | Runtime capture |
| 3 | Vendor extensions | Custom functions/syntax | Non-standard | Vendor-specific parser |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Runtime schema | ALTER TABLE after CREATE | Temporal | Migration ordering |
| 2 | Stored procedure bodies | Complex procedural logic | Different syntax | Procedure parser |
| 3 | Views | Computed columns | Requires expansion | View resolution |
| 4 | Implicit conversions | Type coercion | Database-specific | Type analysis |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | ORM abstraction | Generated queries | Build-time | ORM schema analysis |
| 2 | Dynamic table names | Table name in variable | Runtime value | Query logging |
| 3 | Cross-database | References to other databases | Scope limitation | Multi-database scan |
| 4 | Soft delete conventions | deleted_at patterns | Application logic | Convention detection |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Production data | Real data behavior | Cannot access | Synthetic data testing |
| 2 | Concurrency bugs | Race conditions | Non-deterministic | Transaction testing |
| 3 | Performance at scale | Index effectiveness | Data volume dependent | EXPLAIN ANALYZE |
| 4 | Connection pooling | Pool exhaustion | Load dependent | Load testing |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| Python (ORM) | abstraction | Partial | Partial | Partial | P3 |
| TypeScript (Prisma) | abstraction | Yes | Partial | Yes | P2 |
| PHP (raw queries) | embed | Partial | No | No | P5 |
| Java (JDBC) | api | Partial | Partial | No | P4 |

### Common Boundary Patterns

```sql
-- Pattern 1: Query from PHP
-- SELECT * FROM users WHERE id = $userId
-- VERIFICATION: Check $userId is sanitized (SQL injection risk)

-- Pattern 2: ORM-generated
-- Prisma: prisma.user.findMany({ where: { active: true } })
-- Generates: SELECT * FROM "User" WHERE "active" = true
-- VERIFICATION: Cross-reference Prisma schema with actual DB

-- Pattern 3: Migration dependency
-- Migration 002 depends on Migration 001
-- VERIFICATION: Must run in order, check for missing migrations
```

---

## Game Server Specific Patterns

### MapleStory Database

```sql
-- Pattern: Character data tables
CREATE TABLE characters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    accountid INT NOT NULL,
    name VARCHAR(13) NOT NULL,
    level INT DEFAULT 1,
    exp INT DEFAULT 0,
    job INT DEFAULT 0,
    str INT DEFAULT 4,
    dex INT DEFAULT 4,
    int_ INT DEFAULT 4,  -- Reserved keyword workaround
    luk INT DEFAULT 4,
    hp INT DEFAULT 50,
    mp INT DEFAULT 5,
    maxhp INT DEFAULT 50,
    maxmp INT DEFAULT 5,
    mesos INT DEFAULT 0,
    FOREIGN KEY (accountid) REFERENCES accounts(id)
);

-- DETECTION RULES:
-- 1. Check FK to accounts exists
-- 2. Check for indexes on frequently queried columns (accountid, name)
-- 3. Check for missing NOT NULL where needed
```

### Travian/TWLan Database

```sql
-- Pattern: Resource and building tables
CREATE TABLE villages (
    id INT PRIMARY KEY,
    owner INT NOT NULL,
    wood INT DEFAULT 0,
    clay INT DEFAULT 0,
    iron INT DEFAULT 0,
    crop INT DEFAULT 0,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(id)
);

-- Pattern: Building queue (potential cron job dependency)
CREATE TABLE building_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    village_id INT NOT NULL,
    building_type INT NOT NULL,
    target_level INT NOT NULL,
    finish_time TIMESTAMP NOT NULL,
    FOREIGN KEY (village_id) REFERENCES villages(id)
);

-- DETECTION RULES:
-- 1. Cron job must process finish_time < NOW()
-- 2. Check for indexes on finish_time for cron efficiency
-- 3. Verify cascading deletes on village deletion
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| tree-sitter-sql | Parsing | 0.20.0 |
| Database client | Validation | Varies |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| sqlfluff | Linting | Parse accuracy |
| pgAdmin/MySQL Workbench | Schema visualization | Wiring analysis |
| dbt | Testing | Runtime verification |

---

## Failure Patterns

### Pattern 1: Missing Foreign Key Target

**Description:** FK references non-existent table or column

**Detection:** Cross-reference FK definitions with table inventory

**Example:**
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT REFERENCES nonexistent_table(id)  -- DETECTED: Table doesn't exist
);
```

### Pattern 2: Column Type Mismatch

**Description:** FK column type doesn't match referenced column

**Detection:** Compare column types across FK relationships

**Example:**
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(id)  -- DETECTED: customers.id is INT
);
```

### Pattern 3: Missing Index on FK

**Description:** Foreign key without index (performance issue)

**Detection:** Check FK columns have corresponding indexes

**Example:**
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT REFERENCES customers(id)
    -- DETECTED: No index on customer_id, will cause slow JOINs
);
```

### Pattern 4: SQL Injection Vector

**Description:** Query built with string concatenation

**Detection:** Pattern matching on query construction

**Example:**
```php
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
// DETECTED: SQL injection vulnerability
```

### Pattern 5: Orphaned Migration

**Description:** Migration references column/table from skipped migration

**Detection:** Migration dependency graph analysis

**Example:**
```sql
-- Migration 003_add_column.sql
ALTER TABLE users ADD COLUMN role VARCHAR(50);
-- But migration 001_create_users.sql was never run
-- DETECTED: Table 'users' does not exist
```

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "Schema is complete" | Migrations may be pending | Migration status check |
| "All queries are safe" | SQL injection from app code | Security scan results |
| "No data integrity issues" | Runtime data needed | Constraint validation |
| "Indexes are optimal" | Workload dependent | EXPLAIN ANALYZE under load |
| "No orphan records" | FK cascade behavior | Data integrity scan |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: FK to Nowhere

**Purpose:** Tests detection of invalid foreign keys

**File:** `fixtures/sql/fk-to-nowhere/`

**Expected Findings:**
- CRITICAL: FK references non-existent table 'nonexistent'
- HIGH: FK column type INT doesn't match target VARCHAR

**Forbidden False Positives:**
- Should NOT flag FKs to tables defined in other files
- Should NOT flag cross-database FKs (mark as UNVERIFIED)

### Fixture 2: Migration Disorder

**Purpose:** Tests detection of out-of-order migrations

**File:** `fixtures/sql/migration-disorder/`

**Expected Findings:**
- CRITICAL: Migration 003 references table created in migration 005
- HIGH: Migration 002 skipped but 003 depends on it

**Forbidden False Positives:**
- Should NOT flag independent migrations that can run in any order

---

## Golden Output Expectations (MANDATORY SECTION)

### Golden 1: FK to Nowhere

```json
{
  "findings": [
    {
      "type": "invalid_foreign_key",
      "severity": "critical",
      "location": "schema.sql:45",
      "message": "Foreign key references non-existent table 'nonexistent'",
      "proof_level": "P1",
      "evidence": "schema_graph_20240118_001"
    }
  ],
  "confidence": 0.99,
  "blindspots_acknowledged": [
    "Cross-database references not verified",
    "Runtime schema changes not tracked"
  ]
}
```

### Golden 2: Migration Disorder

```json
{
  "findings": [
    {
      "type": "migration_dependency_error",
      "severity": "critical",
      "location": "migrations/003_add_column.sql:1",
      "message": "Migration references table 'users' which is created in migration 005",
      "proof_level": "P2",
      "evidence": "migration_graph_20240118_001"
    }
  ],
  "confidence": 0.95,
  "blindspots_acknowledged": [
    "Manual migration execution order unknown",
    "Migration rollback state not tracked"
  ]
}
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.92 × 0.15 = 0.138
    semantic_accuracy × 0.20 +        # 0.75 × 0.20 = 0.150
    wiring_completeness × 0.25 +      # 0.80 × 0.25 = 0.200
    runtime_capability × 0.25 +       # 0.70 × 0.25 = 0.175
    (1 - blindspot_penalty) × 0.15    # 0.65 × 0.15 = 0.098
)
```

**Current Score:** 0.76 (PARTIAL - dynamic SQL and ORM abstraction blindspots)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with game server patterns |
