# Boundary Contract Verifier

**Version:** 1.0.0
**Status:** PARTIAL
**Proof Level:** P5 (HEURISTIC)
**Overall Confidence:** 0.55

---

## Purpose

The Boundary Contract Verifier addresses where real apps fail:

> **"Does the caller and callee agree on the contract?"**

Boundaries are where "complete but broken" hides:
- UI expects `{user: {id, name}}`, API returns `{id, name}`
- Node spawns Python script with wrong arguments
- Frontend uses v2 API, backend only implements v1
- File format expected by reader doesn't match writer

---

## Boundary Types

### Type 1: HTTP/REST API

**Boundary:** Frontend → Backend API

**Contract:** OpenAPI/Swagger specification

**Verification:**
```python
async def verify_http_boundary(
    caller_code: Path,
    api_spec: Path,
    runtime_har: Optional[Path]
) -> BoundaryResult:
    """
    Verify HTTP API contract compliance.

    1. Extract API calls from caller code
    2. Parse OpenAPI spec
    3. Compare request/response schemas
    4. If HAR available, verify actual payloads
    """
    # Static: Extract fetch/axios calls
    api_calls = extract_api_calls(caller_code)

    # Static: Parse OpenAPI spec
    spec = parse_openapi(api_spec)

    violations = []
    for call in api_calls:
        endpoint = spec.get_endpoint(call.method, call.path)

        if endpoint is None:
            violations.append(Violation(
                type="ENDPOINT_NOT_FOUND",
                detail=f"{call.method} {call.path} not in spec",
                severity="CRITICAL"
            ))
            continue

        # Check request body schema
        if call.body and endpoint.request_body:
            if not schemas_compatible(call.body_schema, endpoint.request_body):
                violations.append(Violation(
                    type="REQUEST_SCHEMA_MISMATCH",
                    detail=f"Request body doesn't match spec",
                    caller_expects=call.body_schema,
                    spec_expects=endpoint.request_body
                ))

        # Check response handling
        if call.response_handler:
            if not schemas_compatible(endpoint.response_schema, call.expected_response):
                violations.append(Violation(
                    type="RESPONSE_SCHEMA_MISMATCH",
                    detail=f"Response handling doesn't match spec",
                    caller_expects=call.expected_response,
                    spec_provides=endpoint.response_schema
                ))

    # Dynamic: Verify against actual runtime data
    if runtime_har:
        har_violations = verify_against_har(api_calls, runtime_har)
        violations.extend(har_violations)

    return BoundaryResult(
        boundary_type="HTTP_API",
        violations=violations,
        confidence=0.85 if runtime_har else 0.60
    )
```

### Type 2: Process/IPC

**Boundary:** Node → Python, Python → Shell, etc.

**Contract:** Argument schema, stdin/stdout format

**Verification:**
```python
async def verify_process_boundary(
    caller_code: Path,
    callee_code: Path
) -> BoundaryResult:
    """
    Verify process spawn contract.

    1. Find spawn calls (subprocess, child_process, etc.)
    2. Extract expected arguments
    3. Parse callee's argument handling
    4. Compare schemas
    """
    # Find spawn calls
    spawn_calls = extract_spawn_calls(caller_code)

    violations = []
    for spawn in spawn_calls:
        # Find callee file
        callee = resolve_callee(spawn.command, callee_code)

        if callee is None:
            violations.append(Violation(
                type="CALLEE_NOT_FOUND",
                detail=f"Cannot find: {spawn.command}",
                severity="CRITICAL"
            ))
            continue

        # Parse callee's argument handling
        callee_args = parse_argument_handler(callee)

        # Compare
        if spawn.args and callee_args:
            mismatches = compare_args(spawn.args, callee_args)
            for mismatch in mismatches:
                violations.append(Violation(
                    type="ARGUMENT_MISMATCH",
                    detail=mismatch.detail,
                    caller_provides=mismatch.caller,
                    callee_expects=mismatch.callee
                ))

    return BoundaryResult(
        boundary_type="PROCESS_IPC",
        violations=violations,
        confidence=0.55
    )
```

### Type 3: Database Schema

**Boundary:** Application → Database

**Contract:** Database schema, ORM models

**Verification:**
```python
async def verify_database_boundary(
    app_code: Path,
    db_schema: Path
) -> BoundaryResult:
    """
    Verify database schema contract.

    1. Extract ORM models from app code
    2. Parse database schema (SQL, migrations)
    3. Compare column types, constraints
    """
    # Extract ORM models
    orm_models = extract_orm_models(app_code)

    # Parse DB schema
    db_tables = parse_db_schema(db_schema)

    violations = []
    for model in orm_models:
        table = db_tables.get(model.table_name)

        if table is None:
            violations.append(Violation(
                type="TABLE_NOT_FOUND",
                detail=f"Table '{model.table_name}' not in schema"
            ))
            continue

        # Check columns
        for column in model.columns:
            db_column = table.get_column(column.name)

            if db_column is None:
                violations.append(Violation(
                    type="COLUMN_NOT_FOUND",
                    detail=f"Column '{column.name}' not in table '{table.name}'"
                ))
            elif not types_compatible(column.type, db_column.type):
                violations.append(Violation(
                    type="TYPE_MISMATCH",
                    detail=f"Column type mismatch: {column.type} vs {db_column.type}"
                ))

    return BoundaryResult(
        boundary_type="DATABASE",
        violations=violations,
        confidence=0.80
    )
```

### Type 4: Message Queue

**Boundary:** Publisher → Consumer

**Contract:** Message schema, queue name, routing

**Verification:**
```python
async def verify_queue_boundary(
    publisher_code: Path,
    consumer_code: Path
) -> BoundaryResult:
    """
    Verify message queue contract.

    1. Extract publish calls
    2. Extract consume/subscribe handlers
    3. Compare message schemas
    4. Check queue name matching
    """
    # Extract publishers
    publishers = extract_publishers(publisher_code)

    # Extract consumers
    consumers = extract_consumers(consumer_code)

    violations = []

    # Check queue name matching
    published_queues = set(p.queue for p in publishers)
    consumed_queues = set(c.queue for c in consumers)

    orphan_publishers = published_queues - consumed_queues
    orphan_consumers = consumed_queues - published_queues

    for queue in orphan_publishers:
        violations.append(Violation(
            type="QUEUE_NO_CONSUMER",
            detail=f"Queue '{queue}' has publishers but no consumers"
        ))

    for queue in orphan_consumers:
        violations.append(Violation(
            type="QUEUE_NO_PUBLISHER",
            detail=f"Queue '{queue}' has consumers but no publishers"
        ))

    # Check message schema compatibility
    for queue in published_queues & consumed_queues:
        pub_schema = get_message_schema(publishers, queue)
        con_schema = get_expected_schema(consumers, queue)

        if not schemas_compatible(pub_schema, con_schema):
            violations.append(Violation(
                type="MESSAGE_SCHEMA_MISMATCH",
                detail=f"Message schema mismatch for queue '{queue}'"
            ))

    return BoundaryResult(
        boundary_type="MESSAGE_QUEUE",
        violations=violations,
        confidence=0.50
    )
```

### Type 5: File Format

**Boundary:** Writer → Reader

**Contract:** File format specification

**Verification:**
```python
async def verify_file_boundary(
    writer_code: Path,
    reader_code: Path,
    format_spec: Optional[Path]
) -> BoundaryResult:
    """
    Verify file format contract.

    1. Extract file write operations
    2. Extract file read operations
    3. Compare expected formats
    4. Check field names, types
    """
    # Extract writes
    writers = extract_file_writes(writer_code)

    # Extract reads
    readers = extract_file_reads(reader_code)

    violations = []

    for writer in writers:
        matching_readers = [r for r in readers if r.filename_pattern.matches(writer.filename)]

        for reader in matching_readers:
            if not formats_compatible(writer.output_format, reader.expected_format):
                violations.append(Violation(
                    type="FILE_FORMAT_MISMATCH",
                    detail=f"Writer outputs {writer.output_format}, reader expects {reader.expected_format}"
                ))

    return BoundaryResult(
        boundary_type="FILE_FORMAT",
        violations=violations,
        confidence=0.45
    )
```

---

## Cross-Language Detection

### Supported Boundaries

| Caller | Callee | Detection Method | Confidence |
|--------|--------|------------------|------------|
| TypeScript | Python (API) | HTTP request extraction | 0.75 |
| TypeScript | Node.js | Import tracing | 0.90 |
| Python | PostgreSQL | ORM/query detection | 0.80 |
| Python | Shell | Subprocess detection | 0.60 |
| Node.js | Python | child_process detection | 0.60 |
| PowerShell | Python | Process spawn detection | 0.50 |
| Lua | C/C++ (engine) | FFI detection | 0.40 |
| C# | SQL Server | ADO.NET/EF detection | 0.80 |
| Java | MySQL | JDBC detection | 0.75 |
| PHP | MySQL | mysqli/PDO detection | 0.75 |

### Detection Patterns

```python
BOUNDARY_PATTERNS = {
    "http_client": {
        "typescript": [
            r"fetch\s*\(",
            r"axios\.(get|post|put|delete)",
            r"http\.request",
        ],
        "python": [
            r"requests\.(get|post|put|delete)",
            r"httpx\.(get|post|put|delete)",
            r"aiohttp\.ClientSession",
        ],
    },
    "subprocess": {
        "python": [
            r"subprocess\.(run|call|Popen)",
            r"os\.system",
            r"os\.popen",
        ],
        "typescript": [
            r"child_process\.(exec|spawn|fork)",
            r"execSync",
            r"spawnSync",
        ],
        "powershell": [
            r"Start-Process",
            r"Invoke-Expression",
            r"\&\s+",
        ],
    },
    "database": {
        "python": [
            r"session\.(query|execute|add)",
            r"cursor\.execute",
            r"prisma\.",
        ],
        "typescript": [
            r"prisma\.\w+\.(find|create|update|delete)",
            r"knex\(",
            r"sequelize\.",
        ],
    },
}
```

---

## Contract Verification

### OpenAPI Contract

```python
def verify_openapi_contract(
    frontend_calls: List[APICall],
    openapi_spec: OpenAPISpec
) -> List[Violation]:
    """
    Verify frontend API calls against OpenAPI spec.
    """
    violations = []

    for call in frontend_calls:
        # Find matching operation
        operation = openapi_spec.find_operation(call.method, call.path)

        if not operation:
            violations.append(Violation(
                type="UNKNOWN_ENDPOINT",
                detail=f"{call.method} {call.path} not in spec",
                location=call.location
            ))
            continue

        # Verify request parameters
        for param in call.params:
            spec_param = operation.get_parameter(param.name)
            if not spec_param:
                violations.append(Violation(
                    type="UNKNOWN_PARAMETER",
                    detail=f"Parameter '{param.name}' not in spec"
                ))
            elif not type_matches(param.type, spec_param.schema):
                violations.append(Violation(
                    type="PARAMETER_TYPE_MISMATCH",
                    detail=f"Parameter '{param.name}' type mismatch"
                ))

        # Verify request body
        if call.body:
            if not operation.request_body:
                violations.append(Violation(
                    type="UNEXPECTED_BODY",
                    detail="Request body sent but not expected"
                ))
            elif not schema_matches(call.body_schema, operation.request_body.schema):
                violations.append(Violation(
                    type="BODY_SCHEMA_MISMATCH",
                    detail="Request body doesn't match spec"
                ))

        # Verify response handling
        if call.response_usage:
            success_response = operation.get_response(200)
            if success_response and not schema_matches(
                call.expected_response_schema,
                success_response.schema
            ):
                violations.append(Violation(
                    type="RESPONSE_SCHEMA_MISMATCH",
                    detail="Response handling doesn't match spec"
                ))

    return violations
```

---

## Output Schema

### Boundary Report

```json
{
  "repo_path": "/path/to/repo",
  "analysis_timestamp": "2024-01-18T12:00:00Z",
  "boundaries_found": 15,
  "boundaries_verified": 12,
  "boundaries_failed": 3,
  "violations": [
    {
      "boundary_type": "HTTP_API",
      "caller": {
        "file": "src/api/client.ts",
        "line": 45,
        "call": "fetch('/api/users')"
      },
      "callee": {
        "spec": "openapi.yaml",
        "endpoint": "/api/users"
      },
      "violation_type": "RESPONSE_SCHEMA_MISMATCH",
      "detail": "Caller expects {users: User[]}, spec defines {data: User[]}",
      "severity": "HIGH",
      "confidence": 0.85
    }
  ],
  "unverified_boundaries": [
    {
      "type": "LUA_FFI",
      "reason": "Cannot verify C++ engine calls from Lua"
    }
  ],
  "overall_confidence": 0.55
}
```

---

## Limitations (MANDATORY)

### What This Engine CANNOT Verify

1. **Runtime-only contracts**
   - Contracts defined at runtime (env vars, config files)
   - Mitigation: Config file analysis

2. **Dynamic schema generation**
   - Schemas generated from code
   - Mitigation: Run schema generator first

3. **FFI/Native calls**
   - Lua → C++, Python → C, etc.
   - Mitigation: Interface header analysis

4. **Undocumented APIs**
   - No OpenAPI spec available
   - Mitigation: Generate from code

5. **Version mismatches**
   - Using wrong version of spec
   - Mitigation: Version pinning

6. **Custom serialization**
   - Non-standard JSON/XML formats
   - Mitigation: Schema documentation

### What MUST Be Labeled UNPROVEN

- Boundaries without specs: `UNPROVEN (no contract defined)`
- FFI boundaries: `UNPROVEN (native code boundary)`
- Dynamic endpoints: `UNPROVEN (dynamic path)`
- External APIs: `UNPROVEN (external system)`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial specification |
