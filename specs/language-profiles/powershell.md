# Language Truth Profile: PowerShell

**Profile Version:** 1.0.0
**Language Version:** PowerShell 5.1+ (Windows), PowerShell 7+ (Cross-platform)
**Stack Tier:** 3 (Production & Infra)
**Profile Completeness:** 0.80
**Implementation Completeness:** 0.70

---

## Overview

PowerShell appears in 3 repos directly, but is embedded in many others for:
- **Build automation** (build scripts, deployment)
- **System administration** (server management, game server ops)
- **CI/CD pipelines** (GitHub Actions, Azure DevOps)
- **Game server management** (MapleStory server scripts, game bot automation)
- **Windows tool scripting** (desktop automation)

### Automation Context (Critical)

PowerShell automation scripts have unique failure patterns:
- Scripts that parse parameters but don't use them
- Error handling that silently continues
- Commands that succeed but have no effect
- Pipeline stages that filter to empty
- Scheduled tasks that never run

---

## File Identification

| Pattern | Type | Description |
|---------|------|-------------|
| `*.ps1` | Extension | PowerShell scripts |
| `*.psm1` | Extension | PowerShell modules |
| `*.psd1` | Extension | PowerShell data/manifest |
| `*.ps1xml` | Extension | Format/type definitions |
| `profile.ps1` | Filename | User profile |
| `Microsoft.PowerShell_profile.ps1` | Filename | PowerShell profile |
| `build.ps1` | Filename | Build scripts |
| `deploy.ps1` | Filename | Deployment scripts |
| `*.pssc` | Extension | Session config |

---

## Parse Capability

### Parser Configuration

| Property | Value |
|----------|-------|
| Parser Type | tree_sitter + ast_native |
| Parser Name | tree-sitter-powershell + [System.Management.Automation.Language.Parser] |
| Grammar Version | 0.15.0 |
| Syntax Accuracy | 0.90 |
| Semantic Accuracy | 0.70 |

### Parse Features

| Feature | Supported | Notes |
|---------|-----------|-------|
| Partial parsing | Yes | Tree-sitter recovers |
| Error recovery | Partial | Some edge cases fail |
| Incremental parsing | Yes | Supported |
| Comment preservation | Yes | Comment-based help extracted |
| Here-string parsing | Yes | @""@ and @''@ |

### Known Parse Failures

1. **Complex here-strings**: Nested here-strings
2. **DSC configurations**: Domain-specific extensions
3. **Class definitions**: PowerShell 5+ classes
4. **Using statements**: Namespace imports

---

## Semantic Capability

### Type System

| Property | Value |
|----------|-------|
| Type Inference Level | basic (type constraints on parameters) |
| Import Resolution | Yes (modules, dot-sourcing) |
| Type Resolution | Partial (.NET types) |
| Mutation Tracking | No |
| Control Flow Analysis | Yes |
| Data Flow Analysis | Partial |

### Scope Analysis

| Feature | Supported | Accuracy |
|---------|-----------|----------|
| Scope Resolution | Yes | 0.80 |
| Shadowing Detection | Yes | 0.75 |
| Closure Detection | Yes | 0.70 |
| Cross-file Resolution | Partial | 0.60 |
| Module Resolution | Yes | 0.75 |

### Semantic Blindspots

| Blindspot | Impact | Severity | Mitigation |
|-----------|--------|----------|------------|
| Invoke-Expression | false_negative | critical | Ban via PSScriptAnalyzer |
| Dynamic cmdlet names | false_negative | high | Static cmdlet names |
| Remoting (Invoke-Command) | incomplete | critical | Remote audit |
| COM objects | incomplete | high | COM interface docs |
| .NET reflection | false_negative | high | Type documentation |
| Splatting | incomplete | medium | Expand splats |
| $ExecutionContext | false_negative | critical | Avoid meta-programming |

---

## Wiring Capability

### Graph Construction

| Graph Type | Supported | Completeness | Proof Level |
|------------|-----------|--------------|-------------|
| Call Graph | Yes | 0.65 | P2 (STATIC_PARTIAL) |
| Event Graph | Partial | 0.40 | P5 (HEURISTIC) |
| Route Graph | No | 0.00 | P7 (IMPOSSIBLE) |
| Data Flow Graph | Partial | 0.55 | P5 (HEURISTIC) |

### Boundary Detection

| Boundary Type | Detected | Proof Level |
|---------------|----------|-------------|
| HTTP Calls (Invoke-WebRequest/RestMethod) | Yes | P2 |
| Database (Invoke-SqlCmd) | Yes | P2 |
| File I/O | Yes | P1 |
| Process Spawn (Start-Process) | Yes | P1 |
| Registry Operations | Yes | P2 |
| WMI/CIM Queries | Yes | P2 |
| Remote Commands | Partial | P5 |
| Scheduled Tasks | Partial | P5 |

### Reachability Proofs

| Proof Type | Supported | Confidence |
|------------|-----------|------------|
| Prove Reachable | Yes | 0.65 |
| Prove Unreachable | Partial | 0.45 |

### Wiring Blindspots

| Blindspot | Impact | Severity | Example |
|-----------|--------|----------|---------|
| Invoke-Expression | false_negative | critical | `Invoke-Expression $cmd` |
| Dynamic cmdlet | false_negative | high | `& $cmdletName` |
| Remote sessions | incomplete | critical | `Invoke-Command -Session $s` |
| Module auto-loading | incomplete | medium | Implicit module import |
| Event subscriptions | incomplete | high | `Register-ObjectEvent` |
| DSC resources | incomplete | high | Configuration blocks |

---

## Runtime Capability

### Execution Environment

| Property | Value |
|----------|-------|
| Can Execute | Yes |
| Environment | PowerShell 5.1 / pwsh 7+ |
| Min Version | 5.1 (Windows), 7.0 (cross-platform) |

### Instrumentation

| Feature | Supported | Tool |
|---------|-----------|------|
| Code Instrumentation | Partial | Script block logging |
| Execution Tracing | Yes | Transcript, -Verbose |
| Performance Profiling | Partial | Measure-Command |
| State Snapshots | Partial | Variable export |

### Testing

| Test Type | Supported | Framework |
|-----------|-----------|-----------|
| Unit Tests | Yes | Pester |
| Integration Tests | Yes | Pester |
| E2E Tests | Partial | Pester + automation |

### Coverage

| Property | Value |
|----------|-------|
| Coverage Supported | Yes |
| Granularity | line |
| Tool | Pester code coverage |

### Runtime Blindspots

| Blindspot | Impact | Severity | Reason |
|-----------|--------|----------|--------|
| Remote execution | incomplete | critical | Different machine |
| Background jobs | incomplete | high | Separate runspace |
| COM automation | incomplete | high | External object |
| .NET code | incomplete | medium | Assembly execution |
| Native executables | incomplete | high | External process |
| Scheduled task context | incomplete | critical | Different user/session |

---

## Automation Patterns (CRITICAL SECTION)

### Build Script
```powershell
# build.ps1
param(
    [string]$Configuration = "Release",
    [switch]$SkipTests
)

# VERIFY: Parameters actually used
Write-Host "Building in $Configuration mode"

# VERIFY: Command succeeds AND has effect
dotnet build -c $Configuration

if (-not $SkipTests) {
    # VERIFY: Tests actually run
    dotnet test
}

# FAILURE PATTERN: Returns success without checking
# $LASTEXITCODE not checked!
```

### Deployment Script
```powershell
# deploy.ps1
param(
    [Parameter(Mandatory)]
    [string]$Environment,

    [Parameter(Mandatory)]
    [string]$Version
)

# VERIFY: Actually deploys, not just logs
Write-Host "Deploying version $Version to $Environment"

# FAILURE PATTERN: Copies file but service not restarted
Copy-Item ".\app\*" "\\server\deploy\" -Recurse

# MISSING: Restart service
# MISSING: Health check
# MISSING: Rollback on failure
```

### Scheduled Task
```powershell
# cleanup.ps1 (scheduled to run daily)
# VERIFY: Actually scheduled in Task Scheduler
# VERIFY: Task runs with correct permissions

$logPath = "C:\Logs"
$daysToKeep = 7

# VERIFY: Actually deletes files
Get-ChildItem $logPath -Recurse |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$daysToKeep) } |
    Remove-Item -Force

# FAILURE PATTERN: Pipeline returns empty, nothing deleted
# No error if $logPath doesn't exist (Get-ChildItem silently returns nothing)
```

### Game Server Management
```powershell
# start-server.ps1
param(
    [string]$ServerPath = "C:\GameServer",
    [int]$Port = 8484
)

# VERIFY: Server process starts
$process = Start-Process "$ServerPath\server.exe" -ArgumentList "-p $Port" -PassThru

# FAILURE PATTERN: Process starts but crashes immediately
# No health check, no wait for ready

# VERIFY: Server is actually accepting connections
# MISSING: Test-NetConnection or similar
```

### Detection Rules for Automation

| Pattern | Detection Method | Evidence Required |
|---------|------------------|-------------------|
| Parameter unused | AST analysis - param vs usage | Usage count > 0 |
| Command no error check | $LASTEXITCODE not checked | Error handling proof |
| Pipeline to empty | Empty pipeline possible | Pipeline analysis |
| Scheduled task missing | Script vs Task Scheduler | Task export |
| Remote call no verify | Invoke-Command without check | Return value check |

---

## Evidence Artifacts

| Artifact | Format | Proof Level | Trust Level | Deterministic | Requires Runtime |
|----------|--------|-------------|-------------|---------------|------------------|
| ast_graph | json | P1 | T0 | Yes | No |
| command_graph | json | P2 | T0 | Yes | No |
| module_imports | json | P2 | T0 | Yes | No |
| parameter_usage | json | P2 | T0 | Yes | No |
| pester_results | nunitxml | P4 | T0 | No | Yes |
| coverage_report | json | P4 | T0 | No | Yes |
| transcript | log | P3 | T0 | No | Yes |

---

## Critical Blindspots (MANDATORY SECTION)

### Category: Parsing

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | DSC configurations | Domain-specific syntax | Extension to language | DSC-specific analysis |
| 2 | Class definitions | PS 5.0+ class syntax | Newer grammar | Updated parser |

### Category: Semantic

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Invoke-Expression | Arbitrary code execution | String to code | PSScriptAnalyzer ban |
| 2 | Dynamic cmdlets | `& $variable` calls | Variable dispatch | Static cmdlet names |
| 3 | Module auto-loading | Implicit import | System behavior | Explicit Import-Module |
| 4 | COM objects | Dynamic dispatch | COM interop | Interface documentation |

### Category: Wiring

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Remoting | Invoke-Command to remote | Network boundary | Remote manifest |
| 2 | Background jobs | Start-Job, runspaces | Parallel execution | Job tracking |
| 3 | Event subscriptions | Register-*Event | Async handlers | Event inventory |
| 4 | Splatting | @params expansion | Indirect parameters | Expand in analysis |

### Category: Runtime

| # | Name | Description | Reason | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Execution policy | May block scripts | Security feature | Policy documentation |
| 2 | Profile loading | profile.ps1 auto-executes | User environment | Profile audit |
| 3 | Module paths | $env:PSModulePath | Environment-dependent | Explicit paths |
| 4 | Constrained language | Restricted commands | Security mode | Mode detection |

---

## Cross-Language Boundaries

| Target Language | Boundary Type | Detection | Tracing | Contract Verification | Proof Level |
|-----------------|---------------|-----------|---------|----------------------|-------------|
| .NET (Add-Type) | interop | Yes | Partial | Partial | P3 |
| CMD (cmd.exe) | process | Yes | Partial | No | P3 |
| Python (python.exe) | process | Yes | Partial | No | P3 |
| SQL (Invoke-SqlCmd) | database | Yes | Partial | Yes (schema) | P2 |
| REST API | http | Yes | Partial | Yes (OpenAPI) | P2 |
| Registry | system | Yes | Yes | No | P2 |

### Common Boundary Patterns

```powershell
# Pattern 1: REST API call
$response = Invoke-RestMethod -Uri "https://api.example.com/data" -Method Get
# VERIFY: Response actually used, not just fetched

# Pattern 2: Process spawn
$result = & python.exe script.py --arg value
# VERIFY: $LASTEXITCODE checked

# Pattern 3: SQL query
$data = Invoke-SqlCmd -ServerInstance "server" -Query "SELECT * FROM users"
# VERIFY: Query returns expected data

# Pattern 4: .NET interop
Add-Type -AssemblyName System.Web
$encoded = [System.Web.HttpUtility]::UrlEncode($value)
# Traceable, but .NET internals opaque
```

---

## Failure Patterns

### Pattern 1: Parameter Defined But Unused

**Description:** Script parameter never referenced in body

**Detection:** AST parameter list vs variable references

**Example:**
```powershell
param(
    [string]$OutputPath,  # DETECTED: Never used
    [switch]$Force
)

# Only uses $Force, not $OutputPath
if ($Force) { ... }
```

### Pattern 2: No Error Handling

**Description:** Commands can fail silently

**Detection:** Check $LASTEXITCODE, -ErrorAction, try/catch

**Example:**
```powershell
# DETECTED: No error handling
Copy-Item $source $dest
Remove-Item $temp
# If Copy fails, Remove still runs!
```

### Pattern 3: Empty Pipeline

**Description:** Pipeline filters to nothing, no action taken

**Detection:** Pipeline analysis for potential empty result

**Example:**
```powershell
# DETECTED: May return nothing
Get-Process "NonExistent*" | Stop-Process
# No error if no matching process
```

### Pattern 4: Scheduled Task Not Registered

**Description:** Script exists but not scheduled

**Detection:** Compare scripts with Get-ScheduledTask output

**Example:**
```powershell
# cleanup.ps1 exists but:
# - Not in Task Scheduler
# - Or disabled
# - Or wrong path
# DETECTED: Script not scheduled
```

---

## Confidence Computation

```
confidence = (
    parse_accuracy × 0.15 +           # 0.90 × 0.15 = 0.135
    semantic_accuracy × 0.20 +        # 0.70 × 0.20 = 0.140
    wiring_completeness × 0.25 +      # 0.55 × 0.25 = 0.138
    runtime_capability × 0.25 +       # 0.70 × 0.25 = 0.175
    (1 - blindspot_penalty) × 0.15    # 0.60 × 0.15 = 0.090
)
```

**Current Score:** 0.68 (PARTIAL)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-18 | Initial profile |
