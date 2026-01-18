"""
API Contract Analyzer

Validates API contracts against OpenAPI/JSON Schema specifications.
Detects mismatches between spec and implementation.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from codetruth.analyzers.base import BaseAnalyzer, AnalysisResult
from codetruth.core.evidence import Evidence, EvidenceType, Severity, EvidenceLocation

if TYPE_CHECKING:
    from codetruth.core.evidence import EvidenceVault


class APIContractAnalyzer(BaseAnalyzer):
    """API contract validation analyzer."""

    name = "contracts"
    description = "Validate API contracts"

    async def run(
        self,
        repo_path: Path,
        options: dict[str, Any],
        evidence_vault: "EvidenceVault | None" = None,
    ) -> AnalysisResult:
        result = AnalysisResult(
            analyzer_name=self.name,
            started_at=datetime.utcnow(),
        )

        try:
            # Find OpenAPI specs
            openapi_specs = await self._find_openapi_specs(repo_path)

            # Find API routes in code
            api_routes = await self._find_api_routes(repo_path)

            # Cross-reference
            await self._validate_contracts(openapi_specs, api_routes, repo_path, result, evidence_vault)

            result.success = True
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = int((result.completed_at - result.started_at).total_seconds() * 1000)
        result.findings_count = len(result.findings)

        return result

    async def _find_openapi_specs(self, repo_path: Path) -> list[dict[str, Any]]:
        """Find OpenAPI/Swagger specification files."""
        specs = []

        spec_files = list(repo_path.glob("**/openapi.yaml")) + \
                     list(repo_path.glob("**/openapi.json")) + \
                     list(repo_path.glob("**/swagger.yaml")) + \
                     list(repo_path.glob("**/swagger.json")) + \
                     list(repo_path.glob("**/api.yaml"))

        for spec_file in spec_files:
            if self._is_ignored(spec_file):
                continue

            try:
                content = spec_file.read_text()
                if spec_file.suffix in [".yaml", ".yml"]:
                    import yaml
                    spec = yaml.safe_load(content)
                else:
                    spec = json.loads(content)

                if spec.get("openapi") or spec.get("swagger"):
                    specs.append({
                        "file": str(spec_file.relative_to(repo_path)),
                        "spec": spec,
                    })
            except:
                continue

        return specs

    async def _find_api_routes(self, repo_path: Path) -> list[dict[str, Any]]:
        """Find API routes defined in code."""
        routes = []

        # Python routes (FastAPI, Flask)
        for path in repo_path.rglob("*.py"):
            if self._is_ignored(path):
                continue

            content = path.read_text(errors="ignore")
            rel_path = str(path.relative_to(repo_path))

            # FastAPI routes
            for match in re.finditer(r'@(?:app|router)\.(\w+)\(["\']([^"\']+)["\']', content):
                method, route = match.groups()
                routes.append({
                    "method": method.upper(),
                    "path": route,
                    "file": rel_path,
                    "framework": "fastapi",
                })

            # Flask routes
            for match in re.finditer(r'@\w+\.route\(["\']([^"\']+)["\'](?:.*?methods=\[([^\]]+)\])?', content):
                route, methods = match.groups()
                method_list = ["GET"]
                if methods:
                    method_list = [m.strip().strip("'\"") for m in methods.split(",")]
                for method in method_list:
                    routes.append({
                        "method": method.upper(),
                        "path": route,
                        "file": rel_path,
                        "framework": "flask",
                    })

        # TypeScript routes (Express, Fastify)
        for ext in ["*.ts", "*.js"]:
            for path in repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")
                rel_path = str(path.relative_to(repo_path))

                # Express/Fastify routes
                for match in re.finditer(r'\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content):
                    method, route = match.groups()
                    if route.startswith("/"):
                        routes.append({
                            "method": method.upper(),
                            "path": route,
                            "file": rel_path,
                            "framework": "express",
                        })

        return routes

    async def _validate_contracts(
        self,
        specs: list[dict[str, Any]],
        routes: list[dict[str, Any]],
        repo_path: Path,
        result: AnalysisResult,
        evidence_vault: "EvidenceVault | None",
    ) -> None:
        """Validate API routes against OpenAPI specs."""

        if not specs:
            # No OpenAPI spec found - check if there should be one
            if routes:
                result.findings.append({
                    "type": "missing_spec",
                    "severity": "note",
                    "message": f"Found {len(routes)} API routes but no OpenAPI specification",
                    "tool": self.name,
                    "suggested_fix": "Consider adding an OpenAPI spec for API documentation and validation",
                })
            return

        for spec_info in specs:
            spec = spec_info["spec"]
            spec_file = spec_info["file"]

            # Get paths from spec
            spec_paths = spec.get("paths", {})

            # Check each route against spec
            for route in routes:
                route_path = self._normalize_path(route["path"])
                route_method = route["method"].lower()

                # Try to find matching spec path
                matching_spec_path = self._find_matching_spec_path(route_path, spec_paths)

                if not matching_spec_path:
                    finding = {
                        "type": "undocumented_route",
                        "severity": "warning",
                        "message": f"Route {route['method']} {route['path']} not documented in OpenAPI spec",
                        "file": route["file"],
                        "tool": self.name,
                    }
                    result.findings.append(finding)

                    if evidence_vault:
                        evidence = Evidence(
                            evidence_type=EvidenceType.CONTRACT_MISMATCH,
                            severity=Severity.WARNING,
                            message=finding["message"],
                            location=EvidenceLocation(file_path=route["file"]),
                            tool_name=self.name,
                            repo_path=str(repo_path),
                        )
                        await evidence_vault.store_evidence(evidence)
                else:
                    # Check if method is documented
                    path_spec = spec_paths.get(matching_spec_path, {})
                    if route_method not in path_spec:
                        finding = {
                            "type": "undocumented_method",
                            "severity": "warning",
                            "message": f"Method {route['method']} for path {route['path']} not documented in spec",
                            "file": route["file"],
                            "tool": self.name,
                        }
                        result.findings.append(finding)

            # Check for spec paths without implementation
            for spec_path, path_spec in spec_paths.items():
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method in path_spec:
                        # Check if implemented
                        implemented = any(
                            self._paths_match(r["path"], spec_path) and r["method"].lower() == method
                            for r in routes
                        )
                        if not implemented:
                            finding = {
                                "type": "unimplemented_route",
                                "severity": "error",
                                "message": f"Spec defines {method.upper()} {spec_path} but no implementation found",
                                "file": spec_file,
                                "tool": self.name,
                            }
                            result.findings.append(finding)

    def _normalize_path(self, path: str) -> str:
        """Normalize path for comparison."""
        # Convert Express-style :param to OpenAPI {param}
        path = re.sub(r":(\w+)", r"{\1}", path)
        return path.rstrip("/") or "/"

    def _find_matching_spec_path(self, route_path: str, spec_paths: dict[str, Any]) -> str | None:
        """Find matching spec path for a route."""
        for spec_path in spec_paths:
            if self._paths_match(route_path, spec_path):
                return spec_path
        return None

    def _paths_match(self, route_path: str, spec_path: str) -> bool:
        """Check if a route path matches a spec path."""
        # Normalize both
        route_normalized = self._normalize_path(route_path)
        spec_normalized = spec_path.rstrip("/") or "/"

        # Exact match
        if route_normalized == spec_normalized:
            return True

        # Pattern match (handle path params)
        route_parts = route_normalized.split("/")
        spec_parts = spec_normalized.split("/")

        if len(route_parts) != len(spec_parts):
            return False

        for route_part, spec_part in zip(route_parts, spec_parts):
            # Both are params
            if route_part.startswith("{") and spec_part.startswith("{"):
                continue
            # Neither are params, must match
            if route_part != spec_part:
                return False

        return True
