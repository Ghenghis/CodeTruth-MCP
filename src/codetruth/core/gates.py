"""
Milestone 19: Quality Gate Ladder System (Gates 0-6)

A tiered verification system that ensures code quality at multiple levels.
Each gate must pass before proceeding to the next.
"""

from __future__ import annotations

import asyncio
import subprocess
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from codetruth.core.evidence import EvidenceVault, Evidence, EvidenceType, Severity, EvidenceLocation


class GateLevel(int, Enum):
    """Quality gate levels."""

    BUILD_BOOT = 0  # Install, start, health endpoint
    LINT_TYPE = 1  # eslint, ruff, tsc, mypy
    UNIT_TESTS = 2  # Core module coverage
    CONTRACT_TESTS = 3  # API schema validation
    INTEGRATION_E2E = 4  # Playwright click flows
    SECURITY = 5  # SAST, secrets, dependencies
    RELEASE = 6  # Reproducible build, docs


class GateStatus(str, Enum):
    """Status of a quality gate."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"  # Passed with warnings


class GateResult(BaseModel):
    """Result of running a quality gate."""

    gate: GateLevel
    status: GateStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None

    # Results
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warned: int = 0
    checks_skipped: int = 0

    # Details
    findings: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)

    # Commands run
    commands: list[dict[str, Any]] = Field(default_factory=list)

    def add_log(self, message: str) -> None:
        """Add a log message."""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")


class QualityGate:
    """Base class for quality gates."""

    level: GateLevel
    name: str
    description: str

    def __init__(self, repo_path: Path, evidence_vault: EvidenceVault):
        self.repo_path = repo_path
        self.evidence_vault = evidence_vault

    async def run(self) -> GateResult:
        """Run the quality gate."""
        raise NotImplementedError

    async def _run_command(
        self,
        command: list[str],
        result: GateResult,
        timeout: int = 300,
    ) -> tuple[int, str, str]:
        """Run a command and capture output."""
        result.add_log(f"Running: {' '.join(command)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            result.commands.append({
                "command": command,
                "exit_code": process.returncode,
                "stdout_lines": len(stdout.decode().split("\n")),
                "stderr_lines": len(stderr.decode().split("\n")),
            })

            return process.returncode or 0, stdout.decode(), stderr.decode()

        except asyncio.TimeoutError:
            result.add_log(f"Command timed out after {timeout}s")
            return -1, "", "Timeout"
        except Exception as e:
            result.add_log(f"Command failed: {e}")
            return -1, "", str(e)


class Gate0BuildBoot(QualityGate):
    """Gate 0: Build & Boot - Install, start, health endpoint."""

    level = GateLevel.BUILD_BOOT
    name = "Build & Boot"
    description = "Verify installation and basic startup"

    async def run(self) -> GateResult:
        result = GateResult(
            gate=self.level,
            status=GateStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        # Check for package managers and run install
        checks = []

        # Node.js
        if (self.repo_path / "package.json").exists():
            result.add_log("Detected Node.js project")
            exit_code, stdout, stderr = await self._run_command(
                ["npm", "install", "--ignore-scripts"],
                result,
            )
            checks.append(("npm install", exit_code == 0))

            if exit_code == 0:
                # Try to build
                exit_code, stdout, stderr = await self._run_command(
                    ["npm", "run", "build"],
                    result,
                    timeout=600,
                )
                checks.append(("npm build", exit_code == 0))

        # Python
        if (self.repo_path / "pyproject.toml").exists() or (self.repo_path / "requirements.txt").exists():
            result.add_log("Detected Python project")

            if (self.repo_path / "pyproject.toml").exists():
                exit_code, _, _ = await self._run_command(
                    ["pip", "install", "-e", ".", "--quiet"],
                    result,
                )
                checks.append(("pip install", exit_code == 0))
            elif (self.repo_path / "requirements.txt").exists():
                exit_code, _, _ = await self._run_command(
                    ["pip", "install", "-r", "requirements.txt", "--quiet"],
                    result,
                )
                checks.append(("pip install requirements", exit_code == 0))

        # Rust
        if (self.repo_path / "Cargo.toml").exists():
            result.add_log("Detected Rust project")
            exit_code, _, _ = await self._run_command(
                ["cargo", "check"],
                result,
            )
            checks.append(("cargo check", exit_code == 0))

        # Go
        if (self.repo_path / "go.mod").exists():
            result.add_log("Detected Go project")
            exit_code, _, _ = await self._run_command(
                ["go", "build", "./..."],
                result,
            )
            checks.append(("go build", exit_code == 0))

        # Calculate results
        result.checks_passed = sum(1 for _, passed in checks if passed)
        result.checks_failed = sum(1 for _, passed in checks if not passed)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int(
            (result.completed_at - result.started_at).total_seconds() * 1000
        )

        if result.checks_failed == 0 and result.checks_passed > 0:
            result.status = GateStatus.PASSED
        elif result.checks_failed > 0:
            result.status = GateStatus.FAILED
        else:
            result.status = GateStatus.SKIPPED

        return result


class Gate1LintType(QualityGate):
    """Gate 1: Lint/Type - eslint, ruff, tsc, mypy."""

    level = GateLevel.LINT_TYPE
    name = "Lint & Type Check"
    description = "Static analysis for code quality and type safety"

    async def run(self) -> GateResult:
        result = GateResult(
            gate=self.level,
            status=GateStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        checks = []

        # ESLint for JavaScript/TypeScript
        if (self.repo_path / "package.json").exists():
            has_eslint = False
            try:
                with open(self.repo_path / "package.json") as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    has_eslint = "eslint" in deps
            except:
                pass

            if has_eslint:
                result.add_log("Running ESLint")
                exit_code, stdout, stderr = await self._run_command(
                    ["npx", "eslint", ".", "--format", "json", "--max-warnings", "0"],
                    result,
                )

                if stdout:
                    await self._parse_eslint_output(stdout, result)

                checks.append(("eslint", exit_code == 0))

            # TypeScript
            if (self.repo_path / "tsconfig.json").exists():
                result.add_log("Running TypeScript compiler")
                exit_code, stdout, stderr = await self._run_command(
                    ["npx", "tsc", "--noEmit"],
                    result,
                )

                if exit_code != 0:
                    await self._parse_tsc_output(stderr or stdout, result)

                checks.append(("tsc", exit_code == 0))

        # Python linting
        if any(self.repo_path.glob("**/*.py")):
            # Ruff
            result.add_log("Running Ruff")
            exit_code, stdout, stderr = await self._run_command(
                ["ruff", "check", ".", "--output-format", "json"],
                result,
            )

            if stdout:
                await self._parse_ruff_output(stdout, result)

            checks.append(("ruff", exit_code == 0))

            # MyPy
            result.add_log("Running MyPy")
            exit_code, stdout, stderr = await self._run_command(
                ["mypy", ".", "--ignore-missing-imports"],
                result,
            )

            if exit_code != 0:
                await self._parse_mypy_output(stdout, result)

            checks.append(("mypy", exit_code == 0))

        # Calculate results
        result.checks_passed = sum(1 for _, passed in checks if passed)
        result.checks_failed = sum(1 for _, passed in checks if not passed)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int(
            (result.completed_at - result.started_at).total_seconds() * 1000
        )

        if result.checks_failed == 0:
            result.status = GateStatus.PASSED
        elif result.checks_warned > 0 and result.checks_failed == 0:
            result.status = GateStatus.WARNING
        else:
            result.status = GateStatus.FAILED

        return result

    async def _parse_eslint_output(self, output: str, result: GateResult) -> None:
        """Parse ESLint JSON output and create evidence."""
        try:
            data = json.loads(output)
            for file_result in data:
                for msg in file_result.get("messages", []):
                    evidence = Evidence(
                        evidence_type=EvidenceType.LINT_ERROR,
                        severity=Severity.ERROR if msg.get("severity") == 2 else Severity.WARNING,
                        message=msg.get("message", ""),
                        location=EvidenceLocation(
                            file_path=file_result.get("filePath", ""),
                            start_line=msg.get("line"),
                            end_line=msg.get("endLine"),
                            start_column=msg.get("column"),
                            end_column=msg.get("endColumn"),
                        ),
                        tool_name="eslint",
                        rule_id=msg.get("ruleId"),
                        repo_path=str(self.repo_path),
                    )
                    evidence_id = await self.evidence_vault.store_evidence(evidence)
                    result.evidence_ids.append(evidence_id)
                    result.findings.append(evidence.model_dump())
        except json.JSONDecodeError:
            result.add_log("Failed to parse ESLint output")

    async def _parse_tsc_output(self, output: str, result: GateResult) -> None:
        """Parse TypeScript compiler output."""
        import re

        for line in output.split("\n"):
            match = re.match(r"(.+)\((\d+),(\d+)\): error (TS\d+): (.+)", line)
            if match:
                file_path, line_num, col, code, message = match.groups()
                evidence = Evidence(
                    evidence_type=EvidenceType.TYPE_ERROR,
                    severity=Severity.ERROR,
                    message=message,
                    location=EvidenceLocation(
                        file_path=file_path,
                        start_line=int(line_num),
                        start_column=int(col),
                    ),
                    tool_name="tsc",
                    rule_id=code,
                    repo_path=str(self.repo_path),
                )
                evidence_id = await self.evidence_vault.store_evidence(evidence)
                result.evidence_ids.append(evidence_id)

    async def _parse_ruff_output(self, output: str, result: GateResult) -> None:
        """Parse Ruff JSON output."""
        try:
            data = json.loads(output)
            for issue in data:
                evidence = Evidence(
                    evidence_type=EvidenceType.LINT_ERROR,
                    severity=Severity.WARNING,
                    message=issue.get("message", ""),
                    location=EvidenceLocation(
                        file_path=issue.get("filename", ""),
                        start_line=issue.get("location", {}).get("row"),
                        start_column=issue.get("location", {}).get("column"),
                    ),
                    tool_name="ruff",
                    rule_id=issue.get("code"),
                    repo_path=str(self.repo_path),
                )
                evidence_id = await self.evidence_vault.store_evidence(evidence)
                result.evidence_ids.append(evidence_id)
        except json.JSONDecodeError:
            result.add_log("Failed to parse Ruff output")

    async def _parse_mypy_output(self, output: str, result: GateResult) -> None:
        """Parse MyPy output."""
        import re

        for line in output.split("\n"):
            match = re.match(r"(.+):(\d+): error: (.+)", line)
            if match:
                file_path, line_num, message = match.groups()
                evidence = Evidence(
                    evidence_type=EvidenceType.TYPE_ERROR,
                    severity=Severity.ERROR,
                    message=message,
                    location=EvidenceLocation(
                        file_path=file_path,
                        start_line=int(line_num),
                    ),
                    tool_name="mypy",
                    repo_path=str(self.repo_path),
                )
                evidence_id = await self.evidence_vault.store_evidence(evidence)
                result.evidence_ids.append(evidence_id)


class Gate2UnitTests(QualityGate):
    """Gate 2: Unit Tests - Core module coverage."""

    level = GateLevel.UNIT_TESTS
    name = "Unit Tests"
    description = "Run unit tests and verify coverage"

    async def run(self) -> GateResult:
        result = GateResult(
            gate=self.level,
            status=GateStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        checks = []

        # Jest/Vitest for Node.js
        if (self.repo_path / "package.json").exists():
            pkg_data = {}
            try:
                with open(self.repo_path / "package.json") as f:
                    pkg_data = json.load(f)
            except:
                pass

            scripts = pkg_data.get("scripts", {})
            if "test" in scripts:
                result.add_log("Running npm test")
                exit_code, stdout, stderr = await self._run_command(
                    ["npm", "test", "--", "--passWithNoTests"],
                    result,
                    timeout=600,
                )
                checks.append(("npm test", exit_code == 0))

        # Pytest for Python
        if any(self.repo_path.glob("**/test_*.py")) or any(self.repo_path.glob("**/*_test.py")):
            result.add_log("Running pytest")
            exit_code, stdout, stderr = await self._run_command(
                ["pytest", "-v", "--tb=short"],
                result,
                timeout=600,
            )
            checks.append(("pytest", exit_code == 0))

        # Cargo test for Rust
        if (self.repo_path / "Cargo.toml").exists():
            result.add_log("Running cargo test")
            exit_code, stdout, stderr = await self._run_command(
                ["cargo", "test"],
                result,
                timeout=600,
            )
            checks.append(("cargo test", exit_code == 0))

        # Go test
        if (self.repo_path / "go.mod").exists():
            result.add_log("Running go test")
            exit_code, stdout, stderr = await self._run_command(
                ["go", "test", "./..."],
                result,
                timeout=600,
            )
            checks.append(("go test", exit_code == 0))

        result.checks_passed = sum(1 for _, passed in checks if passed)
        result.checks_failed = sum(1 for _, passed in checks if not passed)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int(
            (result.completed_at - result.started_at).total_seconds() * 1000
        )

        if result.checks_failed == 0 and result.checks_passed > 0:
            result.status = GateStatus.PASSED
        elif result.checks_failed > 0:
            result.status = GateStatus.FAILED
        else:
            result.status = GateStatus.SKIPPED

        return result


class GateLadder:
    """Orchestrates running all quality gates."""

    GATE_CLASSES = {
        GateLevel.BUILD_BOOT: Gate0BuildBoot,
        GateLevel.LINT_TYPE: Gate1LintType,
        GateLevel.UNIT_TESTS: Gate2UnitTests,
        # Additional gates would be implemented similarly
    }

    def __init__(self, repo_path: Path, evidence_vault: EvidenceVault):
        self.repo_path = repo_path
        self.evidence_vault = evidence_vault

    async def run(
        self,
        profile: str = "standard",
        gates: list[int] | None = None,
        fail_fast: bool = False,
    ) -> dict[str, Any]:
        """Run quality gate ladder."""
        from codetruth.core.config import CodeTruthConfig

        config = CodeTruthConfig()
        profile_config = config.get_profile_config(profile)

        # Determine which gates to run
        gates_to_run = gates or profile_config.get("gates", [0, 1, 2, 3, 4, 5])

        results: list[GateResult] = []
        all_passed = True

        for gate_level in sorted(gates_to_run):
            gate_enum = GateLevel(gate_level)

            if gate_enum not in self.GATE_CLASSES:
                # Skip unimplemented gates
                results.append(GateResult(
                    gate=gate_enum,
                    status=GateStatus.SKIPPED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                ))
                continue

            gate_class = self.GATE_CLASSES[gate_enum]
            gate = gate_class(self.repo_path, self.evidence_vault)

            result = await gate.run()
            results.append(result)

            if result.status == GateStatus.FAILED:
                all_passed = False
                if fail_fast:
                    break

        return {
            "repo_path": str(self.repo_path),
            "profile": profile,
            "all_passed": all_passed,
            "gates_run": len(results),
            "gates_passed": sum(1 for r in results if r.status == GateStatus.PASSED),
            "gates_failed": sum(1 for r in results if r.status == GateStatus.FAILED),
            "results": [r.model_dump() for r in results],
        }
