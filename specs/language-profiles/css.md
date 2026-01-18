# Language Truth Profile: CSS

**Profile Version:** 1.0.0
**Language Version:** CSS3+
**Stack Tier:** 2 (UI Layer - Presentation)
**Profile Completeness:** 0.90
**Implementation Completeness:** 0.85

---

## Overview

CSS defines visual presentation across all web repos. In the user's 589+ repos, CSS appears in:
- Tailwind CSS configurations (Next.js, React)
- SCSS/SASS stylesheets
- CSS-in-JS (styled-components, emotion)
- CSS Modules
- Game server admin panel themes (Travian, TWLan, MapleStory web)
- Legacy inline styles in PHP templates

CSS verification focuses on **selector validity**, **property correctness**, **unused rule detection**, and **specificity conflicts**.

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.css` | Extension | CSS stylesheets |
| `*.scss` | Extension | SCSS preprocessor |
| `*.sass` | Extension | SASS preprocessor |
| `*.less` | Extension | LESS preprocessor |
| `*.styl` | Extension | Stylus preprocessor |
| `*.module.css` | Extension | CSS Modules |
| `*.module.scss` | Extension | SCSS Modules |
| `tailwind.config.js` | Filename | Tailwind config |
| `postcss.config.js` | Filename | PostCSS config |
| `styles.css` | Filename | Common stylesheet |
| `globals.css` | Filename | Global styles |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter |
| Parser Name | tree-sitter-css |
| Grammar Version | 0.20.0 |
| Syntax Accuracy | 0.98 |
| Semantic Accuracy | 0.85 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Good recovery |
| Error recovery | Yes | Handles malformed CSS |
| Incremental parsing | Yes | Supported |
| Comment preservation | Yes | Extracted |
| At-rules | Yes | @media, @keyframes, @import |
| Custom properties | Yes | CSS variables (--var) |

### Known Parse Failures

1. **CSS-in-JS**: Template literals containing CSS (`styled.div\`...\``)
2. **PostCSS plugins**: Custom syntax transformations
3. **Tailwind @apply**: Utility class expansion
4. **CSS Nesting**: Native nesting (partial spec support)
5. **Container queries**: Emerging spec, limited support

---

## Semantic Capability

### Style Analysis

| Property | Value |
|----------|-------|
| Selector Parsing | Yes |
| Property Validation | Yes |
| Value Parsing | Yes |
| Specificity Calculation | Yes |
| Cascade Analysis | Partial |
| Inheritance Tracking | Partial |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Selector Resolution | Yes | 0.90 |
| Specificity Ordering | Yes | 0.95 |
| Media Query Parsing | Yes | 0.95 |
| Custom Property Tracking | Partial | 0.75 |
| Animation Tracking | Yes | 0.85 |
| Import Resolution | Yes | 0.90 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Dynamic class names | false_negative | critical | Class inventory |
| CSS-in-JS | incomplete | high | Runtime extraction |
| !important cascades | incomplete | medium | Full cascade analysis |
| Browser prefixes | incomplete | low | Autoprefixer data |
| calc() expressions | incomplete | medium | Expression evaluation |
| var() fallbacks | incomplete | medium | Variable tracking |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Selector Graph | Yes | 0.85 | P2 (STATIC_PARTIAL) |
| Import Graph | Yes | 0.90 | P1 (STATIC_COMPLETE) |
| Animation Graph | Yes | 0.80 | P2 (STATIC_PARTIAL) |
| Variable Graph | Partial | 0.60 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| @import | Yes | P1 |
| url() references | Yes | P1 |
| font-face sources | Yes | P1 |
| background images | Yes | P1 |
| CSS variables cross-file | Partial | P3 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Selector Matches | Partial | 0.70 |
| Prove Rule Applied | Partial | 0.60 |
| Prove Rule Unused | Partial | 0.75 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Dynamic classes | false_negative | critical | `className={condition ? 'a' : 'b'}` |
| Conditional styles | incomplete | high | JS-toggled classes |
| Shadow DOM styles | incomplete | high | Scoped to component |
| CSS Modules hashing | incomplete | medium | `.class` → `.class_abc123` |
| Tailwind purge | incomplete | medium | Unused class removal |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes (via browser) |
| Environment | Browser, JSDOM (limited) |
| Min Version | Modern browsers |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Computed Style Inspection | Yes | getComputedStyle() |
| Coverage Analysis | Yes | Chrome DevTools |
| Performance Audit | Yes | Lighthouse |
| Layout Analysis | Yes | DevTools Layout panel |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Visual Regression | Yes | Percy, Chromatic, BackstopJS |
| Layout Tests | Yes | Playwright, Cypress |
| Responsive Tests | Yes | Multi-viewport screenshots |
| Snapshot Tests | Yes | Jest snapshots |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Yes |
| Granularity | rule |
| Tool | Chrome DevTools Coverage |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Hover states | incomplete | medium | Requires interaction |
| Print styles | incomplete | low | Different media |
| Animation states | incomplete | medium | Time-dependent |
| Media query breakpoints | incomplete | medium | Viewport-dependent |
| Focus states | incomplete | medium | Requires focus |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| selector_list | json | P1 | T0 | Yes | No |
| property_inventory | json | P1 | T0 | Yes | No |
| import_graph | json | P1 | T0 | Yes | No |
| specificity_map | json | P2 | T0 | Yes | No |
| coverage_report | json | P4 | T1 | No | Yes |
| unused_rules | json | P4 | T1 | No | Yes |
| computed_styles | json | P3 | T1 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | CSS-in-JS | Template literal CSS | JS embedding | Runtime extraction |
| 2 | PostCSS transforms | Plugin-specific syntax | Build-time | Build output analysis |
| 3 | Native nesting | CSS nesting spec | Partial support | PostCSS fallback |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Dynamic classes | JS-generated class names | Runtime decision | Class inventory |
| 2 | Cascade resolution | Complex specificity | Order + specificity | Full document analysis |
| 3 | Custom properties | var() runtime values | Computed at runtime | Variable tracking |
| 4 | !important wars | Multiple !important | Requires full cascade | Cascade simulation |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | HTML class binding | Which elements use classes | Cross-file | Full project analysis |
| 2 | Framework bindings | :class, className, etc. | Framework-specific | Framework adapter |
| 3 | Module hashing | CSS Modules transform | Build-time naming | Build output mapping |
| 4 | Tailwind utilities | Dynamic class assembly | Requires class inventory | Tailwind config analysis |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | State styles | :hover, :focus, :active | Interaction required | Event simulation |
| 2 | Media queries | Viewport-dependent | Multiple viewports | Multi-viewport test |
| 3 | Animation frames | @keyframes states | Time-dependent | Animation inspection |
| 4 | Dark mode | prefers-color-scheme | System setting | Theme enumeration |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| HTML (selectors) | reference | Yes | Partial | Partial | P3 |
| JavaScript (classList) | runtime | Partial | No | No | P5 |
| TypeScript (CSS Modules) | import | Yes | Yes | Partial | P2 |
| SCSS (imports) | compile | Yes | Yes | Yes | P1 |
| Tailwind (config) | compile | Partial | Partial | No | P4 |

### Common Boundary Patterns

```css
/* Pattern 1: Class referenced in HTML */
.button-primary {
    background: blue;
}
/* VERIFICATION: Must find <* class="button-primary"> in HTML */

/* Pattern 2: CSS Variable definition */
:root {
    --primary-color: #007bff;
}
/* VERIFICATION: Must find var(--primary-color) usage */

/* Pattern 3: Animation reference */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
/* VERIFICATION: Must find animation: fadeIn or animation-name: fadeIn */
```

---

## Game Server Specific Patterns

### Travian/TWLan Admin Styles

```css
/* Pattern: PHP-conditional class usage */
.admin-only {
    display: block;  /* Only shown when $isAdmin true */
}
.user-banned {
    color: red;
    text-decoration: line-through;
}
/* BLINDSPOT: Cannot verify PHP conditions control visibility */
```

**Detection Rules:**
1. Classes like `.admin-*` → check for auth guards in PHP
2. State classes like `.banned`, `.online` → verify JS/PHP sets them
3. Legacy inline styles → flag for review

### MapleStory Character Styles

```css
/* Pattern: Character equipment display */
.equip-slot-hat { background-position: 0 0; }
.equip-slot-weapon { background-position: -32px 0; }
.job-warrior { border-color: red; }
.job-mage { border-color: blue; }
/* These classes must be set by server data */
```

---

## Tool Dependencies

### Required

| Tool | Purpose | Min Version |
|------|---------|-------------|
| tree-sitter-css | Parsing | 0.20.0 |
| Node.js | Runtime | 18.0.0 |

### Optional

| Tool | Purpose | Enhances |
|------|---------|----------|
| PurgeCSS | Unused detection | Wiring analysis |
| Stylelint | Validation | Semantic analysis |
| Chrome DevTools | Coverage | Runtime verification |
| postcss | Transforms | Parse enhancement |

---

## Failure Patterns

### Pattern 1: Unused Selector

**Description:** CSS selector matches no elements in the project

**Detection:** Cross-reference selectors with HTML element/class inventory

**Example:**
```css
.legacy-component {  /* DETECTED: No element uses this class */
    color: red;
}
```

### Pattern 2: Invalid Property

**Description:** CSS property doesn't exist or is misspelled

**Detection:** Property validation against CSS spec

**Example:**
```css
.box {
    colr: red;  /* DETECTED: Invalid property 'colr' */
    widht: 100px;  /* DETECTED: Invalid property 'widht' */
}
```

### Pattern 3: Specificity Override (Dead Rule)

**Description:** Rule is always overridden by higher specificity

**Detection:** Specificity analysis across all rules for same property

**Example:**
```css
#main .button { color: blue; }
.button { color: red; }  /* DETECTED: Always overridden by #main .button */
```

### Pattern 4: Undefined Variable

**Description:** CSS variable used but never defined

**Detection:** Variable usage vs definition inventory

**Example:**
```css
.box {
    color: var(--undefined-color);  /* DETECTED: --undefined-color never defined */
}
```

### Pattern 5: Circular Import

**Description:** CSS files import each other creating a loop

**Detection:** Import graph cycle detection

**Example:**
```css
/* a.css */
@import 'b.css';

/* b.css */
@import 'a.css';  /* DETECTED: Circular import */
```

---

## Forbidden Claims (MANDATORY SECTION)

| Claim | Why Forbidden | Required Evidence |
|-------|---------------|-------------------|
| "All styles applied correctly" | Cannot verify computed styles | Runtime computed style check |
| "No unused CSS" | Dynamic classes exist | Full runtime class coverage |
| "Responsive design complete" | Cannot test all viewports | Multi-viewport test results |
| "No specificity conflicts" | Requires full cascade | Cascade simulation output |
| "Theme support complete" | Cannot verify all themes | Theme enumeration test |

---

## Required Fixtures (MANDATORY SECTION)

### Fixture 1: Dead Selector

**Purpose:** Tests detection of selectors matching nothing

**File:** `fixtures/css/dead-selector/`

**Expected Findings:**
- HIGH: Selector `.nonexistent-class` matches no elements
- MEDIUM: Selector `#unused-id` matches no elements

**Forbidden False Positives:**
- Should NOT flag classes used in JavaScript dynamically
- Should NOT flag classes in lazy-loaded components

### Fixture 2: Specificity Hell

**Purpose:** Tests detection of overridden rules

**File:** `fixtures/css/specificity-hell/`

**Expected Findings:**
- MEDIUM: Rule on line 45 always overridden by rule on line 12
- LOW: Unnecessary !important (no conflict exists)

**Forbidden False Positives:**
- Should NOT flag intentional cascade overrides
- Should NOT flag media query variants

---

## Golden Output Expectations (MANDATORY SECTION)

### Golden 1: Dead Selector

```json
{
  "findings": [
    {
      "type": "unused_selector",
      "severity": "high",
      "location": "styles.css:23",
      "message": "Selector '.nonexistent-class' matches no elements in project",
      "proof_level": "P4",
      "evidence": "class_inventory_20240118_001"
    }
  ],
  "confidence": 0.75,
  "blindspots_acknowledged": [
    "Dynamic class names not tracked",
    "Third-party component classes not inventoried"
  ]
}
```

### Golden 2: Specificity Hell

```json
{
  "findings": [
    {
      "type": "dead_rule",
      "severity": "medium",
      "location": "styles.css:45",
      "message": "Rule always overridden by higher specificity rule at styles.css:12",
      "proof_level": "P2",
      "evidence": "specificity_analysis_20240118_001"
    }
  ],
  "confidence": 0.85,
  "blindspots_acknowledged": [
    "Source order in dynamic stylesheets unknown",
    "Shadow DOM specificity boundaries not analyzed"
  ]
}
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.98 × 0.15 = 0.147
    semantic_accuracy × 0.20 +        # 0.85 × 0.20 = 0.170
    wiring_completeness × 0.25 +      # 0.65 × 0.25 = 0.163
    runtime_capability × 0.25 +       # 0.75 × 0.25 = 0.188
    (1 - blindspot_penalty) × 0.15    # 0.70 × 0.15 = 0.105
)
```

**Current Score:** 0.77 (PARTIAL - due to dynamic class and CSS-in-JS blindspots)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile with game server patterns |
