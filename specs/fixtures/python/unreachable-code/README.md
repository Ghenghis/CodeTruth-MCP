# Fixture: Unreachable Code (Python)

## Purpose

Tests detection of code that can never be executed due to early return/raise.

## Expected Findings

| # | Type | Severity | Location | Message |
|---|------|----------|----------|---------|
| 1 | `unreachable_code` | WARNING | unreachable.py:16 | Code after return statement |
| 2 | `unreachable_code` | WARNING | unreachable.py:17 | Code after return statement |
| 3 | `unreachable_code` | WARNING | unreachable.py:25 | Code after raise statement |
| 4 | `unreachable_code` | WARNING | unreachable.py:26 | Code after raise statement |
| 5 | `unreachable_code` | WARNING | unreachable.py:34-36 | Code after return statement |
| 6 | `code_marker` | NOTE | unreachable.py:39 | TODO marker |
| 7 | `code_marker` | WARNING | unreachable.py:40 | FIXME marker |

## Golden Output Reference

See: `specs/goldens/python-unreachable-code.json`
