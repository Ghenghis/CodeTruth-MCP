# Fixture: Cron Never Runs

## Purpose

This fixture demonstrates code that is designed to run as a cron job but is never actually invoked. The code exists and would work, but the crontab entry is missing, commented out, or points to the wrong file.

## Files

- `cron_processor.php` - PHP cron script with resource and building queue processing
- `crontab.example` - Example crontab showing misconfiguration

## Expected Findings

| # | Type | Severity | Location | Message |
|---|------|----------|----------|---------|
| 1 | `unreachable_cron` | CRITICAL | cron_processor.php:1 | File appears to be cron script but no crontab entry found |
| 2 | `cron_path_mismatch` | HIGH | crontab.example:12 | Crontab points to 'cron_old.php' but 'cron_processor.php' exists |
| 3 | `dead_code` | HIGH | cron_processor.php:18 | Function 'processBuildingQueue' is never called externally |
| 4 | `dead_code` | HIGH | cron_processor.php:42 | Function 'processResourceTick' is never called externally |
| 5 | `entry_point_unreachable` | CRITICAL | cron_processor.php:67 | Function 'runCron' is entry point but file is never executed |

## Required Evidence

| Evidence Type | Description | Proof Level |
|---------------|-------------|-------------|
| `file_analysis` | Identify file as cron script (CLI check, scheduled patterns) | P2 (STATIC_PARTIAL) |
| `crontab_scan` | Parse crontab files for references to this file | P3 (DYNAMIC_VERIFIED) |
| `path_resolution` | Verify crontab paths resolve to actual files | P3 (DYNAMIC_VERIFIED) |
| `execution_trace` | (OPTIONAL) Check if file was ever executed | P4 (DYNAMIC_SAMPLED) |

## Forbidden False Positives

- Should NOT flag cron scripts that are called by other cron scripts
- Should NOT flag scripts that are invoked via web hooks
- Should NOT flag scripts with valid crontab entries

## Golden Output Reference

See: `specs/goldens/php-cron-never-runs.json`

## Game Server Context

This pattern is catastrophic in game servers because:
- Buildings never complete construction
- Resources never generate
- Troops never finish training
- The game appears to work but nothing progresses

Players often report "my building has been constructing for 3 days" - this is usually the cause.

## Detection Strategy

1. Identify PHP files with cron-like patterns:
   - `php_sapi_name() === 'cli'` checks
   - "cron" in filename
   - Scheduled task patterns (process queues, tick resources)

2. Scan for crontab references:
   - `/etc/crontab`
   - `/var/spool/cron/*`
   - `crontab -l` output
   - `.crontab` files in repo

3. Cross-reference paths:
   - Does the crontab path match the actual file location?
   - Is the entry commented out?
   - Is there any entry at all?
