"""
CodeTruth-MCP: Evidence-Based Code Auditing MCP Server

No claims without proof - every finding backed by verifiable evidence.
"""

__version__ = "0.1.0"
__author__ = "CodeTruth Team"

from codetruth.core.server import CodeTruthServer
from codetruth.core.config import CodeTruthConfig
from codetruth.core.evidence import Evidence, EvidenceType
from codetruth.core.truth_table import TruthTable, FeatureStatus

__all__ = [
    "CodeTruthServer",
    "CodeTruthConfig",
    "Evidence",
    "EvidenceType",
    "TruthTable",
    "FeatureStatus",
]
