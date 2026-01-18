"""Tests for the Evidence Vault."""

import pytest
import tempfile
from pathlib import Path

from codetruth.core.evidence import (
    Evidence,
    EvidenceType,
    Severity,
    EvidenceLocation,
    EvidenceVault,
)


@pytest.fixture
async def vault():
    """Create a temporary evidence vault."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        vault = EvidenceVault(db_path)
        await vault.initialize()
        yield vault
        await vault.close()


@pytest.mark.asyncio
async def test_store_and_retrieve_evidence(vault):
    """Test storing and retrieving evidence."""
    evidence = Evidence(
        evidence_type=EvidenceType.LINT_ERROR,
        severity=Severity.WARNING,
        message="Test lint error",
        location=EvidenceLocation(
            file_path="test.py",
            start_line=10,
        ),
        tool_name="test_tool",
        repo_path="/test/repo",
    )

    evidence_id = await vault.store_evidence(evidence)
    assert evidence_id is not None

    retrieved = await vault.get_evidence(evidence_id)
    assert retrieved is not None
    assert retrieved.message == "Test lint error"
    assert retrieved.severity == Severity.WARNING


@pytest.mark.asyncio
async def test_search_evidence(vault):
    """Test searching for evidence."""
    # Store multiple evidence items
    for i in range(5):
        evidence = Evidence(
            evidence_type=EvidenceType.LINT_ERROR,
            severity=Severity.WARNING,
            message=f"Test error {i}",
            tool_name="test_tool",
            repo_path="/test/repo",
        )
        await vault.store_evidence(evidence)

    # Search
    results = await vault.search(repo_path="/test/repo")
    assert len(results) == 5


@pytest.mark.asyncio
async def test_get_summary(vault):
    """Test getting evidence summary."""
    # Store evidence of different types/severities
    await vault.store_evidence(Evidence(
        evidence_type=EvidenceType.LINT_ERROR,
        severity=Severity.ERROR,
        message="Error 1",
        tool_name="test",
        repo_path="/test",
    ))
    await vault.store_evidence(Evidence(
        evidence_type=EvidenceType.LINT_ERROR,
        severity=Severity.WARNING,
        message="Warning 1",
        tool_name="test",
        repo_path="/test",
    ))

    summary = await vault.get_summary("/test")
    assert summary["total"] == 2
    assert summary["by_severity"]["error"] == 1
    assert summary["by_severity"]["warning"] == 1
