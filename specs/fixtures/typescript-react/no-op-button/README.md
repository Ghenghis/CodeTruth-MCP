# Fixture: No-Op Button

## Purpose

This fixture demonstrates UI elements that visually exist but cause no actual effect when interacted with. This is a common "fake completeness" pattern.

## Files

- `NoOpButton.tsx` - React component with multiple no-op patterns

## Expected Findings

| # | Type | Severity | Location | Message |
|---|------|----------|----------|---------|
| 1 | `empty_handler` | HIGH | NoOpButton.tsx:20 | Handler 'handleClick' has empty body |
| 2 | `debug_only_handler` | MEDIUM | NoOpButton.tsx:25 | Handler 'handleSubmit' only contains console statement |
| 3 | `unused_handler` | WARNING | NoOpButton.tsx:29 | Handler 'handleUnused' is defined but never used |
| 4 | `button_no_handler` | LOW | NoOpButton.tsx:46 | Button without onClick handler |

## Required Evidence

| Evidence Type | Description | Proof Level |
|---------------|-------------|-------------|
| `ast_analysis` | Parse the TSX and identify handler definitions | P2 (STATIC_PARTIAL) |
| `handler_body_check` | Verify handler function bodies are empty or trivial | P2 (STATIC_PARTIAL) |
| `usage_tracking` | Track which handlers are actually bound to elements | P2 (STATIC_PARTIAL) |
| `playwright_trace` | (OPTIONAL) Click button, observe no network/DOM change | P3 (DYNAMIC_VERIFIED) |

## Forbidden False Positives

- Should NOT flag handlers that call external functions (even if we can't trace them)
- Should NOT flag handlers with TODO comments (those are code_marker findings, separate)
- Should NOT flag submit buttons inside forms (they may trigger form submission)

## Golden Output Reference

See: `specs/goldens/typescript-react-no-op-button.json`

## How to Use

```bash
codetruth audit specs/fixtures/typescript-react/no-op-button --profile typescript-react
```

Expected exit code: 1 (findings present)
