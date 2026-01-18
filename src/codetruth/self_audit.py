"""
CodeTruth Self-Audit Command

Runs all fixtures and compares results to golden outputs.
This is the CI gate that prevents fake completeness.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .engines.reachability.graph import ReachabilityGraph
from .engines.reachability.proofs import analyze_reachability
from .engines.reachability.builders.typescript import build_typescript_graph
from .engines.ui_verifier.verifier import verify_ui


@dataclass
class FixtureResult:
    """Result of running a single fixture."""
    fixture_id: str
    fixture_path: str
    golden_path: str
    passed: bool
    expected_findings: int
    actual_findings: int
    missing_findings: List[Dict[str, Any]] = field(default_factory=list)
    extra_findings: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "fixture_path": self.fixture_path,
            "golden_path": self.golden_path,
            "passed": self.passed,
            "expected_findings": self.expected_findings,
            "actual_findings": self.actual_findings,
            "missing_findings": self.missing_findings,
            "extra_findings": self.extra_findings,
            "error": self.error_message,
        }


@dataclass
class SelfAuditReport:
    """Complete self-audit report."""
    created_at: datetime = field(default_factory=datetime.utcnow)
    total_fixtures: int = 0
    passed: int = 0
    failed: int = 0
    results: List[FixtureResult] = field(default_factory=list)
    overall_pass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": "1.0.0",
            "created_at": self.created_at.isoformat(),
            "statistics": {
                "total_fixtures": self.total_fixtures,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": round((self.passed / max(self.total_fixtures, 1)) * 100, 2),
            },
            "overall_pass": self.overall_pass,
            "results": [r.to_dict() for r in self.results],
        }

    def export_json(self, output_path: Path) -> None:
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class SelfAuditor:
    """
    Runs self-audit by executing fixtures and comparing to goldens.
    """

    def __init__(self, specs_dir: Path):
        self.specs_dir = specs_dir
        self.fixtures_dir = specs_dir / "fixtures"
        self.goldens_dir = specs_dir / "goldens"

    def run_all_fixtures(self) -> SelfAuditReport:
        """
        Run all fixtures and compare to golden outputs.
        """
        report = SelfAuditReport()

        # Find all fixture directories
        if not self.fixtures_dir.exists():
            print(f"Fixtures directory not found: {self.fixtures_dir}")
            return report

        # Process each language directory
        for lang_dir in self.fixtures_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            # Process each fixture in this language
            for fixture_dir in lang_dir.iterdir():
                if not fixture_dir.is_dir():
                    continue

                result = self._run_fixture(lang_dir.name, fixture_dir.name, fixture_dir)
                report.results.append(result)
                report.total_fixtures += 1

                if result.passed:
                    report.passed += 1
                else:
                    report.failed += 1

        report.overall_pass = report.failed == 0
        return report

    def _run_fixture(
        self,
        language: str,
        fixture_name: str,
        fixture_dir: Path
    ) -> FixtureResult:
        """
        Run a single fixture and compare to its golden.
        """
        fixture_id = f"{language}/{fixture_name}"
        golden_path = self.goldens_dir / f"{language}-{fixture_name}.json"

        # Check if golden exists
        if not golden_path.exists():
            return FixtureResult(
                fixture_id=fixture_id,
                fixture_path=str(fixture_dir),
                golden_path=str(golden_path),
                passed=False,
                expected_findings=0,
                actual_findings=0,
                error_message=f"Golden file not found: {golden_path}",
            )

        # Load golden
        try:
            with open(golden_path) as f:
                golden = json.load(f)
        except Exception as e:
            return FixtureResult(
                fixture_id=fixture_id,
                fixture_path=str(fixture_dir),
                golden_path=str(golden_path),
                passed=False,
                expected_findings=0,
                actual_findings=0,
                error_message=f"Failed to load golden: {e}",
            )

        # Run analysis based on language
        try:
            actual_findings = self._analyze_fixture(language, fixture_dir)
        except Exception as e:
            return FixtureResult(
                fixture_id=fixture_id,
                fixture_path=str(fixture_dir),
                golden_path=str(golden_path),
                passed=False,
                expected_findings=len(golden.get("expected_findings", [])),
                actual_findings=0,
                error_message=f"Analysis failed: {e}",
            )

        # Compare findings
        expected = golden.get("expected_findings", [])
        missing, extra = self._compare_findings(expected, actual_findings)

        passed = len(missing) == 0 and len(extra) == 0

        return FixtureResult(
            fixture_id=fixture_id,
            fixture_path=str(fixture_dir),
            golden_path=str(golden_path),
            passed=passed,
            expected_findings=len(expected),
            actual_findings=len(actual_findings),
            missing_findings=missing,
            extra_findings=extra,
        )

    def _analyze_fixture(self, language: str, fixture_dir: Path) -> List[Dict[str, Any]]:
        """
        Run appropriate analysis for a fixture.
        """
        findings: List[Dict[str, Any]] = []

        if language in {"typescript-react", "javascript"}:
            # Run TypeScript/React analysis
            graph = build_typescript_graph(fixture_dir)
            reach_report = analyze_reachability(graph)

            # Convert proofs to findings
            for proof in reach_report.proofs:
                findings.append({
                    "type": "unreachable_code" if proof.proof_type.value == "unreachable" else "reachable",
                    "severity": "HIGH" if proof.proof_type.value == "unreachable" else "INFO",
                    "location": {
                        "file": proof.target_node_id,
                    },
                    "message": f"Node {proof.target_node_id} is {proof.proof_type.value}",
                })

            # Run UI verification
            ui_report = verify_ui(fixture_dir)
            for finding in ui_report.findings:
                findings.append({
                    "type": finding.reason.value,
                    "severity": finding.severity.upper(),
                    "location": finding.element.location,
                    "message": finding.explanation,
                })

        elif language == "python":
            # Run Python analysis (simplified for now)
            for py_file in fixture_dir.glob("**/*.py"):
                content = py_file.read_text(errors="ignore")
                lines = content.split("\n")

                # Check for unreachable code after return
                in_function = False
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("def ") or stripped.startswith("async def "):
                        in_function = True
                    elif in_function and stripped.startswith("return"):
                        # Check next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith("#"):
                                findings.append({
                                    "type": "unreachable_code",
                                    "severity": "WARNING",
                                    "location": {
                                        "file": str(py_file),
                                        "line": i + 2,
                                    },
                                    "message": "Unreachable code after return statement",
                                })

                # Check for TODO/FIXME markers
                for i, line in enumerate(lines):
                    for marker in ["TODO", "FIXME", "HACK", "XXX"]:
                        if marker in line:
                            findings.append({
                                "type": "code_marker",
                                "severity": "NOTE" if marker == "TODO" else "WARNING",
                                "location": {
                                    "file": str(py_file),
                                    "line": i + 1,
                                },
                                "message": f"{marker} found",
                            })
                            break

        elif language == "php":
            # Run PHP analysis (simplified)
            for php_file in fixture_dir.glob("**/*.php"):
                content = php_file.read_text(errors="ignore")

                # Check for AJAX handlers that return success without effect
                if "echo json_encode" in content and ("'success' => true" in content or '"success" => true' in content):
                    # Check if there's actual DB or file operations
                    has_effect = any(kw in content for kw in ["mysql_query", "mysqli_query", "$pdo->", "file_put_contents", "fwrite"])
                    if not has_effect:
                        findings.append({
                            "type": "fake_success",
                            "severity": "CRITICAL",
                            "location": {"file": str(php_file)},
                            "message": "AJAX handler returns success without actual effect",
                        })

                # Check for cron-like patterns
                if "php_sapi_name()" in content or "cron" in str(php_file).lower():
                    findings.append({
                        "type": "cron_candidate",
                        "severity": "INFO",
                        "location": {"file": str(php_file)},
                        "message": "File appears to be cron script - verify crontab entry exists",
                    })

        return findings

    def _compare_findings(
        self,
        expected: List[Dict[str, Any]],
        actual: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Compare expected and actual findings.

        Returns (missing, extra) findings.
        """
        missing: List[Dict[str, Any]] = []
        extra: List[Dict[str, Any]] = []

        # Simple comparison by type and severity
        expected_types = {(f.get("type"), f.get("severity")) for f in expected}
        actual_types = {(f.get("type"), f.get("severity")) for f in actual}

        for f in expected:
            key = (f.get("type"), f.get("severity"))
            if key not in actual_types:
                missing.append(f)

        for f in actual:
            key = (f.get("type"), f.get("severity"))
            if key not in expected_types:
                extra.append(f)

        return missing, extra


def run_self_audit(specs_dir: Optional[Path] = None) -> SelfAuditReport:
    """
    Run self-audit and return report.
    """
    if specs_dir is None:
        # Find specs directory relative to this file
        specs_dir = Path(__file__).parent.parent.parent / "specs"

    auditor = SelfAuditor(specs_dir)
    return auditor.run_all_fixtures()


def main():
    """
    CLI entry point for self-audit.
    """
    import argparse

    parser = argparse.ArgumentParser(description="CodeTruth Self-Audit")
    parser.add_argument(
        "--specs-dir",
        type=Path,
        help="Path to specs directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON report path",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    report = run_self_audit(args.specs_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("CODETRUTH SELF-AUDIT REPORT")
    print("=" * 60)
    print(f"Total Fixtures: {report.total_fixtures}")
    print(f"Passed: {report.passed}")
    print(f"Failed: {report.failed}")
    print(f"Pass Rate: {(report.passed / max(report.total_fixtures, 1)) * 100:.1f}%")
    print("=" * 60)

    if args.verbose:
        for result in report.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{status} {result.fixture_id}")
            if not result.passed:
                if result.error_message:
                    print(f"  Error: {result.error_message}")
                if result.missing_findings:
                    print(f"  Missing findings: {len(result.missing_findings)}")
                if result.extra_findings:
                    print(f"  Extra findings: {len(result.extra_findings)}")

    if args.output:
        report.export_json(args.output)
        print(f"\nReport saved to: {args.output}")

    print("\n" + "=" * 60)
    if report.overall_pass:
        print("✅ SELF-AUDIT PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SELF-AUDIT FAILED")
        print("CodeTruth cannot claim readiness until all fixtures pass.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
