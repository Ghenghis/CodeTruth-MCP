# Fixture: AJAX No Effect

## Purpose

This fixture demonstrates a common game server anti-pattern where AJAX handlers return success responses without actually performing the requested operation. The UI shows "success" but nothing happened on the server.

## Files

- `ajax_handler.php` - PHP AJAX handler with fake success returns

## Expected Findings

| # | Type | Severity | Location | Message |
|---|------|----------|----------|---------|
| 1 | `fake_success_return` | CRITICAL | ajax_handler.php:38 | Function returns success without database mutation |
| 2 | `fake_success_return` | CRITICAL | ajax_handler.php:68 | Function returns success without database mutation |
| 3 | `hardcoded_response` | HIGH | ajax_handler.php:41 | Response contains hardcoded value 'new_level: 5' |
| 4 | `hardcoded_response` | HIGH | ajax_handler.php:71 | Response contains random fake ID |
| 5 | `security_bypass` | CRITICAL | ajax_handler.php:78 | Authorization check always returns true |
| 6 | `code_marker` | WARNING | ajax_handler.php:77 | TODO: Actually check database |

## Required Evidence

| Evidence Type | Description | Proof Level |
|---------------|-------------|-------------|
| `function_analysis` | Parse function body and identify return statements | P2 (STATIC_PARTIAL) |
| `mutation_tracking` | Track database calls (mysqli, PDO, etc.) | P2 (STATIC_PARTIAL) |
| `return_before_mutation` | Verify success returns without preceding mutations | P2 (STATIC_PARTIAL) |
| `database_trace` | (OPTIONAL) Actually run and verify no DB changes | P3 (DYNAMIC_VERIFIED) |

## Forbidden False Positives

- Should NOT flag functions that only read data (GET requests)
- Should NOT flag functions that delegate to other functions
- Should NOT flag functions that use external services (can't trace)

## Golden Output Reference

See: `specs/goldens/php-ajax-no-effect.json`

## Game Server Context

This pattern is extremely common in:
- Travian/TravianZ/TWLan private servers
- MapleStory web panels
- Browser game backends

The root cause is usually copy-paste development where the success response is added before the actual logic.
