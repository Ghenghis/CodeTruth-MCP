# Fixture: Dead Handler

## Purpose

This fixture demonstrates handlers that are defined but never bound to any UI element. The code does real work but can never be triggered.

## Files

- `DeadHandler.tsx` - React component with orphaned handlers

## Expected Findings

| # | Type | Severity | Location | Message |
|---|------|----------|----------|---------|
| 1 | `unused_handler` | WARNING | DeadHandler.tsx:22 | Handler 'handleLogin' is defined but never used |
| 2 | `unused_handler` | WARNING | DeadHandler.tsx:32 | Handler 'handleLogout' is defined but never used |
| 3 | `unused_handler` | WARNING | DeadHandler.tsx:38 | Handler 'handleDataExport' is defined but never used |
| 4 | `missing_reference` | ERROR | DeadHandler.tsx:58 | Reference to 'handleMissing' which is not defined |

## Required Evidence

| Evidence Type | Description | Proof Level |
|---------------|-------------|-------------|
| `handler_inventory` | List all handler definitions in file | P1 (STATIC_COMPLETE) |
| `usage_analysis` | Find all handler references in JSX | P2 (STATIC_PARTIAL) |
| `cross_reference` | Compare defined vs used handlers | P2 (STATIC_PARTIAL) |

## Forbidden False Positives

- Should NOT flag handlers exported for use in other files
- Should NOT flag handlers passed as props to child components
- Should NOT flag handlers used in useEffect or other hooks

## Golden Output Reference

See: `specs/goldens/typescript-react-dead-handler.json`
