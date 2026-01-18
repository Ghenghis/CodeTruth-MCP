"""
Runtime Truth Correlator

Correlates findings from multiple sources to determine truth.
Resolves contradictions between static and dynamic analysis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class TruthDecision(Enum):
    """Final truth decision for a feature/component."""
    COMPLETE = "complete"           # Feature works as intended
    PARTIAL = "partial"             # Feature partially works
    BROKEN = "broken"               # Feature is broken
    FAKE_COMPLETE = "fake_complete" # Looks complete but doesn't work
    UNKNOWN = "unknown"             # Cannot determine


class FindingSource(Enum):
    """Source of a finding."""
    STATIC_LINT = "static_lint"
    STATIC_TYPECHECK = "static_typecheck"
    STATIC_REACHABILITY = "static_reachability"
    DYNAMIC_TEST = "dynamic_test"
    DYNAMIC_COVERAGE = "dynamic_coverage"
    DYNAMIC_UI_VERIFY = "dynamic_ui_verify"
    DYNAMIC_RUNTIME = "dynamic_runtime"
    HEURISTIC = "heuristic"


class ContradictionType(Enum):
    """Types of contradictions between findings."""
    STATIC_OK_DYNAMIC_FAILS = "static_ok_dynamic_fails"
    TESTS_PASS_COVERAGE_LOW = "tests_pass_coverage_low"
    LINT_CLEAN_NO_OP_UI = "lint_clean_no_op_ui"
    ROUTE_EXISTS_NOT_MOUNTED = "route_exists_not_mounted"
    HANDLER_DEFINED_NOT_BOUND = "handler_defined_not_bound"
    TYPE_SAFE_RUNTIME_ERROR = "type_safe_runtime_error"
    DEPENDENCY_OK_IMPORT_FAILS = "dependency_ok_import_fails"
    CONFIG_VALID_STARTUP_FAILS = "config_valid_startup_fails"
    SCHEMA_MATCH_PAYLOAD_MISMATCH = "schema_match_payload_mismatch"
    CODE_REACHABLE_NEVER_EXECUTED = "code_reachable_never_executed"


@dataclass
class Finding:
    """A finding from any analysis source."""
    finding_id: str
    source: FindingSource
    feature_id: str
    severity: str
    message: str
    location: Dict[str, Any]
    confidence: float = 1.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "source": self.source.value,
            "feature_id": self.feature_id,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Contradiction:
    """A contradiction between two findings."""
    contradiction_id: str
    contradiction_type: ContradictionType
    finding_a: Finding
    finding_b: Finding
    explanation: str
    resolution: TruthDecision
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "type": self.contradiction_type.value,
            "finding_a": self.finding_a.to_dict(),
            "finding_b": self.finding_b.to_dict(),
            "explanation": self.explanation,
            "resolution": self.resolution.value,
            "confidence": self.confidence,
        }


@dataclass
class FeatureTruth:
    """Truth determination for a single feature."""
    feature_id: str
    decision: TruthDecision
    confidence: float
    supporting_findings: List[Finding] = field(default_factory=list)
    contradicting_findings: List[Finding] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "decision": self.decision.value,
            "confidence": self.confidence,
            "supporting_findings": [f.to_dict() for f in self.supporting_findings],
            "contradicting_findings": [f.to_dict() for f in self.contradicting_findings],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "explanation": self.explanation,
        }


@dataclass
class CorrelationReport:
    """Complete correlation report."""
    repo_path: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    total_features: int = 0
    feature_truths: List[FeatureTruth] = field(default_factory=list)
    all_contradictions: List[Contradiction] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": "1.0.0",
            "repo_path": self.repo_path,
            "created_at": self.created_at.isoformat(),
            "statistics": {
                "total_features": self.total_features,
                "by_decision": self.summary,
                "total_contradictions": len(self.all_contradictions),
            },
            "feature_truths": [ft.to_dict() for ft in self.feature_truths],
            "contradictions": [c.to_dict() for c in self.all_contradictions],
        }

    def export_json(self, output_path: Path) -> None:
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class RuntimeCorrelator:
    """
    Correlates findings from multiple sources to determine truth.

    Evidence Precedence:
    1. DYNAMIC_PROOF > STATIC_PROOF > HEURISTIC
    2. Runtime evidence trumps static analysis
    3. Contradictions must be resolved explicitly
    """

    # Rules for contradiction detection
    CONTRADICTION_RULES = [
        {
            "name": "static_ok_dynamic_fails",
            "source_a": [FindingSource.STATIC_LINT, FindingSource.STATIC_TYPECHECK],
            "source_b": [FindingSource.DYNAMIC_TEST, FindingSource.DYNAMIC_RUNTIME],
            "type": ContradictionType.STATIC_OK_DYNAMIC_FAILS,
            "resolution": TruthDecision.BROKEN,
            "explanation": "Static analysis passed but dynamic testing failed. Runtime behavior takes precedence.",
        },
        {
            "name": "lint_clean_noop",
            "source_a": [FindingSource.STATIC_LINT],
            "source_b": [FindingSource.DYNAMIC_UI_VERIFY],
            "type": ContradictionType.LINT_CLEAN_NO_OP_UI,
            "resolution": TruthDecision.FAKE_COMPLETE,
            "explanation": "Code passes lint but UI verification shows no-op elements. Feature is fake-complete.",
        },
        {
            "name": "tests_pass_coverage_low",
            "source_a": [FindingSource.DYNAMIC_TEST],
            "source_b": [FindingSource.DYNAMIC_COVERAGE],
            "type": ContradictionType.TESTS_PASS_COVERAGE_LOW,
            "resolution": TruthDecision.PARTIAL,
            "explanation": "Tests pass but coverage is low. Feature may work in tested scenarios only.",
        },
        {
            "name": "reachable_never_executed",
            "source_a": [FindingSource.STATIC_REACHABILITY],
            "source_b": [FindingSource.DYNAMIC_COVERAGE],
            "type": ContradictionType.CODE_REACHABLE_NEVER_EXECUTED,
            "resolution": TruthDecision.UNKNOWN,
            "explanation": "Code is statically reachable but never executed in tests. Cannot determine if it works.",
        },
    ]

    # Evidence weights for confidence calculation
    EVIDENCE_WEIGHTS = {
        FindingSource.DYNAMIC_RUNTIME: 1.0,
        FindingSource.DYNAMIC_TEST: 0.9,
        FindingSource.DYNAMIC_COVERAGE: 0.8,
        FindingSource.DYNAMIC_UI_VERIFY: 0.85,
        FindingSource.STATIC_TYPECHECK: 0.7,
        FindingSource.STATIC_REACHABILITY: 0.7,
        FindingSource.STATIC_LINT: 0.5,
        FindingSource.HEURISTIC: 0.3,
    }

    def __init__(self):
        self._contradiction_counter = 0

    def _generate_contradiction_id(self) -> str:
        self._contradiction_counter += 1
        return f"contra_{self._contradiction_counter:06d}"

    def correlate(self, findings: List[Finding]) -> CorrelationReport:
        """
        Correlate all findings and produce truth decisions.
        """
        report = CorrelationReport(repo_path="")

        # Group findings by feature
        features: Dict[str, List[Finding]] = {}
        for finding in findings:
            if finding.feature_id not in features:
                features[finding.feature_id] = []
            features[finding.feature_id].append(finding)

        report.total_features = len(features)

        # Process each feature
        for feature_id, feature_findings in features.items():
            truth = self._determine_truth(feature_id, feature_findings)
            report.feature_truths.append(truth)
            report.all_contradictions.extend(truth.contradictions)

        # Summary
        report.summary = self._compute_summary(report.feature_truths)

        return report

    def _determine_truth(
        self,
        feature_id: str,
        findings: List[Finding]
    ) -> FeatureTruth:
        """
        Determine truth for a single feature.
        """
        # Detect contradictions
        contradictions = self._detect_contradictions(findings)

        # Separate positive and negative findings
        positive = [f for f in findings if f.severity in {"info", "pass", "ok"}]
        negative = [f for f in findings if f.severity in {"error", "warning", "critical"}]

        # Determine decision
        decision, confidence, explanation = self._make_decision(
            positive, negative, contradictions
        )

        return FeatureTruth(
            feature_id=feature_id,
            decision=decision,
            confidence=confidence,
            supporting_findings=positive,
            contradicting_findings=negative,
            contradictions=contradictions,
            explanation=explanation,
        )

    def _detect_contradictions(self, findings: List[Finding]) -> List[Contradiction]:
        """
        Detect contradictions between findings.
        """
        contradictions: List[Contradiction] = []

        for i, finding_a in enumerate(findings):
            for finding_b in findings[i + 1:]:
                contradiction = self._check_contradiction(finding_a, finding_b)
                if contradiction:
                    contradictions.append(contradiction)

        return contradictions

    def _check_contradiction(
        self,
        finding_a: Finding,
        finding_b: Finding
    ) -> Optional[Contradiction]:
        """
        Check if two findings contradict each other.
        """
        # Simple contradiction: one says OK, other says ERROR
        if finding_a.feature_id != finding_b.feature_id:
            return None

        a_positive = finding_a.severity in {"info", "pass", "ok"}
        b_positive = finding_b.severity in {"info", "pass", "ok"}

        if a_positive == b_positive:
            return None  # Both agree

        # Determine contradiction type
        for rule in self.CONTRADICTION_RULES:
            if (
                finding_a.source in rule["source_a"] and
                finding_b.source in rule["source_b"]
            ) or (
                finding_a.source in rule["source_b"] and
                finding_b.source in rule["source_a"]
            ):
                return Contradiction(
                    contradiction_id=self._generate_contradiction_id(),
                    contradiction_type=rule["type"],
                    finding_a=finding_a,
                    finding_b=finding_b,
                    explanation=rule["explanation"],
                    resolution=rule["resolution"],
                    confidence=0.85,
                )

        # Generic contradiction
        return Contradiction(
            contradiction_id=self._generate_contradiction_id(),
            contradiction_type=ContradictionType.STATIC_OK_DYNAMIC_FAILS,
            finding_a=finding_a,
            finding_b=finding_b,
            explanation=f"Contradiction between {finding_a.source.value} and {finding_b.source.value}",
            resolution=TruthDecision.UNKNOWN,
            confidence=0.5,
        )

    def _make_decision(
        self,
        positive: List[Finding],
        negative: List[Finding],
        contradictions: List[Contradiction]
    ) -> tuple[TruthDecision, float, str]:
        """
        Make a truth decision based on findings and contradictions.
        """
        # If there are contradictions, use the resolution from highest-priority one
        if contradictions:
            # Sort by confidence
            top_contradiction = max(contradictions, key=lambda c: c.confidence)
            return (
                top_contradiction.resolution,
                top_contradiction.confidence,
                top_contradiction.explanation,
            )

        # No contradictions - weigh evidence
        if not positive and not negative:
            return TruthDecision.UNKNOWN, 0.0, "No evidence available"

        if not negative:
            # All positive
            confidence = self._compute_confidence(positive)
            return TruthDecision.COMPLETE, confidence, "All evidence is positive"

        if not positive:
            # All negative
            confidence = self._compute_confidence(negative)
            return TruthDecision.BROKEN, confidence, "All evidence indicates problems"

        # Mixed - compare weights
        pos_weight = sum(self.EVIDENCE_WEIGHTS[f.source] for f in positive)
        neg_weight = sum(self.EVIDENCE_WEIGHTS[f.source] for f in negative)

        if neg_weight > pos_weight:
            return TruthDecision.BROKEN, neg_weight / (pos_weight + neg_weight), "Negative evidence outweighs positive"
        elif pos_weight > neg_weight * 2:
            return TruthDecision.COMPLETE, pos_weight / (pos_weight + neg_weight), "Positive evidence outweighs negative"
        else:
            return TruthDecision.PARTIAL, 0.5, "Mixed evidence - feature may be partially working"

    def _compute_confidence(self, findings: List[Finding]) -> float:
        """
        Compute confidence score from findings.
        """
        if not findings:
            return 0.0

        total_weight = sum(
            self.EVIDENCE_WEIGHTS[f.source] * f.confidence
            for f in findings
        )
        max_weight = sum(self.EVIDENCE_WEIGHTS[f.source] for f in findings)

        return min(total_weight / max(max_weight, 1), 1.0)

    def _compute_summary(self, truths: List[FeatureTruth]) -> Dict[str, int]:
        """
        Compute summary statistics.
        """
        summary: Dict[str, int] = {
            "complete": 0,
            "partial": 0,
            "broken": 0,
            "fake_complete": 0,
            "unknown": 0,
        }

        for truth in truths:
            key = truth.decision.value
            summary[key] = summary.get(key, 0) + 1

        return summary


def correlate_findings(findings: List[Finding]) -> CorrelationReport:
    """
    Convenience function to correlate findings.
    """
    correlator = RuntimeCorrelator()
    return correlator.correlate(findings)
