# Fixtures and Golden Tests

**Version:** 1.0.0
**Status:** AUTHORITATIVE

---

## Purpose

This document defines intentionally broken code fixtures that CodeTruth MUST detect. If CodeTruth fails to detect these issues, it fails itself.

> **A system that cannot catch intentional failures cannot catch unintentional ones.**

---

## Fixture Categories

1. **UI No-Op** - UI that looks complete but does nothing
2. **API Never Mounted** - Routes defined but never registered
3. **Handler Never Called** - Event handlers with no bindings
4. **Fake Success** - Code that returns success without action
5. **Test Without Assert** - Tests that always pass
6. **Cron Never Runs** - Scheduled code that's not scheduled
7. **Dead Code** - Code with no path from entry point
8. **Type Lie** - Types that don't match runtime
9. **Boundary Mismatch** - Caller/callee contract violation
10. **Stub Hell** - All placeholders, no implementation

---

## Fixture 1: UI No-Op Button

### Description
A button that appears functional but does nothing when clicked.

### Files

**`src/components/SaveButton.tsx`**
```tsx
import React from 'react';

export function SaveButton({ data }) {
  const handleSave = async () => {
    // TODO: Implement save functionality
    console.log('Save clicked');
  };

  return (
    <button
      onClick={handleSave}
      className="btn-primary"
    >
      Save Changes
    </button>
  );
}
```

### Expected Finding

```json
{
  "finding_type": "NO_OP_UI",
  "severity": "CRITICAL",
  "location": {
    "file": "src/components/SaveButton.tsx",
    "line": 4,
    "element": "button:text('Save Changes')"
  },
  "evidence": {
    "static": {
      "handler_body": "console.log('Save clicked')",
      "pattern": "CONSOLE_ONLY"
    },
    "dynamic": {
      "network_requests": [],
      "state_changes": [],
      "dom_mutations": []
    }
  },
  "message": "Button 'Save Changes' handler only logs to console, produces no observable effect"
}
```

### Forbidden Claims
- ❌ "Button is functional"
- ❌ "Feature is complete"
- ❌ No finding at all

---

## Fixture 2: API Route Never Mounted

### Description
A FastAPI route that is defined but never included in the app.

### Files

**`src/routes/admin.py`**
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/admin/users")
async def list_admin_users():
    return {"users": []}

@router.post("/admin/delete-user/{user_id}")
async def delete_user(user_id: int):
    return {"deleted": True}
```

**`src/main.py`**
```python
from fastapi import FastAPI
from src.routes.users import router as users_router
# Note: admin_router is NOT imported or included

app = FastAPI()
app.include_router(users_router, prefix="/api")
# admin_router NOT included!
```

### Expected Finding

```json
{
  "finding_type": "ROUTE_NEVER_MOUNTED",
  "severity": "CRITICAL",
  "locations": [
    {
      "file": "src/routes/admin.py",
      "line": 6,
      "route": "GET /admin/users"
    },
    {
      "file": "src/routes/admin.py",
      "line": 11,
      "route": "POST /admin/delete-user/{user_id}"
    }
  ],
  "evidence": {
    "routes_defined": ["GET /admin/users", "POST /admin/delete-user/{user_id}"],
    "app_includes": ["src.routes.users"],
    "missing_includes": ["src.routes.admin"]
  },
  "message": "Admin routes defined but never included in FastAPI app"
}
```

### Forbidden Claims
- ❌ "Admin API is available"
- ❌ "2 routes successfully defined"

---

## Fixture 3: Event Handler Never Bound

### Description
An event handler function that exists but is never attached to any element.

### Files

**`src/handlers.ts`**
```typescript
export function handleFormSubmit(event: Event) {
  event.preventDefault();
  const form = event.target as HTMLFormElement;
  const data = new FormData(form);
  fetch('/api/submit', {
    method: 'POST',
    body: data
  });
}

export function handleCancel() {
  window.location.href = '/';
}
```

**`src/Form.tsx`**
```tsx
import { handleFormSubmit } from './handlers';
// Note: handleCancel is imported but never used

export function ContactForm() {
  return (
    <form onSubmit={handleFormSubmit}>
      <input name="email" />
      <button type="submit">Submit</button>
      {/* Cancel button has no handler! */}
      <button type="button">Cancel</button>
    </form>
  );
}
```

### Expected Finding

```json
{
  "finding_type": "HANDLER_NEVER_BOUND",
  "severity": "HIGH",
  "location": {
    "file": "src/handlers.ts",
    "line": 12,
    "function": "handleCancel"
  },
  "evidence": {
    "handler_defined": true,
    "handler_exported": true,
    "binding_locations_searched": ["src/**/*.tsx", "src/**/*.ts"],
    "bindings_found": []
  },
  "related": {
    "unhandled_element": {
      "file": "src/Form.tsx",
      "line": 9,
      "element": "button:text('Cancel')"
    }
  },
  "message": "Handler 'handleCancel' is defined and exported but never bound to any element"
}
```

---

## Fixture 4: Fake Success Return

### Description
A function that returns success without actually doing anything.

### Files

**`src/services/orderService.ts`**
```typescript
interface Order {
  id: string;
  items: string[];
  total: number;
}

export async function createOrder(order: Order): Promise<{ success: boolean; orderId: string }> {
  // TODO: Actually save to database

  // Just return a fake success!
  return {
    success: true,
    orderId: `ORD-${Date.now()}`
  };
}
```

### Expected Finding

```json
{
  "finding_type": "FAKE_SUCCESS_RETURN",
  "severity": "CRITICAL",
  "location": {
    "file": "src/services/orderService.ts",
    "line": 8,
    "function": "createOrder"
  },
  "evidence": {
    "returns_success": true,
    "database_operations": [],
    "network_operations": [],
    "side_effects": [],
    "contains_todo": true,
    "todo_text": "TODO: Actually save to database"
  },
  "message": "Function 'createOrder' returns success without performing any database or network operation"
}
```

---

## Fixture 5: Test Without Assertions

### Description
Tests that always pass because they have no assertions.

### Files

**`src/utils.ts`**
```typescript
export function calculateTotal(items: number[]): number {
  return items.reduce((sum, item) => sum + item, 0);
}
```

**`tests/utils.test.ts`**
```typescript
import { calculateTotal } from '../src/utils';

describe('calculateTotal', () => {
  it('should calculate total correctly', () => {
    const result = calculateTotal([1, 2, 3]);
    // Missing assertion!
    console.log('Result:', result);
  });

  it('should handle empty array', () => {
    calculateTotal([]);
    // No assertion at all
  });
});
```

### Expected Finding

```json
{
  "finding_type": "TEST_WITHOUT_ASSERTION",
  "severity": "HIGH",
  "locations": [
    {
      "file": "tests/utils.test.ts",
      "line": 4,
      "test_name": "should calculate total correctly"
    },
    {
      "file": "tests/utils.test.ts",
      "line": 10,
      "test_name": "should handle empty array"
    }
  ],
  "evidence": {
    "tests_analyzed": 2,
    "tests_with_assertions": 0,
    "assertion_patterns_searched": ["expect(", "assert", "should.", "toBe", "toEqual"]
  },
  "message": "2 tests have no assertions and will always pass"
}
```

---

## Fixture 6: PHP Cron Never Runs

### Description
A PHP cron job script that exists but is not in crontab.

### Files

**`cron/resource_tick.php`**
```php
<?php
// This should run every 5 seconds to update resources
require_once __DIR__ . '/../include/init.php';

$db = Database::getInstance();
$villages = $db->query("SELECT * FROM villages");

foreach ($villages as $village) {
    $village->updateResources();
    $village->save();
}

echo "Resource tick complete\n";
```

**`crontab` (system crontab)**
```
# Crontab is empty or doesn't include resource_tick.php
0 * * * * /usr/bin/php /var/www/html/cron/cleanup.php
```

### Expected Finding

```json
{
  "finding_type": "CRON_NOT_SCHEDULED",
  "severity": "CRITICAL",
  "location": {
    "file": "cron/resource_tick.php"
  },
  "evidence": {
    "cron_file_exists": true,
    "crontab_entries_searched": [
      "crontab -l",
      "/etc/crontab",
      "/etc/cron.d/*"
    ],
    "matching_entries": [],
    "purpose_detected": "Resource update tick (game server)"
  },
  "message": "Cron script 'resource_tick.php' exists but is not scheduled in any crontab"
}
```

---

## Fixture 7: Dead Code (Orphan Function)

### Description
A function that is never called from any entry point.

### Files

**`src/utils/helpers.ts`**
```typescript
export function formatDate(date: Date): string {
  return date.toISOString();
}

export function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

// This function is never called anywhere
export function legacyFormatter(data: unknown): string {
  return JSON.stringify(data, null, 2);
}
```

**`src/index.ts`**
```typescript
import { formatDate, formatCurrency } from './utils/helpers';
// legacyFormatter is NOT imported

console.log(formatDate(new Date()));
console.log(formatCurrency(99.99));
```

### Expected Finding

```json
{
  "finding_type": "DEAD_CODE",
  "severity": "MEDIUM",
  "location": {
    "file": "src/utils/helpers.ts",
    "line": 10,
    "function": "legacyFormatter"
  },
  "evidence": {
    "function_exported": true,
    "import_searched": ["src/**/*.ts", "src/**/*.tsx"],
    "imports_found": [],
    "call_sites_found": [],
    "reachability_proof": {
      "entry_points": ["src/index.ts"],
      "path_exists": false
    }
  },
  "message": "Function 'legacyFormatter' is exported but never imported or called from any entry point"
}
```

---

## Fixture 8: Type Lie (as any)

### Description
Type assertion that masks a runtime error.

### Files

**`src/api/handler.ts`**
```typescript
interface User {
  id: number;
  name: string;
  email: string;
}

export async function getUser(userId: string): Promise<User> {
  const response = await fetch(`/api/users/${userId}`);
  const data = await response.json();

  // Dangerous: assuming API returns correct shape
  return data as User;
}

export function displayUser(user: User): void {
  // This will crash if user.name is undefined
  console.log(`Hello, ${user.name.toUpperCase()}`);
}
```

### Expected Finding

```json
{
  "finding_type": "UNSAFE_TYPE_ASSERTION",
  "severity": "HIGH",
  "location": {
    "file": "src/api/handler.ts",
    "line": 12,
    "expression": "data as User"
  },
  "evidence": {
    "assertion_type": "as User",
    "source_type": "any (from json())",
    "no_runtime_validation": true,
    "potential_crash_sites": [
      {
        "file": "src/api/handler.ts",
        "line": 17,
        "access": "user.name.toUpperCase()"
      }
    ]
  },
  "message": "Type assertion 'as User' on unvalidated API response. If API returns unexpected shape, 'user.name.toUpperCase()' will crash."
}
```

---

## Fixture 9: Boundary Mismatch (API Contract)

### Description
Frontend expects different response shape than API provides.

### Files

**`openapi.yaml`**
```yaml
paths:
  /api/users:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
```

**`src/client.ts`**
```typescript
interface UsersResponse {
  users: User[];  // WRONG: should be 'data', not 'users'
}

export async function fetchUsers(): Promise<User[]> {
  const response = await fetch('/api/users');
  const json: UsersResponse = await response.json();
  return json.users;  // Will be undefined!
}
```

### Expected Finding

```json
{
  "finding_type": "BOUNDARY_SCHEMA_MISMATCH",
  "severity": "CRITICAL",
  "boundary": {
    "caller": {
      "file": "src/client.ts",
      "line": 8,
      "expects": "{ users: User[] }"
    },
    "callee": {
      "file": "openapi.yaml",
      "path": "/api/users",
      "provides": "{ data: User[] }"
    }
  },
  "evidence": {
    "expected_property": "users",
    "actual_property": "data",
    "openapi_schema": "paths./api/users.get.responses.200.content.application/json.schema"
  },
  "message": "Frontend expects response property 'users' but API spec defines 'data'"
}
```

---

## Fixture 10: Stub Hell (MapleStory Server)

### Description
Game server with all skill effects stubbed.

### Files

**`src/skills/SkillEffect.cs`**
```csharp
public class SkillEffectHandler
{
    public void HandleSkillEffect(int skillId, Character user, Character target)
    {
        switch (skillId)
        {
            case 1001: // Power Strike
                // TODO: Implement damage calculation
                break;
            case 1002: // Slash Blast
                // TODO: Implement AoE damage
                break;
            case 1003: // Final Attack
                throw new NotImplementedException("Final Attack not implemented");
            default:
                // Unknown skill - do nothing
                break;
        }
    }
}
```

### Expected Finding

```json
{
  "finding_type": "STUB_IMPLEMENTATION",
  "severity": "CRITICAL",
  "location": {
    "file": "src/skills/SkillEffect.cs",
    "line": 3,
    "class": "SkillEffectHandler"
  },
  "evidence": {
    "switch_cases": 4,
    "implemented_cases": 0,
    "stub_patterns": [
      { "case": 1001, "pattern": "EMPTY_CASE", "comment": "TODO: Implement damage calculation" },
      { "case": 1002, "pattern": "EMPTY_CASE", "comment": "TODO: Implement AoE damage" },
      { "case": 1003, "pattern": "NOT_IMPLEMENTED_EXCEPTION" },
      { "case": "default", "pattern": "EMPTY_CASE" }
    ]
  },
  "message": "SkillEffectHandler has 0 implemented cases out of 4. All skill effects are stubs."
}
```

---

## Golden Output Format

### Per-Fixture Golden File

Each fixture has a corresponding golden file at:
```
specs/goldens/{fixture-name}.golden.json
```

### Golden Schema

```json
{
  "fixture_name": "ui-noop-button",
  "fixture_version": "1.0.0",
  "expected_findings": [
    {
      "finding_type": "NO_OP_UI",
      "severity": "CRITICAL",
      "required_fields": ["location", "evidence.static", "evidence.dynamic"],
      "forbidden_messages": ["functional", "complete", "working"]
    }
  ],
  "expected_confidence": {
    "min": 0.80,
    "max": 1.00
  },
  "execution_requirements": {
    "needs_runtime": true,
    "needs_browser": true,
    "timeout_seconds": 30
  }
}
```

---

## Acceptance Test Runner

### Running Fixture Tests

```bash
# Run all fixture tests
codetruth test-fixtures

# Run specific fixture
codetruth test-fixtures --fixture ui-noop-button

# Generate golden files from current output
codetruth test-fixtures --update-goldens
```

### Test Pass Criteria

| Criterion | Requirement |
|-----------|-------------|
| Finding detected | Matching finding_type |
| Correct severity | Severity matches expected |
| Required fields present | All required_fields exist |
| No forbidden messages | Finding doesn't contain forbidden text |
| Confidence in range | min <= confidence <= max |
| Evidence attached | Evidence is not empty |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial 10 fixtures |
