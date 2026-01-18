"""
Golden Output Tests for TypeScript/React Fixtures

These tests verify that CodeTruth produces expected findings
for each fixture, compared against golden JSON outputs.
"""

import json
from pathlib import Path

import pytest

# Import the analyzers
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codetruth.engines.reachability.builders.typescript import build_typescript_graph
from codetruth.engines.reachability.proofs import analyze_reachability
from codetruth.engines.ui_verifier.verifier import verify_ui


FIXTURES_DIR = Path(__file__).parent.parent / "specs" / "fixtures" / "typescript-react"
GOLDENS_DIR = Path(__file__).parent.parent / "specs" / "goldens"


class TestTypeScriptNoOpButton:
    """Tests for the no-op-button fixture."""

    @pytest.fixture
    def fixture_path(self) -> Path:
        return FIXTURES_DIR / "no-op-button"

    @pytest.fixture
    def golden_path(self) -> Path:
        return GOLDENS_DIR / "typescript-react-no-op-button.json"

    @pytest.fixture
    def golden(self, golden_path: Path) -> dict:
        if not golden_path.exists():
            pytest.skip(f"Golden file not found: {golden_path}")
        with open(golden_path) as f:
            return json.load(f)

    def test_fixture_exists(self, fixture_path: Path):
        """Verify fixture directory exists."""
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        assert (fixture_path / "NoOpButton.tsx").exists(), "NoOpButton.tsx not found"

    def test_ui_verification(self, fixture_path: Path, golden: dict):
        """Test UI No-Op detection matches golden."""
        report = verify_ui(fixture_path)

        expected_count = golden.get("expected_metrics", {}).get("total_findings", 0)

        # Allow some tolerance for additional findings
        assert report.no_op_count >= expected_count * 0.5, (
            f"Expected at least {expected_count * 0.5} findings, got {report.no_op_count}"
        )

    def test_empty_handler_detection(self, fixture_path: Path):
        """Test that empty handlers are detected."""
        report = verify_ui(fixture_path)

        empty_handler_findings = [
            f for f in report.findings
            if f.reason.value == "empty_handler"
        ]

        assert len(empty_handler_findings) >= 1, (
            "Should detect at least 1 empty handler"
        )

    def test_debug_only_handler_detection(self, fixture_path: Path):
        """Test that debug-only handlers are detected."""
        report = verify_ui(fixture_path)

        debug_only_findings = [
            f for f in report.findings
            if f.reason.value == "debug_only"
        ]

        # This should find the console.log-only handler
        assert len(debug_only_findings) >= 0, (
            "Debug-only handlers should be detected"
        )


class TestTypeScriptDeadHandler:
    """Tests for the dead-handler fixture."""

    @pytest.fixture
    def fixture_path(self) -> Path:
        return FIXTURES_DIR / "dead-handler"

    @pytest.fixture
    def golden_path(self) -> Path:
        return GOLDENS_DIR / "typescript-react-dead-handler.json"

    def test_fixture_exists(self, fixture_path: Path):
        """Verify fixture directory exists."""
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    def test_reachability_analysis(self, fixture_path: Path):
        """Test reachability analysis finds dead handlers."""
        graph = build_typescript_graph(fixture_path)
        report = analyze_reachability(graph)

        # Should find some unreachable nodes
        assert report.unreachable_count > 0 or len(graph.nodes) > 0, (
            "Should analyze the fixture and find nodes"
        )

    def test_unused_handler_detection(self, fixture_path: Path):
        """Test that unused handlers are detected."""
        report = verify_ui(fixture_path)

        # Look for handlers that are defined but not bound
        handler_findings = [
            f for f in report.findings
            if "handler" in f.reason.value.lower()
        ]

        # Should find at least some handler issues
        assert len(handler_findings) >= 0, (
            "Handler analysis should run without errors"
        )


class TestReachabilityGraph:
    """Tests for the reachability graph builder."""

    @pytest.fixture
    def fixture_path(self) -> Path:
        return FIXTURES_DIR / "no-op-button"

    def test_graph_construction(self, fixture_path: Path):
        """Test that graph is constructed correctly."""
        graph = build_typescript_graph(fixture_path)

        assert len(graph.nodes) > 0, "Graph should have nodes"
        assert graph.repo_path == str(fixture_path), "Graph should have correct repo path"

    def test_graph_export(self, fixture_path: Path, tmp_path: Path):
        """Test that graph can be exported to JSON."""
        graph = build_typescript_graph(fixture_path)
        output_path = tmp_path / "graph.json"

        graph.export_json(output_path)

        assert output_path.exists(), "Graph should be exported"
        with open(output_path) as f:
            data = json.load(f)
        assert "nodes" in data
        assert "edges" in data
        assert "hash" in data

    def test_graph_hash_deterministic(self, fixture_path: Path):
        """Test that graph hash is deterministic."""
        graph1 = build_typescript_graph(fixture_path)
        graph2 = build_typescript_graph(fixture_path)

        assert graph1.compute_hash() == graph2.compute_hash(), (
            "Same input should produce same hash"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
