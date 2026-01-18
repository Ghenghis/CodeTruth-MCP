# Language Truth Profile: HTML

**Profile Version:** 1.0.0
**Language Version:** HTML5
**Stack Tier:** 1 (UI Layer - Document Structure)
**Profile Completeness:** 0.92
**Implementation Completeness:** 0.88

---

## Overview

HTML is the structural foundation of all web applications. In the user's 589+ repos, HTML appears in:
- React/Next.js templates (JSX/TSX transpiled)
- PHP game server admin panels (Travian, TWLan)
- Static websites and documentation
- Email templates
- Electron app shells

HTML verification focuses on **element existence**, **attribute correctness**, **accessibility compliance**, and **form integrity**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.html` | Extension | HTML documents |
| `*.htm` | Extension | Legacy extension |
| `*.xhtml` | Extension | XHTML documents |
| `*.vue` | Extension | Vue single-file components |
| `*.svelte` | Extension | Svelte components |
| `*.blade.php` | Extension | Laravel Blade templates |
| `*.ejs` | Extension | EJS templates |
| `*.hbs` | Extension | Handlebars templates |
| `*.phtml` | Extension | PHP HTML templates |
| `*.twig` | Extension | Twig templates |
| `index.html` | Filename | Entry points |
| `template.html` | Filename | Template files |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-html |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.99 |
| Semantic Accuracy | 0.85 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Excellent recovery |
| Error recovery | Yes | Handles malformed HTML |
| Incremental parsing | Yes | Supported |
| Comment preservation | Yes | Extracted |
| DOCTYPE parsing | Yes | All doctypes |
| Self-closing tags | Yes | XHTML and HTML5 |

### Known Parse Failures

1. **Template syntax**: `{{ variable }}`, `<% code %>` embedded in HTML
2. **JSX in HTML files**: React components mixed with HTML
3. **Malformed nesting**: Browsers auto-correct, parser may not match
4. **Custom elements**: Web components with non-standard tags
5. **Server-side includes**: `<!--#include -->` directives

---

## Semantic Capability

### Element Analysis

| Property | Value |
|----------|-------|
| Element Inventory | Yes |
| Attribute Validation | Yes |
| ID Uniqueness | Yes |
| Class Inventory | Yes |
| Form Structure | Yes |
| Link Validation | Partial |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| DOM Tree Construction | Yes | 0.98 |
| ID Resolution | Yes | 0.99 |
| Form-Input Association | Yes | 0.95 |
| Label-Input Association | Yes | 0.95 |
| ARIA Attribute Validation | Partial | 0.80 |
| Schema.org Validation | Partial | 0.70 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Dynamic HTML (innerHTML) | false_negative | critical | Runtime DOM inspection |
| Template interpolation | incomplete | high | Template-specific parser |
| Custom elements | incomplete | medium | Custom element registry |
| Shadow DOM | false_negative | high | Shadow root traversal |
| iframes | incomplete | medium | Cross-frame analysis |
| document.write | false_negative | high | Runtime tracing |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| DOM Tree | Yes | 0.95 | P1 (STATIC_COMPLETE) |
| Form Graph | Yes | 0.90 | P2 (STATIC_PARTIAL) |
| Link Graph | Yes | 0.85 | P2 (STATIC_PARTIAL) |
| Event Binding Graph | Partial | 0.50 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| Script tags | Yes | P1 |
| Link hrefs | Yes | P1 |
| Form actions | Yes | P1 |
| Image sources | Yes | P1 |
| iframe sources | Yes | P1 |
| data-* attributes | Yes | P2 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Element Exists | Yes | 0.99 |
| Prove ID Unique | Yes | 0.99 |
| Prove Form Complete | Partial | 0.80 |
| Prove Link Valid | Partial | 0.70 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| JS-generated HTML | false_negative | critical | `innerHTML = '<div>...'` |
| React/Vue components | incomplete | critical | `<Component />` → HTML |
| Template loops | incomplete | high | `{% for item in items %}` |
| Conditional rendering | incomplete | high | `v-if`, `*ngIf` |
| Dynamic attributes | incomplete | medium | `:href="url"` |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes (via browser) |
| Environment | Browser, JSDOM, Puppeteer |
| Min Version | Modern browsers |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| DOM Inspection | Yes | DevTools, Puppeteer |
| Mutation Observation | Yes | MutationObserver |
| Event Tracing | Yes | Event listeners |
| Accessibility Audit | Yes | axe-core, Lighthouse |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | N/A | N/A |
| Integration Tests | Yes | Cypress, Playwright |
| E2E Tests | Yes | Selenium, Puppeteer |
| Accessibility Tests | Yes | axe-core, pa11y |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | N/A |
| Granularity | element |
| Tool | DOM traversal |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Time-based rendering | incomplete | medium | Elements appear later |
| User interaction gates | incomplete | high | Click required |
| Network-dependent | incomplete | high | AJAX loads content |
| Auth-gated content | incomplete | high | Requires login |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| dom_tree | json | P1 | T0 | Yes | No |
| element_inventory | json | P1 | T0 | Yes | No |
| id_map | json | P1 | T0 | Yes | No |
| class_inventory | json | P1 | T0 | Yes | No |
| form_analysis | json | P2 | T0 | Yes | No |
| link_inventory | json | P2 | T0 | Yes | No |
| runtime_dom | json | P3 | T1 | No | Yes |
| accessibility_audit | json | P4 | T1 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Template syntax | `{{ }}`, `<% %>` | Not HTML | Template-aware parser |
| 2 | JSX | React component syntax | Different grammar | JSX parser |
| 3 | Custom elements | `<my-component>` | Unknown semantics | Registry lookup |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Dynamic content | innerHTML, document.write | Runtime only | DOM observation |
| 2 | Shadow DOM | Encapsulated content | Isolation | Shadow traversal |
| 3 | Template data | Interpolated values | Not in HTML | Data flow analysis |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Event handlers | onclick="..." | May be dynamic | JS analysis |
| 2 | JS DOM manipulation | createElement | Not in HTML | JS tracing |
| 3 | Framework bindings | v-bind, [attr] | Framework-specific | Framework analysis |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Lazy loading | Content loaded on scroll | Interaction needed | Scroll simulation |
| 2 | Auth gates | Content behind login | Credentials needed | Auth context |
| 3 | Conditional display | CSS display:none | State dependent | State enumeration |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| JavaScript (inline) | embed | Yes | Partial | No | P3 |
| CSS (inline/link) | reference | Yes | Yes | Partial | P2 |
| PHP (templates) | embed | Partial | No | No | P5 |
| Images (src) | reference | Yes | Yes | Yes | P1 |
| External URLs | reference | Yes | No | No | P6 |

### Common Boundary Patterns

```html
<!-- Pattern 1: Inline JavaScript -->
<button onclick="handleClick()">Click</button>
<!-- VERIFICATION: Must verify handleClick exists in JS -->

<!-- Pattern 2: Form Action -->
<form action="/api/submit" method="POST">
<!-- VERIFICATION: Must verify /api/submit route exists -->

<!-- Pattern 3: Data Attributes for JS -->
<div data-user-id="123" data-action="delete">
<!-- VERIFICATION: Must verify JS reads these attributes -->

<!-- Pattern 4: Template Interpolation (Blade) -->
<span>{{ $user->name }}</span>
<!-- VERIFICATION: Cannot verify - template context unknown -->
```

---

## Game Server Specific Patterns

### Travian/TWLan Admin Panels

```html
<!-- Pattern: PHP-embedded HTML -->
<?php if ($isAdmin): ?>
<div class="admin-panel">
    <form action="admin.php" method="POST">
        <input type="hidden" name="action" value="ban_user">
        <!-- BLINDSPOT: PHP condition not analyzed -->
    </form>
</div>
<?php endif; ?>
```

**Detection Rules:**
1. Form actions to `.php` files → verify PHP handler exists
2. Hidden inputs with `action` field → verify action is handled
3. Admin conditionals → mark PARTIAL confidence

### MapleStory Web Interfaces

```html
<!-- Pattern: Character display -->
<div class="character-card" data-char-id="{{ charId }}">
    <img src="/avatars/{{ charId }}.png" onerror="this.src='/default.png'">
</div>
<!-- BLINDSPOT: Template variable not resolvable -->
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| tree-sitter-html | Parsing | 0.20.0 |
| Node.js | Runtime | 18.0.0 |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| Puppeteer | Runtime DOM | Runtime verification |
| axe-core | Accessibility | Semantic analysis |
| html-validate | Validation | Parse accuracy |
| JSDOM | Lightweight DOM | Testing |

---

## Failure Patterns

### Pattern 1: Form Without Handler

**Description:** Form action points to non-existent endpoint

**Detection:** Cross-reference form action with route definitions

**Example:**
```html
<form action="/api/nonexistent" method="POST">
    <input type="text" name="data">
    <button type="submit">Submit</button>
</form>
<!-- DETECTED: /api/nonexistent has no handler -->
```

### Pattern 2: Dead ID Reference

**Description:** JavaScript references ID that doesn't exist

**Detection:** Cross-reference getElementById calls with HTML IDs

**Example:**
```html
<div id="container"></div>
<script>
document.getElementById('contaner').innerHTML = 'test'; // typo
</script>
<!-- DETECTED: ID 'contaner' does not exist -->
```

### Pattern 3: Orphan Form Inputs

**Description:** Form inputs outside any form element

**Detection:** Check all inputs have form parent or form attribute

**Example:**
```html
<input type="text" name="username" id="username">
<!-- Not inside a form, no form="formId" attribute -->
<!-- DETECTED: Input 'username' not associated with any form -->
```

### Pattern 4: Inaccessible Interactive Element

**Description:** Clickable element not keyboard accessible

**Detection:** Accessibility audit on interactive elements

**Example:**
```html
<div onclick="doSomething()" class="button">Click me</div>
<!-- DETECTED: div with onclick but no tabindex, role, or keyboard handler -->
```

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "All forms work correctly" | Cannot verify server handlers | Server handler existence proof |
| "Page is accessible" | Requires full audit | axe-core clean report |
| "All links valid" | External links may break | HTTP 200 responses |
| "No XSS vulnerabilities" | Requires context analysis | Security scanner output |
| "Complete DOM coverage" | Dynamic content exists | Runtime DOM snapshot |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Form Action Nowhere

**Purpose:** Tests detection of forms pointing to non-existent handlers

**File:** `fixtures/html/form-action-nowhere/`

**Expected Findings:**
- CRITICAL: Form action `/api/submit` has no handler
- HIGH: Form action `/process.php` file does not exist

**Forbidden False Positives:**
- Should NOT flag forms with valid actions
- Should NOT flag forms with JavaScript handlers (onsubmit)

### Fixture 2: Dead ID References

**Purpose:** Tests detection of JavaScript referencing non-existent IDs

**File:** `fixtures/html/dead-id-refs/`

**Expected Findings:**
- HIGH: getElementById('nonexistent') - ID does not exist
- MEDIUM: querySelector('#typo') - selector matches nothing

**Forbidden False Positives:**
- Should NOT flag dynamically created IDs
- Should NOT flag IDs in other HTML files (SPA)

---

## Golden Output Expectations (MANDATORY SECTION)

### Golden 1: Form Action Nowhere

```json
{
  "findings": [
    {
      "type": "dead_form_action",
      "severity": "critical",
      "location": "index.html:15",
      "message": "Form action '/api/submit' has no corresponding handler",
      "proof_level": "P2",
      "evidence": "route_scan_20240118_001"
    }
  ],
  "confidence": 0.85,
  "blindspots_acknowledged": [
    "Cannot verify external form actions",
    "JavaScript form handlers not traced"
  ]
}
```

### Golden 2: Dead ID References

```json
{
  "findings": [
    {
      "type": "dead_reference",
      "severity": "high",
      "location": "app.js:42",
      "message": "getElementById('nonexistent') references non-existent ID",
      "proof_level": "P2",
      "evidence": "id_inventory_20240118_001"
    }
  ],
  "confidence": 0.90,
  "blindspots_acknowledged": [
    "Dynamic ID creation not tracked",
    "IDs in lazy-loaded content not visible"
  ]
}
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.99 × 0.15 = 0.149
    semantic_accuracy × 0.20 +        # 0.85 × 0.20 = 0.170
    wiring_completeness × 0.25 +      # 0.75 × 0.25 = 0.188
    runtime_capability × 0.25 +       # 0.80 × 0.25 = 0.200
    (1 - blindspot_penalty) × 0.15    # 0.70 × 0.15 = 0.105
)
```

**Current Score:** 0.81 (PARTIAL - due to template and dynamic content blindspots)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with game server patterns |
