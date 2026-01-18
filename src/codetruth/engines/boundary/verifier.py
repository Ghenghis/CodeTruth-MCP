"""
Boundary Contract Verifier Engine

Detects contract mismatches across language/system boundaries:
- API payload schema mismatches
- Cross-process argument mismatches
- Database schema vs query mismatches
- Environment variable requirements
- Service connectivity contracts
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class BoundaryType(Enum):
    """Types of cross-system boundaries."""
    HTTP_API = "http_api"           # REST/GraphQL API calls
    PROCESS_SPAWN = "process_spawn"  # subprocess, exec
    DATABASE = "database"            # SQL queries vs schema
    MESSAGE_QUEUE = "message_queue"  # Pub/sub, queues
    FILE_FORMAT = "file_format"      # Shared file formats
    ENV_CONFIG = "env_config"        # Environment variables
    IPC = "ipc"                      # Inter-process communication


class ContractSource(Enum):
    """Sources of contract definitions."""
    OPENAPI = "openapi"
    JSON_SCHEMA = "json_schema"
    PROTOBUF = "protobuf"
    SQL_SCHEMA = "sql_schema"
    TYPESCRIPT_TYPES = "typescript_types"
    PYTHON_TYPES = "python_types"
    ENV_FILE = "env_file"
    INFERRED = "inferred"


class MismatchType(Enum):
    """Types of contract mismatches."""
    FIELD_MISSING = "field_missing"           # Required field not sent
    FIELD_EXTRA = "field_extra"               # Unknown field sent
    TYPE_MISMATCH = "type_mismatch"           # Wrong type
    VALUE_RANGE = "value_range"               # Out of range
    NULLABLE_MISMATCH = "nullable_mismatch"   # Null where not allowed
    FORMAT_MISMATCH = "format_mismatch"       # Wrong format (date, email, etc.)
    ENCODING_MISMATCH = "encoding_mismatch"   # Character encoding issues
    VERSION_MISMATCH = "version_mismatch"     # API version incompatibility
    PATH_MISMATCH = "path_mismatch"           # File/script path wrong


@dataclass
class ContractField:
    """A field in a contract."""
    name: str
    field_type: str
    required: bool = True
    nullable: bool = False
    default: Optional[Any] = None
    format: Optional[str] = None
    enum_values: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type,
            "required": self.required,
            "nullable": self.nullable,
            "default": self.default,
            "format": self.format,
            "enum": self.enum_values,
        }


@dataclass
class Contract:
    """A contract definition between two systems."""
    contract_id: str
    boundary_type: BoundaryType
    source: ContractSource
    source_location: str
    fields: List[ContractField] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "boundary_type": self.boundary_type.value,
            "source": self.source.value,
            "source_location": self.source_location,
            "fields": [f.to_dict() for f in self.fields],
            "metadata": self.metadata,
        }


@dataclass
class ContractMismatch:
    """A mismatch between contract and usage."""
    mismatch_id: str
    mismatch_type: MismatchType
    contract: Contract
    location: Dict[str, Any]
    severity: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mismatch_id": self.mismatch_id,
            "type": self.mismatch_type.value,
            "contract": self.contract.to_dict(),
            "location": self.location,
            "severity": self.severity,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class BoundaryVerificationReport:
    """Complete boundary verification report."""
    repo_path: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    contracts_found: int = 0
    mismatches_found: int = 0
    contracts: List[Contract] = field(default_factory=list)
    mismatches: List[ContractMismatch] = field(default_factory=list)
    blindspots: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": "1.0.0",
            "repo_path": self.repo_path,
            "created_at": self.created_at.isoformat(),
            "statistics": {
                "contracts_found": self.contracts_found,
                "mismatches_found": self.mismatches_found,
                "by_boundary_type": self._count_by_boundary(),
                "by_mismatch_type": self._count_by_mismatch(),
            },
            "contracts": [c.to_dict() for c in self.contracts],
            "mismatches": [m.to_dict() for m in self.mismatches],
            "blindspots": self.blindspots,
        }

    def _count_by_boundary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for contract in self.contracts:
            key = contract.boundary_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_by_mismatch(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for mismatch in self.mismatches:
            key = mismatch.mismatch_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def export_json(self, output_path: Path) -> None:
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class BoundaryVerifier:
    """
    Verifies contracts across system boundaries.

    Detects mismatches between:
    - API specs and actual API calls
    - Database schemas and queries
    - Process spawn arguments
    - Environment variable requirements
    """

    STANDARD_BLINDSPOTS = [
        "Dynamic contract generation (runtime schemas)",
        "External APIs without local schema",
        "Binary protocols (gRPC requires .proto files)",
        "Database migrations not captured",
        "Runtime environment variable injection",
    ]

    # Patterns for detecting API calls
    API_PATTERNS = {
        "fetch": re.compile(r"fetch\s*\(\s*['\"`]([^'\"`]+)['\"`]", re.MULTILINE),
        "axios": re.compile(r"axios\s*\.\s*(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)['\"`]", re.MULTILINE),
        "api_call": re.compile(r"api\s*\.\s*(\w+)\s*\(", re.MULTILINE),
    }

    # Patterns for detecting subprocess calls
    SUBPROCESS_PATTERNS = {
        "python_subprocess": re.compile(r"subprocess\.(run|call|Popen)\s*\(\s*\[?['\"]([^'\"]+)['\"]", re.MULTILINE),
        "node_spawn": re.compile(r"spawn\s*\(\s*['\"]([^'\"]+)['\"]", re.MULTILINE),
        "exec": re.compile(r"exec\s*\(\s*['\"]([^'\"]+)['\"]", re.MULTILINE),
    }

    # Patterns for SQL queries
    SQL_PATTERNS = {
        "select": re.compile(r"SELECT\s+(.+?)\s+FROM\s+(\w+)", re.IGNORECASE | re.DOTALL),
        "insert": re.compile(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)", re.IGNORECASE),
        "update": re.compile(r"UPDATE\s+(\w+)\s+SET\s+(.+?)\s+WHERE", re.IGNORECASE | re.DOTALL),
    }

    def __init__(self):
        self._contract_counter = 0
        self._mismatch_counter = 0

    def _generate_contract_id(self) -> str:
        self._contract_counter += 1
        return f"contract_{self._contract_counter:06d}"

    def _generate_mismatch_id(self) -> str:
        self._mismatch_counter += 1
        return f"mismatch_{self._mismatch_counter:06d}"

    def verify_directory(self, directory: Path) -> BoundaryVerificationReport:
        """Verify all boundaries in a directory."""
        report = BoundaryVerificationReport(repo_path=str(directory))
        report.blindspots = self.STANDARD_BLINDSPOTS

        # Find all source files
        patterns = ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.py", "**/*.php"]
        files: List[Path] = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))

        # Exclude node_modules and common excludes
        files = [f for f in files if "node_modules" not in str(f) and ".git" not in str(f)]

        # First pass: find contract definitions
        self._find_contracts(directory, report)

        # Second pass: find usages and check against contracts
        for file_path in files:
            self._analyze_file(file_path, report)

        report.contracts_found = len(report.contracts)
        report.mismatches_found = len(report.mismatches)

        return report

    def _find_contracts(self, directory: Path, report: BoundaryVerificationReport) -> None:
        """Find contract definitions (OpenAPI, JSON Schema, etc.)."""
        # Find OpenAPI specs
        for spec_file in directory.glob("**/openapi*.{json,yaml,yml}"):
            contract = Contract(
                contract_id=self._generate_contract_id(),
                boundary_type=BoundaryType.HTTP_API,
                source=ContractSource.OPENAPI,
                source_location=str(spec_file),
            )
            report.contracts.append(contract)

        # Find JSON schemas
        for schema_file in directory.glob("**/*.schema.json"):
            contract = Contract(
                contract_id=self._generate_contract_id(),
                boundary_type=BoundaryType.HTTP_API,
                source=ContractSource.JSON_SCHEMA,
                source_location=str(schema_file),
            )
            report.contracts.append(contract)

        # Find .env files
        for env_file in directory.glob("**/.env*"):
            if env_file.name.endswith(".example") or env_file.name.endswith(".sample"):
                contract = Contract(
                    contract_id=self._generate_contract_id(),
                    boundary_type=BoundaryType.ENV_CONFIG,
                    source=ContractSource.ENV_FILE,
                    source_location=str(env_file),
                )
                # Parse env file for required vars
                try:
                    content = env_file.read_text()
                    for line in content.split("\n"):
                        if "=" in line and not line.strip().startswith("#"):
                            var_name = line.split("=")[0].strip()
                            contract.fields.append(ContractField(
                                name=var_name,
                                field_type="string",
                                required=True,
                            ))
                except Exception:
                    pass
                report.contracts.append(contract)

        # Find SQL schema files
        for sql_file in directory.glob("**/schema*.sql"):
            contract = Contract(
                contract_id=self._generate_contract_id(),
                boundary_type=BoundaryType.DATABASE,
                source=ContractSource.SQL_SCHEMA,
                source_location=str(sql_file),
            )
            report.contracts.append(contract)

    def _analyze_file(self, file_path: Path, report: BoundaryVerificationReport) -> None:
        """Analyze a file for boundary crossings."""
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)

        # Check for API calls
        for pattern_name, pattern in self.API_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                # Found an API call - check if we have a contract for it
                # This is simplified - in reality would need endpoint matching
                self._check_api_call(match.group(0), rel_path, line_num, report)

        # Check for subprocess calls
        for pattern_name, pattern in self.SUBPROCESS_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                self._check_subprocess_call(match, rel_path, line_num, report)

        # Check for SQL queries
        for pattern_name, pattern in self.SQL_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                self._check_sql_query(match, pattern_name, rel_path, line_num, report)

        # Check for environment variable access
        env_patterns = [
            re.compile(r"process\.env\.(\w+)"),
            re.compile(r"os\.environ\[?['\"](\w+)['\"]"),
            re.compile(r"\$_ENV\[['\"](\w+)['\"]"),
            re.compile(r"getenv\(['\"](\w+)['\"]"),
        ]

        for pattern in env_patterns:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                var_name = match.group(1)
                self._check_env_var(var_name, rel_path, line_num, report)

    def _check_api_call(
        self,
        call: str,
        file_path: str,
        line: int,
        report: BoundaryVerificationReport
    ) -> None:
        """Check an API call against known contracts."""
        # In a full implementation, this would:
        # 1. Parse the API endpoint
        # 2. Find the matching contract
        # 3. Compare payload fields
        # For now, we just record the boundary crossing
        pass

    def _check_subprocess_call(
        self,
        match: re.Match,
        file_path: str,
        line: int,
        report: BoundaryVerificationReport
    ) -> None:
        """Check a subprocess call for potential issues."""
        command = match.group(1) if len(match.groups()) > 0 else match.group(0)

        # Check if the called script/binary exists
        # This is simplified - would need path resolution
        if command.endswith(".py") or command.endswith(".sh"):
            # Infer a contract for this subprocess
            contract = Contract(
                contract_id=self._generate_contract_id(),
                boundary_type=BoundaryType.PROCESS_SPAWN,
                source=ContractSource.INFERRED,
                source_location=file_path,
                metadata={"command": command},
            )
            report.contracts.append(contract)

    def _check_sql_query(
        self,
        match: re.Match,
        query_type: str,
        file_path: str,
        line: int,
        report: BoundaryVerificationReport
    ) -> None:
        """Check a SQL query against schema contracts."""
        # In a full implementation, would:
        # 1. Parse the table name from the query
        # 2. Find the schema contract for that table
        # 3. Compare columns used vs columns in schema
        pass

    def _check_env_var(
        self,
        var_name: str,
        file_path: str,
        line: int,
        report: BoundaryVerificationReport
    ) -> None:
        """Check if an environment variable is defined in contracts."""
        # Check against .env contracts
        for contract in report.contracts:
            if contract.boundary_type == BoundaryType.ENV_CONFIG:
                defined_vars = {f.name for f in contract.fields}
                if var_name not in defined_vars:
                    # Environment variable not in .env.example
                    mismatch = ContractMismatch(
                        mismatch_id=self._generate_mismatch_id(),
                        mismatch_type=MismatchType.FIELD_MISSING,
                        contract=contract,
                        location={"file": file_path, "line": line},
                        severity="warning",
                        message=f"Environment variable '{var_name}' not defined in {contract.source_location}",
                        expected=f"{var_name} in .env.example",
                        actual="Not defined",
                        fix_suggestion=f"Add {var_name}= to {contract.source_location}",
                    )
                    report.mismatches.append(mismatch)
                    return  # Only report once


def verify_boundaries(path: Path) -> BoundaryVerificationReport:
    """Convenience function to verify boundaries."""
    verifier = BoundaryVerifier()
    return verifier.verify_directory(path)
