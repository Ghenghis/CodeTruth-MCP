# UI No-Op Detector

**Version:** 1.0.0
**Status:** PRODUCTION
**Proof Level:** P3 (DYNAMIC_VERIFIED)
**Overall Confidence:** 0.82

---

## Purpose

The UI No-Op Detector answers the critical question:

> **"Does clicking this button actually DO something?"**

This is the user's #1 pain point: UI that looks complete but does nothing.

The detector:
1. Inventories all interactive UI elements
2. Clicks/triggers each element
3. Observes for any effect
4. Marks elements with no effect as `UNWIRED_UI` or `NO_OP_UI`

---

## Detection Strategy

### Level 1: Static Analysis (Pre-Runtime)

Before running Playwright, we do static analysis to find:

| Pattern | Detection | Severity |
|---------|-----------|----------|
| Empty handler | `onClick={() => {}}` | CRITICAL |
| Handler with only comment | `onClick={() => { /* TODO */ }}` | CRITICAL |
| Handler that only logs | `onClick={() => console.log('clicked')}` | HIGH |
| Handler throws NotImplemented | `onClick={() => { throw new Error('TODO') }}` | CRITICAL |
| Handler returns early | `onClick={() => { return; }}` | CRITICAL |
| Missing handler | `<button>` without onClick | HIGH |
| Disabled by default | `disabled={true}` always | MEDIUM |

### Level 2: Dynamic Analysis (Runtime with Playwright)

For each interactive element:

```python
async def verify_element_effect(page: Page, element: Locator) -> EffectResult:
    """
    Click element and observe for ANY effect.

    Effects we can detect:
    - Network request (fetch, XHR)
    - Navigation (URL change)
    - DOM mutation (element added/removed/changed)
    - Console output (log, warn, error)
    - Storage change (localStorage, sessionStorage, cookies)
    - State change (for instrumented state managers)
    """
    # Snapshot state before
    before = await capture_state(page)

    # Perform interaction
    await element.click()

    # Wait for potential effects (with timeout)
    await page.wait_for_timeout(500)  # Short wait for immediate effects
    await page.wait_for_load_state('networkidle', timeout=2000)

    # Snapshot state after
    after = await capture_state(page)

    # Compare
    effects = compare_states(before, after)

    if len(effects) == 0:
        return EffectResult(
            element=element,
            status="NO_OP",
            evidence=NoOpEvidence(
                before_state=before,
                after_state=after,
                trace_file=trace_path
            )
        )

    return EffectResult(
        element=element,
        status="HAS_EFFECT",
        effects=effects
    )
```

---

## Observable Effects

### Network Effects

| Effect | Detection Method | Confidence |
|--------|------------------|------------|
| Fetch request | Request interception | 0.95 |
| XHR request | Request interception | 0.95 |
| WebSocket message | WebSocket interception | 0.90 |
| GraphQL mutation | Request body inspection | 0.95 |
| Form submission | Navigation + POST | 0.95 |

### DOM Effects

| Effect | Detection Method | Confidence |
|--------|------------------|------------|
| Element added | MutationObserver | 0.95 |
| Element removed | MutationObserver | 0.95 |
| Element text changed | MutationObserver | 0.95 |
| Attribute changed | MutationObserver | 0.95 |
| Class changed | MutationObserver | 0.90 |
| Style changed | MutationObserver | 0.85 |
| Modal opened | Visibility detection | 0.90 |
| Drawer opened | Position detection | 0.85 |

### Navigation Effects

| Effect | Detection Method | Confidence |
|--------|------------------|------------|
| URL change | Page URL comparison | 0.98 |
| Hash change | URL hash comparison | 0.98 |
| History push | History API interception | 0.95 |
| Redirect | Navigation listener | 0.95 |

### Storage Effects

| Effect | Detection Method | Confidence |
|--------|------------------|------------|
| localStorage set | Storage listener | 0.95 |
| sessionStorage set | Storage listener | 0.95 |
| Cookie set | Cookie comparison | 0.90 |
| IndexedDB write | IDB interception | 0.85 |

### Console Effects

| Effect | Detection Method | Confidence |
|--------|------------------|------------|
| console.log | Console listener | 0.95 |
| console.error | Console listener | 0.95 |
| console.warn | Console listener | 0.95 |

---

## Element Discovery

### Interactive Element Types

| Element | Selector | Interaction |
|---------|----------|-------------|
| Button | `button, [role="button"], input[type="button"]` | click |
| Link | `a[href], [role="link"]` | click |
| Form submit | `input[type="submit"], button[type="submit"]` | click |
| Checkbox | `input[type="checkbox"], [role="checkbox"]` | click |
| Radio | `input[type="radio"], [role="radio"]` | click |
| Select | `select, [role="listbox"]` | select option |
| Input | `input[type="text"], textarea` | type + blur |
| Menu item | `[role="menuitem"]` | click |
| Tab | `[role="tab"]` | click |
| Accordion | `[role="button"][aria-expanded]` | click |
| Dialog trigger | `[aria-haspopup="dialog"]` | click |
| Dropdown trigger | `[aria-haspopup="listbox"]` | click |

### Discovery Algorithm

```python
async def discover_interactive_elements(page: Page) -> List[Element]:
    """
    Find all interactive elements on the page.

    Strategy:
    1. Find all elements matching interactive selectors
    2. Filter out hidden/disabled elements
    3. Filter out elements outside viewport (optional)
    4. Deduplicate (same element with multiple selectors)
    """
    selectors = [
        'button:not([disabled])',
        'a[href]:not([disabled])',
        'input[type="submit"]:not([disabled])',
        'input[type="button"]:not([disabled])',
        '[role="button"]:not([aria-disabled="true"])',
        '[role="link"]:not([aria-disabled="true"])',
        '[role="menuitem"]:not([aria-disabled="true"])',
        '[role="tab"]:not([aria-disabled="true"])',
        '[onclick]',
        '[ng-click]',
        '[v-on\\:click]',
        '[@click]',
    ]

    elements = []
    for selector in selectors:
        found = await page.locator(selector).all()
        for el in found:
            if await is_visible(el) and await is_enabled(el):
                elements.append(Element(
                    locator=el,
                    selector=selector,
                    tag=await el.evaluate('el => el.tagName'),
                    text=await el.text_content(),
                    aria_label=await el.get_attribute('aria-label'),
                ))

    return deduplicate(elements)
```

---

## State Capture

### Before/After State Schema

```json
{
  "timestamp": "2024-01-18T12:00:00.000Z",
  "url": "https://app.example.com/dashboard",
  "dom": {
    "element_count": 156,
    "hash": "sha256:abc123...",
    "visible_text_hash": "sha256:def456..."
  },
  "network": {
    "pending_requests": [],
    "completed_requests": [
      {
        "url": "https://api.example.com/users",
        "method": "GET",
        "status": 200
      }
    ]
  },
  "storage": {
    "localStorage": {
      "user": "{\"id\":1,\"name\":\"Test\"}"
    },
    "sessionStorage": {},
    "cookies": [
      {"name": "session", "value": "abc123"}
    ]
  },
  "console": {
    "logs": [],
    "errors": [],
    "warnings": []
  }
}
```

### State Comparison

```python
def compare_states(before: State, after: State) -> List[Effect]:
    effects = []

    # URL change
    if before.url != after.url:
        effects.append(Effect(
            type="NAVIGATION",
            detail=f"URL changed from {before.url} to {after.url}",
            confidence=0.98
        ))

    # Network requests
    new_requests = set(after.network.completed_requests) - set(before.network.completed_requests)
    for req in new_requests:
        effects.append(Effect(
            type="NETWORK_REQUEST",
            detail=f"{req.method} {req.url} -> {req.status}",
            confidence=0.95
        ))

    # DOM changes
    if before.dom.hash != after.dom.hash:
        effects.append(Effect(
            type="DOM_MUTATION",
            detail="DOM structure changed",
            confidence=0.90
        ))

    # Storage changes
    for key in set(after.storage.localStorage.keys()) - set(before.storage.localStorage.keys()):
        effects.append(Effect(
            type="STORAGE_WRITE",
            detail=f"localStorage['{key}'] set",
            confidence=0.95
        ))

    # Console output
    new_logs = after.console.logs[len(before.console.logs):]
    for log in new_logs:
        # Only count non-trivial logs as effects
        if not is_trivial_log(log):
            effects.append(Effect(
                type="CONSOLE_LOG",
                detail=f"console.log: {log}",
                confidence=0.50  # Low confidence - might be debug
            ))

    return effects
```

---

## Output Schema

### UI Verification Report

```json
{
  "repo_path": "/path/to/repo",
  "analysis_timestamp": "2024-01-18T12:00:00Z",
  "pages_tested": 5,
  "elements_found": 47,
  "elements_tested": 42,
  "elements_skipped": 5,
  "results": {
    "has_effect": 35,
    "no_op": 4,
    "error": 3,
    "skipped": 5
  },
  "no_op_elements": [
    {
      "page_url": "https://app.example.com/settings",
      "element": {
        "selector": "button#save-settings",
        "text": "Save Settings",
        "location": {
          "file": "src/pages/Settings.tsx",
          "line": 45,
          "handler": "handleSave"
        }
      },
      "proof": {
        "type": "NO_OBSERVABLE_EFFECT",
        "before_state": { "...": "..." },
        "after_state": { "...": "..." },
        "trace_file": ".codetruth/traces/settings-save-button.zip",
        "video_file": ".codetruth/videos/settings-save-button.webm"
      },
      "static_analysis": {
        "handler_body": "async function handleSave() { /* TODO: implement */ }",
        "pattern": "EMPTY_HANDLER"
      },
      "confidence": 0.88
    }
  ],
  "overall_confidence": 0.85
}
```

---

## Finding Types

### NO_OP_UI

**Condition:** Element is interactive, handler exists, but produces no observable effect.

**Severity:** CRITICAL

**Evidence Required:**
- Before/after state comparison
- Playwright trace file
- Network HAR (empty)
- Static handler source

### EMPTY_HANDLER

**Condition:** Handler function body is empty or trivial.

**Severity:** CRITICAL

**Evidence Required:**
- Handler source code
- AST showing empty body

### STUB_HANDLER

**Condition:** Handler throws NotImplementedError, contains only TODO, or returns early.

**Severity:** CRITICAL

**Evidence Required:**
- Handler source code
- Pattern match evidence

### DISABLED_ALWAYS

**Condition:** Element has `disabled` attribute that never changes.

**Severity:** HIGH

**Evidence Required:**
- Static analysis of disabled prop
- No code path that enables

### MISSING_HANDLER

**Condition:** Interactive element has no event handler.

**Severity:** HIGH

**Evidence Required:**
- Element source
- AST showing no handler props

---

## Test Scenarios

### Scenario 1: Empty onClick Handler

```tsx
// Fixture: src/Button.tsx
export function SaveButton() {
  const handleSave = () => {
    // TODO: Save data
  };

  return <button onClick={handleSave}>Save</button>;
}
```

**Expected Finding:**
```json
{
  "element": "button:text('Save')",
  "finding_type": "EMPTY_HANDLER",
  "severity": "CRITICAL",
  "static_evidence": {
    "handler": "handleSave",
    "body": "// TODO: Save data"
  }
}
```

### Scenario 2: Handler That Only Logs

```tsx
// Fixture: src/DeleteButton.tsx
export function DeleteButton() {
  return (
    <button onClick={() => console.log('Delete clicked')}>
      Delete
    </button>
  );
}
```

**Expected Finding:**
```json
{
  "element": "button:text('Delete')",
  "finding_type": "NO_OP_UI",
  "severity": "HIGH",
  "note": "Handler only produces console.log (not a real effect)",
  "dynamic_evidence": {
    "effects": [
      {"type": "CONSOLE_LOG", "detail": "Delete clicked"}
    ],
    "real_effects": []
  }
}
```

### Scenario 3: Form Submit That Goes Nowhere

```tsx
// Fixture: src/ContactForm.tsx
export function ContactForm() {
  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Send to API
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" />
      <button type="submit">Send</button>
    </form>
  );
}
```

**Expected Finding:**
```json
{
  "element": "button[type='submit']:text('Send')",
  "finding_type": "NO_OP_UI",
  "severity": "CRITICAL",
  "evidence": {
    "form_prevented_default": true,
    "network_requests": [],
    "state_changes": []
  }
}
```

---

## Limitations (MANDATORY)

### What This Engine CANNOT Detect

1. **Server-side effects without response change**
   - If API returns 200 but does nothing, we can't tell
   - Mitigation: Database state verification (if available)

2. **Delayed effects**
   - Effects that happen after timeout (>10s)
   - Mitigation: Configurable wait time

3. **External system effects**
   - Email sent, SMS sent, webhook fired
   - Mitigation: Mock/log external calls

4. **State changes without DOM reflection**
   - Redux/Zustand state that doesn't update UI
   - Mitigation: State instrumentation

5. **Effects behind authentication**
   - Need to be logged in to test
   - Mitigation: Auth configuration

6. **Mobile-specific interactions**
   - Touch, swipe, pinch
   - Mitigation: Mobile viewport testing

### What MUST Be Labeled UNPROVEN

- Elements behind login: `UNPROVEN (auth required)`
- Elements requiring specific state: `UNPROVEN (state precondition)`
- Elements only visible on hover: `UNPROVEN (interaction required)`
- Elements in error states: `UNPROVEN (error condition)`

---

## Integration with Other Engines

### Reachability Engine

Before testing an element:
1. Check if handler is reachable from element
2. If not reachable → `HANDLER_NEVER_BOUND` (skip runtime test)

### Runtime Truth Correlator

After testing:
1. Static says handler is empty → static evidence
2. Runtime shows no effect → dynamic evidence
3. Both agree → HIGH confidence finding
4. Disagree → flag for review

---

## Evidence Artifacts

| Artifact | Format | Purpose |
|----------|--------|---------|
| Playwright trace | .zip | Full interaction replay |
| HAR file | .har | Network request log |
| Video recording | .webm | Visual proof |
| Screenshot before | .png | Visual diff |
| Screenshot after | .png | Visual diff |
| State JSON | .json | Before/after state |
| Console log | .json | Console output |

All artifacts stored in `.codetruth/evidence/ui-verification/`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial specification |
