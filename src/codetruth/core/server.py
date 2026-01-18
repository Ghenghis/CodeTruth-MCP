"""
Milestone 1: Core MCP Server Infrastructure

MCP server with STDIO/SSE transport, tool routing, and policy enforcement.
Implements the "no claims without proof" policy at the protocol level.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    Prompt,
    PromptMessage,
    GetPromptResult,
    CallToolResult,
)
from pydantic import BaseModel

from codetruth.core.config import CodeTruthConfig
from codetruth.core.evidence import EvidenceVault, Evidence, EvidenceType
from codetruth.core.truth_table import TruthTable
from codetruth.core.inventory import RepoInventory
from codetruth.core.gates import GateLadder

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """Definition of an MCP tool with its handler."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None

    class Config:
        arbitrary_types_allowed = True


class CodeTruthServer:
    """
    Evidence-Based Code Auditing MCP Server.

    Core rule: No claims without evidence.
    A finding is only reported if it has reproducible proof.
    """

    def __init__(self, config: CodeTruthConfig | None = None):
        self.config = config or CodeTruthConfig()
        self.server = Server("codetruth-mcp")
        self.evidence_vault: EvidenceVault | None = None
        self.tools: dict[str, ToolDefinition] = {}

        self._register_core_tools()
        self._setup_handlers()

    def _register_core_tools(self) -> None:
        """Register all MCP tools."""

        # Milestone 1: Core infrastructure tools
        self._register_tool(
            ToolDefinition(
                name="discover_repos",
                description="Scan directories for repositories to audit",
                input_schema={
                    "type": "object",
                    "properties": {
                        "root_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Root directories to scan for repos",
                        },
                        "exclude_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Glob patterns to exclude",
                            "default": ["**/node_modules", "**/.git", "**/venv"],
                        },
                    },
                    "required": ["root_paths"],
                },
            )
        )

        # Milestone 2: Evidence management
        self._register_tool(
            ToolDefinition(
                name="search_evidence",
                description="Query the evidence vault for findings with proof",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "evidence_type": {
                            "type": "string",
                            "enum": [
                                "lint",
                                "type_error",
                                "security",
                                "dead_code",
                                "unwired_ui",
                                "contract_mismatch",
                                "test_failure",
                                "coverage_gap",
                            ],
                            "description": "Type of evidence to search",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["error", "warning", "note"],
                            "description": "Minimum severity",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 3-4: AST and Reachability
        self._register_tool(
            ToolDefinition(
                name="inventory",
                description="Generate complete repo inventory: languages, packages, entrypoints, routes, UI components",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "include_ast": {
                            "type": "boolean",
                            "description": "Include AST analysis",
                            "default": True,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="reachability_graph",
                description="Build call graph and identify unreachable code paths",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "entry_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific entry points to trace from",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "dot", "mermaid"],
                            "default": "json",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 5-6: Dead code and UI wiring
        self._register_tool(
            ToolDefinition(
                name="dead_code_audit",
                description="Detect unreachable functions, unused exports, orphan components",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "include_tests": {
                            "type": "boolean",
                            "description": "Include test files in analysis",
                            "default": False,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="ui_wiring_audit",
                description="Detect dead buttons, unbound handlers, missing routes",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "framework": {
                            "type": "string",
                            "enum": ["react", "vue", "angular", "svelte", "auto"],
                            "default": "auto",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 7: API contracts
        self._register_tool(
            ToolDefinition(
                name="api_contract_audit",
                description="Validate API contracts against OpenAPI/JSON Schema specs",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "spec_path": {
                            "type": "string",
                            "description": "Path to OpenAPI/JSON Schema spec",
                        },
                        "strict": {
                            "type": "boolean",
                            "description": "Strict validation mode",
                            "default": True,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 8-9: Security scanning
        self._register_tool(
            ToolDefinition(
                name="secret_scan",
                description="Scan for leaked secrets, API keys, credentials",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "tools": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["gitleaks", "trufflehog"]},
                            "default": ["gitleaks"],
                        },
                        "verify": {
                            "type": "boolean",
                            "description": "Verify if secrets are live (trufflehog)",
                            "default": False,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="dependency_audit",
                description="Scan dependencies for known vulnerabilities",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "tools": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["npm_audit", "pip_audit", "trivy", "osv"],
                            },
                            "default": ["osv"],
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 10-12: Static analysis
        self._register_tool(
            ToolDefinition(
                name="lint_audit",
                description="Run multi-language linting (eslint, ruff, prettier, etc.)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "fix": {
                            "type": "boolean",
                            "description": "Auto-fix issues where possible",
                            "default": False,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="type_check",
                description="Run type checking (tsc, mypy, pyright)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "strict": {
                            "type": "boolean",
                            "description": "Strict mode",
                            "default": True,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="sast_scan",
                description="Run SAST scanning with semgrep/CodeQL",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "rulesets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["p/default", "p/owasp-top-ten"],
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 13-15: E2E and coverage
        self._register_tool(
            ToolDefinition(
                name="run_e2e",
                description="Execute Playwright E2E tests with trace capture",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "flows": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific flows to test",
                        },
                        "trace": {
                            "type": "boolean",
                            "description": "Capture traces",
                            "default": True,
                        },
                        "video": {
                            "type": "boolean",
                            "description": "Record video",
                            "default": False,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="visual_regression",
                description="Run visual regression tests with screenshot comparison",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "baseline_dir": {
                            "type": "string",
                            "description": "Directory with baseline screenshots",
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Pixel difference threshold (0-1)",
                            "default": 0.01,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="coverage_audit",
                description="Analyze code coverage and identify gaps",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "threshold": {
                            "type": "number",
                            "description": "Minimum coverage threshold",
                            "default": 80,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 19-20: Quality gates and truth table
        self._register_tool(
            ToolDefinition(
                name="run_gates",
                description="Execute quality gate ladder (Gates 0-6)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "profile": {
                            "type": "string",
                            "enum": ["fast", "standard", "deep", "forensics"],
                            "default": "standard",
                        },
                        "gates": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0, "maximum": 6},
                            "description": "Specific gates to run",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        self._register_tool(
            ToolDefinition(
                name="generate_truth_table",
                description="Generate Feature Truth Table with status for each feature",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "spec_source": {
                            "type": "string",
                            "description": "Path to feature specs (README, issues, etc.)",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "markdown", "html"],
                            "default": "json",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 22: Fix planning
        self._register_tool(
            ToolDefinition(
                name="create_fix_plan",
                description="Generate remediation plan with acceptance tests",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "findings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Finding IDs to create fix plan for",
                        },
                        "include_tests": {
                            "type": "boolean",
                            "description": "Generate acceptance tests",
                            "default": True,
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Milestone 23: Trace correlation
        self._register_tool(
            ToolDefinition(
                name="correlate_traces",
                description="Correlate trace IDs across UI, API, and DB layers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "trace_id": {"type": "string", "description": "Trace ID to follow"},
                        "logs_dir": {
                            "type": "string",
                            "description": "Directory containing log files",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

        # Full audit tool
        self._register_tool(
            ToolDefinition(
                name="full_audit",
                description="Run complete evidence-based audit with all analyzers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Repository path"},
                        "profile": {
                            "type": "string",
                            "enum": ["fast", "standard", "deep", "forensics"],
                            "default": "standard",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory for audit outputs",
                        },
                    },
                    "required": ["repo_path"],
                },
            )
        )

    def _register_tool(self, tool_def: ToolDefinition) -> None:
        """Register a tool definition."""
        self.tools[tool_def.name] = tool_def

    def _setup_handlers(self) -> None:
        """Setup MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """Return all available tools."""
            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.input_schema,
                )
                for tool in self.tools.values()
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool invocation with evidence enforcement."""
            if name not in self.tools:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            except Exception as e:
                logger.exception(f"Tool execution failed: {name}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": str(e), "tool": name, "arguments": arguments}, indent=2
                        ),
                    )
                ]

        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """Return available resources."""
            return [
                Resource(
                    uri="codetruth://evidence-vault",
                    name="Evidence Vault",
                    description="SQLite database containing all audit evidence",
                    mimeType="application/x-sqlite3",
                ),
                Resource(
                    uri="codetruth://truth-table",
                    name="Feature Truth Table",
                    description="Current feature status table",
                    mimeType="application/json",
                ),
            ]

        @self.server.list_prompts()
        async def handle_list_prompts() -> list[Prompt]:
            """Return available prompts."""
            return [
                Prompt(
                    name="full-audit",
                    description="Run a complete evidence-based audit",
                    arguments=[
                        {
                            "name": "repo_path",
                            "description": "Path to the repository",
                            "required": True,
                        }
                    ],
                ),
                Prompt(
                    name="find-dead-code",
                    description="Find all unreachable and unused code",
                    arguments=[
                        {
                            "name": "repo_path",
                            "description": "Path to the repository",
                            "required": True,
                        }
                    ],
                ),
                Prompt(
                    name="security-audit",
                    description="Run comprehensive security analysis",
                    arguments=[
                        {
                            "name": "repo_path",
                            "description": "Path to the repository",
                            "required": True,
                        }
                    ],
                ),
            ]

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict[str, str]) -> GetPromptResult:
            """Return prompt content."""
            repo_path = arguments.get("repo_path", ".")

            prompts = {
                "full-audit": f"""You are CodeTruth, an evidence-based code auditor.

Run a complete audit of the repository at: {repo_path}

Follow these steps:
1. Generate inventory with `inventory` tool
2. Run quality gates with `run_gates` tool (profile: standard)
3. Run dead code analysis with `dead_code_audit`
4. Run UI wiring audit with `ui_wiring_audit`
5. Run security scans with `secret_scan` and `dependency_audit`
6. Generate the Feature Truth Table with `generate_truth_table`
7. Create fix plans for critical findings with `create_fix_plan`

IMPORTANT: Every finding must have evidence. Do not report issues without proof.
""",
                "find-dead-code": f"""You are CodeTruth, an evidence-based code auditor.

Find all dead and unreachable code in: {repo_path}

Use these tools:
1. `inventory` - to understand the codebase structure
2. `reachability_graph` - to build the call graph
3. `dead_code_audit` - to identify unreachable code
4. `ui_wiring_audit` - to find dead UI elements

Report only what you can prove is unreachable.
""",
                "security-audit": f"""You are CodeTruth, an evidence-based security auditor.

Run a comprehensive security audit of: {repo_path}

Use these tools:
1. `secret_scan` - find leaked credentials
2. `dependency_audit` - find vulnerable dependencies
3. `sast_scan` - static application security testing
4. `api_contract_audit` - validate API security

Every vulnerability must have:
- CVE/CWE reference where applicable
- Exact file and line location
- Proof of exploitability or risk assessment
""",
            }

            if name not in prompts:
                return GetPromptResult(
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=f"Unknown prompt: {name}"),
                        )
                    ]
                )

            return GetPromptResult(
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=prompts[name]),
                    )
                ]
            )

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return results with evidence."""
        from codetruth.analyzers import get_analyzer

        repo_path = arguments.get("repo_path", ".")

        # Initialize evidence vault if not done
        if self.evidence_vault is None:
            self.evidence_vault = EvidenceVault(self.config.db_path)
            await self.evidence_vault.initialize()

        # Route to appropriate analyzer
        if name == "discover_repos":
            from codetruth.core.discovery import discover_repositories

            return await discover_repositories(
                arguments["root_paths"], arguments.get("exclude_patterns", [])
            )

        elif name == "inventory":
            inventory = RepoInventory(Path(repo_path))
            return await inventory.generate(include_ast=arguments.get("include_ast", True))

        elif name == "run_gates":
            ladder = GateLadder(Path(repo_path), self.evidence_vault)
            return await ladder.run(
                profile=arguments.get("profile", "standard"),
                gates=arguments.get("gates"),
            )

        elif name == "generate_truth_table":
            from codetruth.core.truth_table import TruthTableGenerator

            generator = TruthTableGenerator(Path(repo_path), self.evidence_vault)
            return await generator.generate(
                spec_source=arguments.get("spec_source"),
                output_format=arguments.get("output_format", "json"),
            )

        elif name == "full_audit":
            return await self._run_full_audit(repo_path, arguments)

        else:
            # Use generic analyzer routing
            analyzer = get_analyzer(name)
            if analyzer:
                result = await analyzer.run(Path(repo_path), arguments, self.evidence_vault)
                return result.model_dump()
            else:
                return {"error": f"No analyzer found for tool: {name}"}

    async def _run_full_audit(
        self, repo_path: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Run complete audit with all analyzers."""
        profile = arguments.get("profile", "standard")
        output_dir = arguments.get("output_dir")

        results: dict[str, Any] = {
            "repo_path": repo_path,
            "profile": profile,
            "stages": {},
        }

        # Stage 1: Inventory
        inventory = RepoInventory(Path(repo_path))
        results["stages"]["inventory"] = await inventory.generate(include_ast=True)

        # Stage 2: Quality Gates
        if self.evidence_vault:
            ladder = GateLadder(Path(repo_path), self.evidence_vault)
            results["stages"]["gates"] = await ladder.run(profile=profile)

        # Stage 3: Static Analysis
        from codetruth.analyzers import (
            DeadCodeAnalyzer,
            UIWiringAnalyzer,
            LintAnalyzer,
            TypeCheckAnalyzer,
            SASTAnalyzer,
        )

        analyzers = [
            ("dead_code", DeadCodeAnalyzer()),
            ("ui_wiring", UIWiringAnalyzer()),
            ("lint", LintAnalyzer()),
            ("type_check", TypeCheckAnalyzer()),
            ("sast", SASTAnalyzer()),
        ]

        for name, analyzer in analyzers:
            try:
                result = await analyzer.run(Path(repo_path), {}, self.evidence_vault)
                results["stages"][name] = result.model_dump()
            except Exception as e:
                results["stages"][name] = {"error": str(e)}

        # Stage 4: Security
        from codetruth.analyzers import SecretScanner, DependencyAuditor

        security_analyzers = [
            ("secrets", SecretScanner()),
            ("dependencies", DependencyAuditor()),
        ]

        for name, analyzer in security_analyzers:
            try:
                result = await analyzer.run(Path(repo_path), {}, self.evidence_vault)
                results["stages"][name] = result.model_dump()
            except Exception as e:
                results["stages"][name] = {"error": str(e)}

        # Stage 5: Generate Truth Table
        from codetruth.core.truth_table import TruthTableGenerator

        if self.evidence_vault:
            generator = TruthTableGenerator(Path(repo_path), self.evidence_vault)
            results["truth_table"] = await generator.generate()

        # Save results if output_dir specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            with open(output_path / "audit_report.json", "w") as f:
                json.dump(results, f, indent=2, default=str)

        return results

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting CodeTruth MCP Server")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="codetruth-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    """Main entry point."""
    config = CodeTruthConfig()
    server = CodeTruthServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
