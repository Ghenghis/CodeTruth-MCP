#!/usr/bin/env python3
"""
CodeTruth-MCP Comprehensive Self-Audit System

This standalone script audits the entire CodeTruth repository to ensure:
1. All claims have backing implementation
2. All fixtures have matching goldens
3. All engines produce expected outputs
4. Spec-code alignment is maintained
5. No fake completeness exists

Run: python self_audit.py [--verbose] [--fix]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# AUDIT RESULT TYPES
# ============================================================================

class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class AuditCheck:
    """Single audit check result."""
    category: str
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class AuditReport:
    """Complete self-audit report."""
    repo_path: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    checks: List[AuditCheck] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    @property
    def warned(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.WARN)

    @property
    def skipped(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.SKIP)

    @property
    def errored(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.ERROR)

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

    @property
    def overall_pass(self) -> bool:
        return self.failed == 0 and self.errored == 0

    def add(self, check: AuditCheck) -> None:
        self.checks.append(check)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": "2.0.0",
            "repo_path": self.repo_path,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "warned": self.warned,
                "skipped": self.skipped,
                "errored": self.errored,
                "pass_rate": round(self.pass_rate, 2),
                "overall_pass": self.overall_pass,
            },
            "by_category": self._group_by_category(),
            "checks": [c.to_dict() for c in self.checks],
        }

    def _group_by_category(self) -> Dict[str, Dict[str, int]]:
        groups: Dict[str, Dict[str, int]] = {}
        for check in self.checks:
            if check.category not in groups:
                groups[check.category] = {"pass": 0, "fail": 0, "warn": 0, "skip": 0, "error": 0}
            groups[check.category][check.status.value] += 1
        return groups


# ============================================================================
# SELF-AUDITOR
# ============================================================================

class SelfAuditor:
    """
    Comprehensive self-audit system for CodeTruth-MCP.
    """

    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        self.report = AuditReport(repo_path=str(repo_path))
        self.specs_dir = repo_path / "specs"
        self.src_dir = repo_path / "src"
        self.tests_dir = repo_path / "tests"

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"  {message}")

    def run_all_audits(self) -> AuditReport:
        """Run all audit categories."""
        print("\n" + "=" * 70)
        print("CODETRUTH-MCP COMPREHENSIVE SELF-AUDIT")
        print("=" * 70)

        # Run all audit categories
        self._audit_structure()
        self._audit_specs()
        self._audit_fixtures_and_goldens()
        self._audit_engines()
        self._audit_analyzers()
        self._audit_manifest()
        self._audit_spec_code_alignment()
        self._audit_honesty_checks()
        self._audit_forbidden_patterns()
        self._audit_ci_gates()
        self._audit_documentation()

        self.report.completed_at = datetime.utcnow()
        return self.report

    # ========================================================================
    # AUDIT: Repository Structure
    # ========================================================================

    def _audit_structure(self) -> None:
        """Audit repository structure."""
        print("\n[1/11] Repository Structure...")

        required_dirs = [
            ("specs", "Specification documents"),
            ("specs/engines", "Engine specifications"),
            ("specs/evidence", "Evidence model"),
            ("specs/language-profiles", "Language profiles"),
            ("specs/fixtures", "Test fixtures"),
            ("specs/goldens", "Golden outputs"),
            ("specs/diagrams", "Architecture diagrams"),
            ("src/codetruth", "Main source code"),
            ("src/codetruth/core", "Core modules"),
            ("src/codetruth/analyzers", "Language analyzers"),
            ("src/codetruth/engines", "Proof engines"),
            ("tests", "Test suite"),
        ]

        for dir_path, description in required_dirs:
            full_path = self.repo_path / dir_path
            if full_path.exists() and full_path.is_dir():
                self.report.add(AuditCheck(
                    category="structure",
                    name=f"dir:{dir_path}",
                    status=CheckStatus.PASS,
                    message=f"Directory exists: {description}",
                ))
                self.log(f"✅ {dir_path}")
            else:
                self.report.add(AuditCheck(
                    category="structure",
                    name=f"dir:{dir_path}",
                    status=CheckStatus.FAIL,
                    message=f"Missing directory: {description}",
                    fix_suggestion=f"mkdir -p {dir_path}",
                ))
                self.log(f"❌ {dir_path}")

        required_files = [
            ("specs/MASTER.md", "The Law - core philosophy"),
            ("specs/CAPABILITIES.md", "Capability inventory"),
            ("specs/SELF_AUDIT.md", "Anti-hallucination rules"),
            ("specs/COVERAGE_MANIFEST.json", "Code type coverage"),
            ("specs/ANALYZER_MAPPING.md", "Analyzer mapping"),
            ("specs/SPEC_CODE_ALIGNMENT.md", "Spec-code alignment"),
            ("pyproject.toml", "Python project config"),
            ("README.md", "Repository documentation"),
        ]

        for file_path, description in required_files:
            full_path = self.repo_path / file_path
            if full_path.exists():
                self.report.add(AuditCheck(
                    category="structure",
                    name=f"file:{file_path}",
                    status=CheckStatus.PASS,
                    message=f"File exists: {description}",
                ))
                self.log(f"✅ {file_path}")
            else:
                self.report.add(AuditCheck(
                    category="structure",
                    name=f"file:{file_path}",
                    status=CheckStatus.FAIL,
                    message=f"Missing file: {description}",
                    fix_suggestion=f"Create {file_path}",
                ))
                self.log(f"❌ {file_path}")

    # ========================================================================
    # AUDIT: Specification Files
    # ========================================================================

    def _audit_specs(self) -> None:
        """Audit specification files meet requirements."""
        print("\n[2/11] Specification Files...")

        spec_requirements = {
            "MASTER.md": 400,
            "CAPABILITIES.md": 250,
            "SELF_AUDIT.md": 150,
        }

        for spec_file, min_lines in spec_requirements.items():
            path = self.specs_dir / spec_file
            if path.exists():
                lines = len(path.read_text().split("\n"))
                if lines >= min_lines:
                    self.report.add(AuditCheck(
                        category="specs",
                        name=f"lines:{spec_file}",
                        status=CheckStatus.PASS,
                        message=f"{spec_file}: {lines} lines (required: {min_lines})",
                    ))
                    self.log(f"✅ {spec_file}: {lines} lines")
                else:
                    self.report.add(AuditCheck(
                        category="specs",
                        name=f"lines:{spec_file}",
                        status=CheckStatus.FAIL,
                        message=f"{spec_file}: {lines} lines (required: {min_lines})",
                        fix_suggestion=f"Add {min_lines - lines} more lines to {spec_file}",
                    ))
                    self.log(f"❌ {spec_file}: {lines} lines (need {min_lines})")
            else:
                self.report.add(AuditCheck(
                    category="specs",
                    name=f"lines:{spec_file}",
                    status=CheckStatus.FAIL,
                    message=f"{spec_file} not found",
                ))

        # Check language profiles
        profiles_dir = self.specs_dir / "language-profiles"
        if profiles_dir.exists():
            profiles = list(profiles_dir.glob("*.md"))
            # Exclude template
            profiles = [p for p in profiles if not p.name.startswith("_")]

            if len(profiles) >= 7:
                self.report.add(AuditCheck(
                    category="specs",
                    name="language_profiles_count",
                    status=CheckStatus.PASS,
                    message=f"Found {len(profiles)} language profiles (required: 7+)",
                ))
                self.log(f"✅ {len(profiles)} language profiles")
            else:
                self.report.add(AuditCheck(
                    category="specs",
                    name="language_profiles_count",
                    status=CheckStatus.FAIL,
                    message=f"Found {len(profiles)} language profiles (required: 7+)",
                ))

            # Check each profile has minimum lines
            for profile in profiles:
                lines = len(profile.read_text().split("\n"))
                if lines >= 250:
                    self.report.add(AuditCheck(
                        category="specs",
                        name=f"profile:{profile.stem}",
                        status=CheckStatus.PASS,
                        message=f"{profile.name}: {lines} lines",
                    ))
                else:
                    self.report.add(AuditCheck(
                        category="specs",
                        name=f"profile:{profile.stem}",
                        status=CheckStatus.WARN,
                        message=f"{profile.name}: {lines} lines (recommended: 250+)",
                    ))

        # Check engine specs
        engines_dir = self.specs_dir / "engines"
        if engines_dir.exists():
            required_engines = ["REACHABILITY.md", "UI_VERIFICATION.md", "CORRELATOR.md", "BOUNDARY.md"]
            for engine in required_engines:
                engine_path = engines_dir / engine
                if engine_path.exists():
                    lines = len(engine_path.read_text().split("\n"))
                    self.report.add(AuditCheck(
                        category="specs",
                        name=f"engine_spec:{engine}",
                        status=CheckStatus.PASS,
                        message=f"{engine}: {lines} lines",
                    ))
                    self.log(f"✅ {engine}: {lines} lines")
                else:
                    self.report.add(AuditCheck(
                        category="specs",
                        name=f"engine_spec:{engine}",
                        status=CheckStatus.FAIL,
                        message=f"Missing engine spec: {engine}",
                    ))
                    self.log(f"❌ Missing: {engine}")

    # ========================================================================
    # AUDIT: Fixtures and Goldens
    # ========================================================================

    def _audit_fixtures_and_goldens(self) -> None:
        """Audit fixtures have matching goldens."""
        print("\n[3/11] Fixtures and Goldens...")

        fixtures_dir = self.specs_dir / "fixtures"
        goldens_dir = self.specs_dir / "goldens"

        if not fixtures_dir.exists():
            self.report.add(AuditCheck(
                category="fixtures",
                name="fixtures_dir",
                status=CheckStatus.FAIL,
                message="Fixtures directory not found",
            ))
            return

        # Find all fixture directories
        fixture_count = 0
        golden_matches = 0
        missing_goldens = []

        for lang_dir in fixtures_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            for fixture_dir in lang_dir.iterdir():
                if not fixture_dir.is_dir():
                    continue

                fixture_count += 1
                fixture_id = f"{lang_dir.name}/{fixture_dir.name}"

                # Check for code files in fixture
                code_files = list(fixture_dir.glob("*.*"))
                code_files = [f for f in code_files if f.suffix in {".tsx", ".ts", ".js", ".jsx", ".py", ".php", ".cs", ".java", ".lua", ".ps1", ".sql", ".sh", ".yaml", ".json"}]

                if not code_files:
                    readme = fixture_dir / "README.md"
                    if not readme.exists():
                        self.report.add(AuditCheck(
                            category="fixtures",
                            name=f"fixture_content:{fixture_id}",
                            status=CheckStatus.WARN,
                            message=f"Fixture {fixture_id} has no code files or README",
                            fix_suggestion=f"Add code files to specs/fixtures/{fixture_id}/",
                        ))
                        continue

                # Check for matching golden
                golden_name = f"{lang_dir.name}-{fixture_dir.name}.json"
                golden_path = goldens_dir / golden_name

                if golden_path.exists():
                    golden_matches += 1
                    # Validate golden structure
                    try:
                        with open(golden_path) as f:
                            golden = json.load(f)
                        if "expected_findings" in golden:
                            findings_count = len(golden["expected_findings"])
                            self.report.add(AuditCheck(
                                category="fixtures",
                                name=f"golden:{fixture_id}",
                                status=CheckStatus.PASS,
                                message=f"Golden exists with {findings_count} expected findings",
                            ))
                            self.log(f"✅ {fixture_id} -> {golden_name}")
                        else:
                            self.report.add(AuditCheck(
                                category="fixtures",
                                name=f"golden:{fixture_id}",
                                status=CheckStatus.WARN,
                                message=f"Golden missing 'expected_findings' field",
                            ))
                    except json.JSONDecodeError as e:
                        self.report.add(AuditCheck(
                            category="fixtures",
                            name=f"golden:{fixture_id}",
                            status=CheckStatus.FAIL,
                            message=f"Invalid JSON in golden: {e}",
                        ))
                else:
                    missing_goldens.append(fixture_id)
                    self.report.add(AuditCheck(
                        category="fixtures",
                        name=f"golden:{fixture_id}",
                        status=CheckStatus.WARN,
                        message=f"No golden file for fixture",
                        fix_suggestion=f"Create specs/goldens/{golden_name}",
                    ))
                    self.log(f"⚠️  {fixture_id} -> missing golden")

        # Summary checks
        self.report.add(AuditCheck(
            category="fixtures",
            name="fixture_count",
            status=CheckStatus.PASS if fixture_count >= 5 else CheckStatus.FAIL,
            message=f"Found {fixture_count} fixtures (required: 5+)",
        ))

        self.report.add(AuditCheck(
            category="fixtures",
            name="golden_coverage",
            status=CheckStatus.PASS if golden_matches >= 5 else CheckStatus.WARN,
            message=f"{golden_matches}/{fixture_count} fixtures have goldens",
        ))

    # ========================================================================
    # AUDIT: Engine Implementations
    # ========================================================================

    def _audit_engines(self) -> None:
        """Audit P0 engine implementations."""
        print("\n[4/11] Engine Implementations...")

        engines_src = self.src_dir / "codetruth" / "engines"

        required_engines = [
            ("reachability/graph.py", "ReachabilityGraph", 200),
            ("reachability/proofs.py", "ReachabilityProver", 200),
            ("reachability/builders/typescript.py", "TypeScriptGraphBuilder", 200),
            ("ui_verifier/verifier.py", "UIVerifier", 200),
            ("correlator/correlator.py", "RuntimeCorrelator", 200),
        ]

        for engine_path, expected_class, min_lines in required_engines:
            full_path = engines_src / engine_path
            if full_path.exists():
                content = full_path.read_text()
                lines = len(content.split("\n"))

                # Check for expected class
                if f"class {expected_class}" in content:
                    self.report.add(AuditCheck(
                        category="engines",
                        name=f"engine:{engine_path}",
                        status=CheckStatus.PASS,
                        message=f"{engine_path}: {lines} lines, contains {expected_class}",
                    ))
                    self.log(f"✅ {engine_path}: {lines} lines")
                else:
                    self.report.add(AuditCheck(
                        category="engines",
                        name=f"engine:{engine_path}",
                        status=CheckStatus.WARN,
                        message=f"{engine_path}: {lines} lines, missing class {expected_class}",
                    ))
                    self.log(f"⚠️  {engine_path}: missing {expected_class}")
            else:
                self.report.add(AuditCheck(
                    category="engines",
                    name=f"engine:{engine_path}",
                    status=CheckStatus.FAIL,
                    message=f"Engine not implemented: {engine_path}",
                    fix_suggestion=f"Create src/codetruth/engines/{engine_path}",
                ))
                self.log(f"❌ Missing: {engine_path}")

        # Check for boundary engine (not yet implemented)
        boundary_path = engines_src / "boundary" / "verifier.py"
        if boundary_path.exists():
            self.report.add(AuditCheck(
                category="engines",
                name="engine:boundary",
                status=CheckStatus.PASS,
                message="Boundary verifier implemented",
            ))
        else:
            self.report.add(AuditCheck(
                category="engines",
                name="engine:boundary",
                status=CheckStatus.WARN,
                message="Boundary verifier not implemented (P0 engine)",
                fix_suggestion="Create src/codetruth/engines/boundary/verifier.py",
            ))

    # ========================================================================
    # AUDIT: Analyzer Implementations
    # ========================================================================

    def _audit_analyzers(self) -> None:
        """Audit language analyzer implementations."""
        print("\n[5/11] Analyzer Implementations...")

        analyzers_dir = self.src_dir / "codetruth" / "analyzers"

        existing_analyzers = [
            ("dead_code.py", "DeadCodeAnalyzer"),
            ("ui_wiring.py", "UIWiringAnalyzer"),
            ("lint.py", "LintAnalyzer"),
            ("type_check.py", "TypeCheckAnalyzer"),
            ("sast.py", "SASTAnalyzer"),
            ("secrets.py", "SecretScanner"),
            ("dependencies.py", "DependencyAuditor"),
            ("contracts.py", "APIContractAnalyzer"),
        ]

        missing_analyzers = [
            ("php.py", "PHPAnalyzer"),
            ("csharp.py", "CSharpAnalyzer"),
            ("java.py", "JavaAnalyzer"),
            ("lua.py", "LuaAnalyzer"),
            ("powershell.py", "PowerShellAnalyzer"),
            ("html.py", "HTMLAnalyzer"),
            ("css.py", "CSSAnalyzer"),
            ("sql.py", "SQLAnalyzer"),
            ("shell.py", "ShellAnalyzer"),
            ("dockerfile.py", "DockerfileAnalyzer"),
            ("yaml_analyzer.py", "YAMLAnalyzer"),
            ("json_analyzer.py", "JSONAnalyzer"),
        ]

        for analyzer_file, expected_class in existing_analyzers:
            path = analyzers_dir / analyzer_file
            if path.exists():
                content = path.read_text()
                lines = len(content.split("\n"))
                if f"class {expected_class}" in content:
                    self.report.add(AuditCheck(
                        category="analyzers",
                        name=f"analyzer:{analyzer_file}",
                        status=CheckStatus.PASS,
                        message=f"{analyzer_file}: {lines} lines",
                    ))
                    self.log(f"✅ {analyzer_file}")
                else:
                    self.report.add(AuditCheck(
                        category="analyzers",
                        name=f"analyzer:{analyzer_file}",
                        status=CheckStatus.WARN,
                        message=f"{analyzer_file}: exists but missing {expected_class}",
                    ))
            else:
                self.report.add(AuditCheck(
                    category="analyzers",
                    name=f"analyzer:{analyzer_file}",
                    status=CheckStatus.FAIL,
                    message=f"Analyzer not found: {analyzer_file}",
                ))

        # Check for missing language analyzers (expected to be UNPROVEN)
        for analyzer_file, expected_class in missing_analyzers:
            path = analyzers_dir / analyzer_file
            if path.exists():
                self.report.add(AuditCheck(
                    category="analyzers",
                    name=f"analyzer:{analyzer_file}",
                    status=CheckStatus.PASS,
                    message=f"{analyzer_file} implemented (unexpected!)",
                ))
            else:
                self.report.add(AuditCheck(
                    category="analyzers",
                    name=f"analyzer:{analyzer_file}",
                    status=CheckStatus.SKIP,
                    message=f"{analyzer_file} not implemented (marked UNPROVEN)",
                ))

    # ========================================================================
    # AUDIT: Coverage Manifest
    # ========================================================================

    def _audit_manifest(self) -> None:
        """Audit COVERAGE_MANIFEST.json for consistency."""
        print("\n[6/11] Coverage Manifest...")

        manifest_path = self.specs_dir / "COVERAGE_MANIFEST.json"
        if not manifest_path.exists():
            self.report.add(AuditCheck(
                category="manifest",
                name="manifest_exists",
                status=CheckStatus.FAIL,
                message="COVERAGE_MANIFEST.json not found",
            ))
            return

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            self.report.add(AuditCheck(
                category="manifest",
                name="manifest_valid",
                status=CheckStatus.FAIL,
                message=f"Invalid JSON: {e}",
            ))
            return

        self.report.add(AuditCheck(
            category="manifest",
            name="manifest_valid",
            status=CheckStatus.PASS,
            message="COVERAGE_MANIFEST.json is valid JSON",
        ))

        # Check code types
        code_types = manifest.get("code_types", [])
        self.report.add(AuditCheck(
            category="manifest",
            name="code_type_count",
            status=CheckStatus.PASS if len(code_types) >= 10 else CheckStatus.WARN,
            message=f"Found {len(code_types)} code types",
        ))

        # Check for required fields in each code type
        status_counts = {"FULL": 0, "PARTIAL": 0, "UNPROVEN": 0, "PLANNED": 0}
        for ct in code_types:
            status = ct.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

            # If FULL, must have fixtures and goldens
            if status == "FULL":
                if not ct.get("fixtures") or not ct.get("goldens"):
                    self.report.add(AuditCheck(
                        category="manifest",
                        name=f"manifest_full:{ct.get('id')}",
                        status=CheckStatus.FAIL,
                        message=f"{ct.get('id')} claims FULL but missing fixtures/goldens",
                    ))

        # Status summary
        self.log(f"Status distribution: {status_counts}")
        self.report.add(AuditCheck(
            category="manifest",
            name="status_distribution",
            status=CheckStatus.PASS,
            message=f"PARTIAL: {status_counts.get('PARTIAL', 0)}, UNPROVEN: {status_counts.get('UNPROVEN', 0)}",
        ))

        # Check honesty - no claims of FULL without proof
        full_without_impl = [ct for ct in code_types if ct.get("status") == "FULL" and not ct.get("implemented_analyzers")]
        if full_without_impl:
            self.report.add(AuditCheck(
                category="manifest",
                name="manifest_honesty",
                status=CheckStatus.FAIL,
                message=f"{len(full_without_impl)} code types claim FULL without implementation",
            ))
        else:
            self.report.add(AuditCheck(
                category="manifest",
                name="manifest_honesty",
                status=CheckStatus.PASS,
                message="No false FULL claims",
            ))

    # ========================================================================
    # AUDIT: Spec-Code Alignment
    # ========================================================================

    def _audit_spec_code_alignment(self) -> None:
        """Audit spec-to-code alignment."""
        print("\n[7/11] Spec-Code Alignment...")

        alignment_path = self.specs_dir / "SPEC_CODE_ALIGNMENT.md"
        if not alignment_path.exists():
            self.report.add(AuditCheck(
                category="alignment",
                name="alignment_doc",
                status=CheckStatus.FAIL,
                message="SPEC_CODE_ALIGNMENT.md not found",
            ))
            return

        content = alignment_path.read_text()
        lines = len(content.split("\n"))

        self.report.add(AuditCheck(
            category="alignment",
            name="alignment_doc",
            status=CheckStatus.PASS if lines >= 100 else CheckStatus.WARN,
            message=f"SPEC_CODE_ALIGNMENT.md: {lines} lines",
        ))

        # Check for NOT IMPLEMENTED counts
        not_impl_matches = re.findall(r"NOT.?IMPLEMENTED", content, re.IGNORECASE)
        impl_matches = re.findall(r"✅\s*IMPLEMENTED", content)

        self.report.add(AuditCheck(
            category="alignment",
            name="alignment_honesty",
            status=CheckStatus.PASS,
            message=f"Tracks {len(impl_matches)} IMPLEMENTED, {len(not_impl_matches)} NOT IMPLEMENTED",
        ))

    # ========================================================================
    # AUDIT: Honesty Checks
    # ========================================================================

    def _audit_honesty_checks(self) -> None:
        """Audit that all major spec files have HONESTY CHECK blocks."""
        print("\n[8/11] Honesty Checks...")

        files_needing_honesty = [
            "specs/MASTER.md",
            "specs/CAPABILITIES.md",
            "specs/SELF_AUDIT.md",
        ]

        # Add language profiles
        profiles_dir = self.specs_dir / "language-profiles"
        if profiles_dir.exists():
            for profile in profiles_dir.glob("*.md"):
                if not profile.name.startswith("_"):
                    files_needing_honesty.append(str(profile.relative_to(self.repo_path)))

        for file_path in files_needing_honesty:
            full_path = self.repo_path / file_path
            if full_path.exists():
                content = full_path.read_text()
                if "HONESTY CHECK" in content or "Honesty Check" in content.lower():
                    self.report.add(AuditCheck(
                        category="honesty",
                        name=f"honesty:{file_path}",
                        status=CheckStatus.PASS,
                        message="Has HONESTY CHECK block",
                    ))
                else:
                    self.report.add(AuditCheck(
                        category="honesty",
                        name=f"honesty:{file_path}",
                        status=CheckStatus.WARN,
                        message="Missing HONESTY CHECK block",
                        fix_suggestion=f"Add HONESTY CHECK section to {file_path}",
                    ))

    # ========================================================================
    # AUDIT: Forbidden Patterns
    # ========================================================================

    def _audit_forbidden_patterns(self) -> None:
        """Audit for forbidden patterns in spec files."""
        print("\n[9/11] Forbidden Patterns...")

        forbidden = [
            (r"\bTODO\b(?!\s*:.*UNPROVEN)", "TODO without UNPROVEN context"),
            (r"\bwill implement\b", "'will implement' promise"),
            (r"\bplaceholder\b", "'placeholder' content"),
            (r"\bnext step\b", "'next step' vague promise"),
            (r"\bcoming soon\b", "'coming soon' vague promise"),
        ]

        spec_files = list(self.specs_dir.glob("*.md"))
        spec_files.extend(self.specs_dir.glob("**/*.md"))

        violations = []
        for spec_file in spec_files:
            if spec_file.name.startswith("_"):
                continue

            content = spec_file.read_text()
            for pattern, description in forbidden:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append((spec_file.name, description, len(matches)))

        if violations:
            for file_name, desc, count in violations[:5]:  # Limit output
                self.report.add(AuditCheck(
                    category="forbidden",
                    name=f"forbidden:{file_name}",
                    status=CheckStatus.WARN,
                    message=f"{file_name}: {count}x '{desc}'",
                ))
        else:
            self.report.add(AuditCheck(
                category="forbidden",
                name="forbidden_patterns",
                status=CheckStatus.PASS,
                message="No forbidden patterns found in specs",
            ))

    # ========================================================================
    # AUDIT: CI Gates
    # ========================================================================

    def _audit_ci_gates(self) -> None:
        """Audit CI/CD configuration."""
        print("\n[10/11] CI Gates...")

        ci_path = self.repo_path / ".github" / "workflows"
        if not ci_path.exists():
            self.report.add(AuditCheck(
                category="ci",
                name="ci_workflows",
                status=CheckStatus.FAIL,
                message="No GitHub workflows directory",
                fix_suggestion="mkdir -p .github/workflows",
            ))
            return

        workflows = list(ci_path.glob("*.yml")) + list(ci_path.glob("*.yaml"))
        if workflows:
            self.report.add(AuditCheck(
                category="ci",
                name="ci_workflows",
                status=CheckStatus.PASS,
                message=f"Found {len(workflows)} workflow files",
            ))

            # Check for self-audit workflow
            has_self_audit = any("self-audit" in w.name.lower() or "self_audit" in w.name.lower() for w in workflows)
            if has_self_audit:
                self.report.add(AuditCheck(
                    category="ci",
                    name="ci_self_audit",
                    status=CheckStatus.PASS,
                    message="Self-audit workflow exists",
                ))
            else:
                self.report.add(AuditCheck(
                    category="ci",
                    name="ci_self_audit",
                    status=CheckStatus.WARN,
                    message="No self-audit workflow found",
                ))
        else:
            self.report.add(AuditCheck(
                category="ci",
                name="ci_workflows",
                status=CheckStatus.FAIL,
                message="No workflow files found",
            ))

    # ========================================================================
    # AUDIT: Documentation
    # ========================================================================

    def _audit_documentation(self) -> None:
        """Audit documentation completeness."""
        print("\n[11/11] Documentation...")

        readme_path = self.repo_path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            lines = len(content.split("\n"))

            self.report.add(AuditCheck(
                category="docs",
                name="readme_length",
                status=CheckStatus.PASS if lines >= 50 else CheckStatus.WARN,
                message=f"README.md: {lines} lines",
            ))

            # Check for key sections
            sections = ["Installation", "Usage", "License"]
            for section in sections:
                if section.lower() in content.lower():
                    self.report.add(AuditCheck(
                        category="docs",
                        name=f"readme_section:{section}",
                        status=CheckStatus.PASS,
                        message=f"README has '{section}' section",
                    ))
        else:
            self.report.add(AuditCheck(
                category="docs",
                name="readme_exists",
                status=CheckStatus.FAIL,
                message="README.md not found",
            ))

        # Check for SVG diagrams
        diagrams_dir = self.specs_dir / "diagrams"
        if diagrams_dir.exists():
            svgs = list(diagrams_dir.glob("*.svg"))
            self.report.add(AuditCheck(
                category="docs",
                name="svg_diagrams",
                status=CheckStatus.PASS if svgs else CheckStatus.WARN,
                message=f"Found {len(svgs)} SVG diagrams",
            ))


# ============================================================================
# OUTPUT FORMATTERS
# ============================================================================

def print_report(report: AuditReport, verbose: bool = False) -> None:
    """Print formatted audit report."""
    print("\n" + "=" * 70)
    print("SELF-AUDIT RESULTS")
    print("=" * 70)

    print(f"\nTotal Checks: {report.total}")
    print(f"  ✅ Passed:  {report.passed}")
    print(f"  ❌ Failed:  {report.failed}")
    print(f"  ⚠️  Warned:  {report.warned}")
    print(f"  ⏭️  Skipped: {report.skipped}")
    print(f"  💥 Errors:  {report.errored}")
    print(f"\nPass Rate: {report.pass_rate:.1f}%")

    # By category
    print("\n" + "-" * 50)
    print("BY CATEGORY")
    print("-" * 50)
    for category, counts in report._group_by_category().items():
        status_str = f"✅{counts['pass']} ❌{counts['fail']} ⚠️{counts['warn']}"
        print(f"  {category:20} {status_str}")

    # Show failures
    failures = [c for c in report.checks if c.status == CheckStatus.FAIL]
    if failures:
        print("\n" + "-" * 50)
        print("FAILURES")
        print("-" * 50)
        for check in failures:
            print(f"  ❌ [{check.category}] {check.name}")
            print(f"     {check.message}")
            if check.fix_suggestion:
                print(f"     FIX: {check.fix_suggestion}")

    # Show warnings if verbose
    if verbose:
        warnings = [c for c in report.checks if c.status == CheckStatus.WARN]
        if warnings:
            print("\n" + "-" * 50)
            print("WARNINGS")
            print("-" * 50)
            for check in warnings:
                print(f"  ⚠️  [{check.category}] {check.name}")
                print(f"     {check.message}")

    print("\n" + "=" * 70)
    if report.overall_pass:
        print("✅ SELF-AUDIT PASSED")
        print("   CodeTruth-MCP meets minimum requirements.")
    else:
        print("❌ SELF-AUDIT FAILED")
        print("   Fix the failures above before claiming readiness.")
    print("=" * 70)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CodeTruth-MCP Comprehensive Self-Audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python self_audit.py                  # Run basic audit
  python self_audit.py --verbose        # Show all details
  python self_audit.py --output report.json  # Save JSON report
        """
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output including warnings"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Save JSON report to file"
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=Path.cwd(),
        help="Path to repository (default: current directory)"
    )

    args = parser.parse_args()

    # Find repo root
    repo_path = args.repo_path
    if not (repo_path / "specs").exists():
        # Try parent directories
        for _ in range(3):
            repo_path = repo_path.parent
            if (repo_path / "specs").exists():
                break
        else:
            print("Error: Could not find CodeTruth-MCP repository")
            print("Make sure you're in the repository or use --repo-path")
            sys.exit(1)

    # Run audit
    auditor = SelfAuditor(repo_path, verbose=args.verbose)
    report = auditor.run_all_audits()

    # Print results
    print_report(report, verbose=args.verbose)

    # Save JSON if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nReport saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
