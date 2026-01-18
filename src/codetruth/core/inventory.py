"""
Milestone 3 & 4: Repository Inventory with AST Parsing and Reachability

Generates complete inventory of a repository:
- Languages and package manifests
- Entry points (apps, services, CLI, jobs)
- Modules and packages
- API routes and handlers
- UI routes, pages, components
- DB schemas and migrations
- Config and env contracts
- External integrations
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx
from pydantic import BaseModel, Field


class EntryPointType(str, Enum):
    """Types of entry points in a codebase."""

    MAIN = "main"
    CLI = "cli"
    API_SERVER = "api_server"
    WEB_SERVER = "web_server"
    WORKER = "worker"
    JOB = "job"
    LAMBDA = "lambda"
    TEST = "test"
    SCRIPT = "script"


class ComponentType(str, Enum):
    """Types of components."""

    PAGE = "page"
    COMPONENT = "component"
    LAYOUT = "layout"
    HOOK = "hook"
    CONTEXT = "context"
    STORE = "store"
    UTILITY = "utility"
    SERVICE = "service"
    MIDDLEWARE = "middleware"
    ROUTE_HANDLER = "route_handler"


class Language(str, Enum):
    """Supported languages."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    C = "c"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    SHELL = "shell"
    LUA = "lua"
    POWERSHELL = "powershell"
    UNKNOWN = "unknown"


class EntryPoint(BaseModel):
    """An entry point into the codebase."""

    name: str
    entry_type: EntryPointType
    file_path: str
    function_name: str | None = None
    line_number: int | None = None
    is_exported: bool = True
    dependencies: list[str] = Field(default_factory=list)


class Module(BaseModel):
    """A module or package in the codebase."""

    name: str
    path: str
    language: Language
    is_package: bool = False
    exports: list[str] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    entry_points: list[EntryPoint] = Field(default_factory=list)


class APIRoute(BaseModel):
    """An API route definition."""

    method: str  # GET, POST, PUT, DELETE, etc.
    path: str
    handler_file: str
    handler_function: str
    line_number: int | None = None
    is_registered: bool = True  # Is it actually mounted?
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    response_schema: dict[str, Any] | None = None


class UIComponent(BaseModel):
    """A UI component."""

    name: str
    file_path: str
    component_type: ComponentType
    framework: str  # react, vue, angular, svelte
    props: list[dict[str, Any]] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    handlers: list[str] = Field(default_factory=list)
    is_exported: bool = True
    line_number: int | None = None


class UIRoute(BaseModel):
    """A UI route/page."""

    path: str
    component: str
    file_path: str
    is_protected: bool = False
    is_lazy: bool = False


class DBSchema(BaseModel):
    """A database schema/model definition."""

    name: str
    file_path: str
    table_name: str | None = None
    columns: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)


class ConfigContract(BaseModel):
    """An environment/config contract."""

    name: str
    source: str  # .env, config file, etc.
    required: bool = True
    default_value: str | None = None
    description: str | None = None


class ExternalIntegration(BaseModel):
    """An external integration/API."""

    name: str
    integration_type: str  # api, database, queue, storage, etc.
    file_paths: list[str] = Field(default_factory=list)
    config_keys: list[str] = Field(default_factory=list)


@dataclass
class ASTNode:
    """A node in the AST."""

    node_type: str
    name: str | None
    file_path: str
    start_line: int
    end_line: int
    children: list["ASTNode"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class RepoInventory:
    """
    Generates complete repository inventory using AST parsing.

    Uses tree-sitter for multi-language AST analysis.
    """

    # File extension to language mapping
    EXTENSION_MAP: dict[str, Language] = {
        ".py": Language.PYTHON,
        ".ts": Language.TYPESCRIPT,
        ".tsx": Language.TYPESCRIPT,
        ".js": Language.JAVASCRIPT,
        ".jsx": Language.JAVASCRIPT,
        ".rs": Language.RUST,
        ".go": Language.GO,
        ".java": Language.JAVA,
        ".cs": Language.CSHARP,
        ".cpp": Language.CPP,
        ".cc": Language.CPP,
        ".c": Language.C,
        ".h": Language.C,
        ".rb": Language.RUBY,
        ".php": Language.PHP,
        ".swift": Language.SWIFT,
        ".kt": Language.KOTLIN,
        ".html": Language.HTML,
        ".htm": Language.HTML,
        ".css": Language.CSS,
        ".scss": Language.CSS,
        ".sql": Language.SQL,
        ".sh": Language.SHELL,
        ".bash": Language.SHELL,
        ".lua": Language.LUA,
        ".ps1": Language.POWERSHELL,
    }

    # Package manifest files
    MANIFEST_FILES: dict[str, str] = {
        "package.json": "npm",
        "pyproject.toml": "pyproject",
        "setup.py": "setuptools",
        "requirements.txt": "pip",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "pom.xml": "maven",
        "build.gradle": "gradle",
        "Gemfile": "bundler",
        "composer.json": "composer",
    }

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.languages: set[Language] = set()
        self.manifests: dict[str, Path] = {}
        self.modules: list[Module] = []
        self.entry_points: list[EntryPoint] = []
        self.api_routes: list[APIRoute] = []
        self.ui_components: list[UIComponent] = []
        self.ui_routes: list[UIRoute] = []
        self.db_schemas: list[DBSchema] = []
        self.config_contracts: list[ConfigContract] = []
        self.external_integrations: list[ExternalIntegration] = []

        # Call graph for reachability analysis
        self.call_graph: nx.DiGraph = nx.DiGraph()

    async def generate(self, include_ast: bool = True) -> dict[str, Any]:
        """Generate complete inventory."""
        # Scan for files and languages
        await self._scan_files()

        # Find package manifests
        await self._find_manifests()

        # Parse entry points
        await self._find_entry_points()

        # Parse API routes
        await self._find_api_routes()

        # Parse UI components and routes
        await self._find_ui_components()
        await self._find_ui_routes()

        # Parse DB schemas
        await self._find_db_schemas()

        # Parse config contracts
        await self._find_config_contracts()

        # Find external integrations
        await self._find_integrations()

        # Build call graph if AST analysis enabled
        if include_ast:
            await self._build_call_graph()

        return self._to_dict()

    async def _scan_files(self) -> None:
        """Scan repository for all source files."""
        for path in self.repo_path.rglob("*"):
            if path.is_file() and not self._is_ignored(path):
                ext = path.suffix.lower()
                if ext in self.EXTENSION_MAP:
                    self.languages.add(self.EXTENSION_MAP[ext])

    async def _find_manifests(self) -> None:
        """Find all package manifest files."""
        for filename, manifest_type in self.MANIFEST_FILES.items():
            manifest_path = self.repo_path / filename
            if manifest_path.exists():
                self.manifests[manifest_type] = manifest_path

            # Also check subdirectories for monorepos
            for path in self.repo_path.rglob(filename):
                if not self._is_ignored(path):
                    key = f"{manifest_type}:{path.relative_to(self.repo_path).parent}"
                    self.manifests[key] = path

    async def _find_entry_points(self) -> None:
        """Find all entry points in the codebase."""
        # Python entry points
        if Language.PYTHON in self.languages:
            await self._find_python_entry_points()

        # Node/TypeScript entry points
        if Language.TYPESCRIPT in self.languages or Language.JAVASCRIPT in self.languages:
            await self._find_node_entry_points()

    async def _find_python_entry_points(self) -> None:
        """Find Python entry points."""
        for path in self.repo_path.rglob("*.py"):
            if self._is_ignored(path):
                continue

            content = path.read_text(errors="ignore")

            # Main module entry point
            if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                self.entry_points.append(
                    EntryPoint(
                        name=path.stem,
                        entry_type=EntryPointType.MAIN,
                        file_path=str(path.relative_to(self.repo_path)),
                        function_name="__main__",
                    )
                )

            # CLI frameworks
            if "@click.command" in content or "@app.command" in content:
                self.entry_points.append(
                    EntryPoint(
                        name=path.stem,
                        entry_type=EntryPointType.CLI,
                        file_path=str(path.relative_to(self.repo_path)),
                    )
                )

            # API frameworks
            if "FastAPI()" in content or "Flask(__name__)" in content:
                self.entry_points.append(
                    EntryPoint(
                        name=path.stem,
                        entry_type=EntryPointType.API_SERVER,
                        file_path=str(path.relative_to(self.repo_path)),
                    )
                )

    async def _find_node_entry_points(self) -> None:
        """Find Node.js/TypeScript entry points."""
        # Check package.json for entry points
        for key, manifest_path in self.manifests.items():
            if not key.startswith("npm"):
                continue

            try:
                with open(manifest_path) as f:
                    pkg = json.load(f)

                # Main entry
                if "main" in pkg:
                    self.entry_points.append(
                        EntryPoint(
                            name=pkg.get("name", "main"),
                            entry_type=EntryPointType.MAIN,
                            file_path=pkg["main"],
                        )
                    )

                # Scripts
                for script_name, script_cmd in pkg.get("scripts", {}).items():
                    if script_name in ("start", "serve", "dev"):
                        self.entry_points.append(
                            EntryPoint(
                                name=script_name,
                                entry_type=EntryPointType.API_SERVER,
                                file_path=script_cmd.split()[-1] if script_cmd else "",
                            )
                        )
            except (json.JSONDecodeError, OSError):
                continue

        # Look for common entry point files
        for filename in ["index.ts", "index.js", "main.ts", "main.js", "server.ts", "server.js"]:
            for path in self.repo_path.rglob(filename):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")

                # Express/Fastify/Koa apps
                if (
                    "express()" in content
                    or "fastify()" in content
                    or "new Koa()" in content
                ):
                    self.entry_points.append(
                        EntryPoint(
                            name=path.stem,
                            entry_type=EntryPointType.API_SERVER,
                            file_path=str(path.relative_to(self.repo_path)),
                        )
                    )

                # Next.js pages
                if "pages" in str(path.parent) or "app" in str(path.parent):
                    self.entry_points.append(
                        EntryPoint(
                            name=path.stem,
                            entry_type=EntryPointType.WEB_SERVER,
                            file_path=str(path.relative_to(self.repo_path)),
                        )
                    )

    async def _find_api_routes(self) -> None:
        """Find API route definitions."""
        # Python frameworks
        if Language.PYTHON in self.languages:
            await self._find_python_routes()

        # Node frameworks
        if Language.TYPESCRIPT in self.languages or Language.JAVASCRIPT in self.languages:
            await self._find_node_routes()

    async def _find_python_routes(self) -> None:
        """Find Python API routes (FastAPI, Flask, etc.)."""
        route_patterns = [
            (r'@app\.get\(["\']([^"\']+)', "GET"),
            (r'@app\.post\(["\']([^"\']+)', "POST"),
            (r'@app\.put\(["\']([^"\']+)', "PUT"),
            (r'@app\.delete\(["\']([^"\']+)', "DELETE"),
            (r'@app\.patch\(["\']([^"\']+)', "PATCH"),
            (r'@router\.get\(["\']([^"\']+)', "GET"),
            (r'@router\.post\(["\']([^"\']+)', "POST"),
        ]

        import re

        for path in self.repo_path.rglob("*.py"):
            if self._is_ignored(path):
                continue

            content = path.read_text(errors="ignore")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                for pattern, method in route_patterns:
                    match = re.search(pattern, line)
                    if match:
                        # Find the function name on the next non-decorator line
                        func_name = None
                        for j in range(i + 1, min(i + 10, len(lines))):
                            func_match = re.match(r"(?:async )?def (\w+)", lines[j])
                            if func_match:
                                func_name = func_match.group(1)
                                break

                        self.api_routes.append(
                            APIRoute(
                                method=method,
                                path=match.group(1),
                                handler_file=str(path.relative_to(self.repo_path)),
                                handler_function=func_name or "unknown",
                                line_number=i + 1,
                            )
                        )

    async def _find_node_routes(self) -> None:
        """Find Node.js API routes (Express, Fastify, etc.)."""
        import re

        route_patterns = [
            (r'\.get\(["\']([^"\']+)', "GET"),
            (r'\.post\(["\']([^"\']+)', "POST"),
            (r'\.put\(["\']([^"\']+)', "PUT"),
            (r'\.delete\(["\']([^"\']+)', "DELETE"),
            (r'\.patch\(["\']([^"\']+)', "PATCH"),
        ]

        for ext in ["*.ts", "*.js"]:
            for path in self.repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")
                lines = content.split("\n")

                for i, line in enumerate(lines):
                    for pattern, method in route_patterns:
                        match = re.search(pattern, line)
                        if match:
                            route_path = match.group(1)
                            if route_path.startswith("/"):
                                self.api_routes.append(
                                    APIRoute(
                                        method=method,
                                        path=route_path,
                                        handler_file=str(path.relative_to(self.repo_path)),
                                        handler_function="anonymous",
                                        line_number=i + 1,
                                    )
                                )

    async def _find_ui_components(self) -> None:
        """Find UI components."""
        # React components
        if Language.TYPESCRIPT in self.languages or Language.JAVASCRIPT in self.languages:
            await self._find_react_components()

    async def _find_react_components(self) -> None:
        """Find React components."""
        import re

        for ext in ["*.tsx", "*.jsx"]:
            for path in self.repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")

                # Function components
                func_matches = re.findall(
                    r"(?:export\s+)?(?:const|function)\s+(\w+)\s*[=:]\s*(?:\([^)]*\)|[^=])*=>\s*(?:\(|\{)?[^}]*(?:return\s+)?<",
                    content,
                    re.MULTILINE,
                )

                for name in func_matches:
                    if name[0].isupper():  # React components start with capital
                        self.ui_components.append(
                            UIComponent(
                                name=name,
                                file_path=str(path.relative_to(self.repo_path)),
                                component_type=self._guess_component_type(path, name),
                                framework="react",
                            )
                        )

                # Class components
                class_matches = re.findall(
                    r"class\s+(\w+)\s+extends\s+(?:React\.)?Component",
                    content,
                )

                for name in class_matches:
                    self.ui_components.append(
                        UIComponent(
                            name=name,
                            file_path=str(path.relative_to(self.repo_path)),
                            component_type=self._guess_component_type(path, name),
                            framework="react",
                        )
                    )

    def _guess_component_type(self, path: Path, name: str) -> ComponentType:
        """Guess component type from path and name."""
        path_str = str(path).lower()
        name_lower = name.lower()

        if "page" in path_str or "page" in name_lower:
            return ComponentType.PAGE
        if "layout" in path_str or "layout" in name_lower:
            return ComponentType.LAYOUT
        if "hook" in path_str or name_lower.startswith("use"):
            return ComponentType.HOOK
        if "context" in path_str or "context" in name_lower:
            return ComponentType.CONTEXT
        if "store" in path_str or "store" in name_lower:
            return ComponentType.STORE
        if "util" in path_str or "helper" in path_str:
            return ComponentType.UTILITY
        if "service" in path_str:
            return ComponentType.SERVICE

        return ComponentType.COMPONENT

    async def _find_ui_routes(self) -> None:
        """Find UI routes/pages."""
        # Next.js pages
        pages_dir = self.repo_path / "pages"
        app_dir = self.repo_path / "app"
        src_pages = self.repo_path / "src" / "pages"
        src_app = self.repo_path / "src" / "app"

        for route_dir in [pages_dir, app_dir, src_pages, src_app]:
            if route_dir.exists():
                await self._find_nextjs_routes(route_dir)

        # React Router routes
        await self._find_react_router_routes()

    async def _find_nextjs_routes(self, route_dir: Path) -> None:
        """Find Next.js file-based routes."""
        for path in route_dir.rglob("*"):
            if path.is_file() and path.suffix in [".tsx", ".jsx", ".ts", ".js"]:
                if path.name.startswith("_") or path.name.startswith("."):
                    continue

                rel_path = path.relative_to(route_dir)
                route_path = "/" + str(rel_path.with_suffix("")).replace("\\", "/")

                # Handle index routes
                if route_path.endswith("/index"):
                    route_path = route_path[:-6] or "/"

                # Handle dynamic routes
                route_path = route_path.replace("[", ":").replace("]", "")

                self.ui_routes.append(
                    UIRoute(
                        path=route_path,
                        component=path.stem,
                        file_path=str(path.relative_to(self.repo_path)),
                    )
                )

    async def _find_react_router_routes(self) -> None:
        """Find React Router route definitions."""
        import re

        for ext in ["*.tsx", "*.jsx", "*.ts", "*.js"]:
            for path in self.repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")

                # Look for Route components
                route_matches = re.findall(
                    r'<Route[^>]*path=["\']([^"\']+)["\'][^>]*(?:component|element)=[{"\']?(\w+)',
                    content,
                )

                for route_path, component in route_matches:
                    self.ui_routes.append(
                        UIRoute(
                            path=route_path,
                            component=component,
                            file_path=str(path.relative_to(self.repo_path)),
                        )
                    )

    async def _find_db_schemas(self) -> None:
        """Find database schema definitions."""
        # SQLAlchemy models
        await self._find_sqlalchemy_models()

        # Prisma schema
        await self._find_prisma_schema()

        # Django models
        await self._find_django_models()

    async def _find_sqlalchemy_models(self) -> None:
        """Find SQLAlchemy model definitions."""
        import re

        for path in self.repo_path.rglob("*.py"):
            if self._is_ignored(path):
                continue

            content = path.read_text(errors="ignore")

            # Look for SQLAlchemy model classes
            class_matches = re.findall(
                r"class\s+(\w+)\s*\([^)]*(?:Base|Model|db\.Model)[^)]*\)",
                content,
            )

            for name in class_matches:
                # Try to find table name
                table_match = re.search(rf"__tablename__\s*=\s*['\"](\w+)['\"]", content)
                table_name = table_match.group(1) if table_match else name.lower()

                self.db_schemas.append(
                    DBSchema(
                        name=name,
                        file_path=str(path.relative_to(self.repo_path)),
                        table_name=table_name,
                    )
                )

    async def _find_prisma_schema(self) -> None:
        """Find Prisma schema models."""
        import re

        for path in self.repo_path.rglob("schema.prisma"):
            if self._is_ignored(path):
                continue

            content = path.read_text(errors="ignore")

            model_matches = re.findall(r"model\s+(\w+)\s*\{", content)

            for name in model_matches:
                self.db_schemas.append(
                    DBSchema(
                        name=name,
                        file_path=str(path.relative_to(self.repo_path)),
                        table_name=name,
                    )
                )

    async def _find_django_models(self) -> None:
        """Find Django model definitions."""
        import re

        for path in self.repo_path.rglob("models.py"):
            if self._is_ignored(path):
                continue

            content = path.read_text(errors="ignore")

            class_matches = re.findall(
                r"class\s+(\w+)\s*\([^)]*models\.Model[^)]*\)",
                content,
            )

            for name in class_matches:
                self.db_schemas.append(
                    DBSchema(
                        name=name,
                        file_path=str(path.relative_to(self.repo_path)),
                        table_name=name.lower(),
                    )
                )

    async def _find_config_contracts(self) -> None:
        """Find environment and config contracts."""
        # .env files
        for env_file in [".env", ".env.example", ".env.local", ".env.development"]:
            env_path = self.repo_path / env_file
            if env_path.exists():
                await self._parse_env_file(env_path)

        # Look for config loading in code
        await self._find_config_usage()

    async def _parse_env_file(self, path: Path) -> None:
        """Parse .env file for config contracts."""
        content = path.read_text(errors="ignore")

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                self.config_contracts.append(
                    ConfigContract(
                        name=key,
                        source=str(path.relative_to(self.repo_path)),
                        required=".example" not in str(path),
                        default_value=value if value else None,
                    )
                )

    async def _find_config_usage(self) -> None:
        """Find config/env usage in code."""
        import re

        patterns = [
            r'os\.(?:environ|getenv)\s*\[\s*["\'](\w+)',
            r'os\.(?:environ|getenv)\s*\(\s*["\'](\w+)',
            r'process\.env\.(\w+)',
            r'env\s*\.\s*(\w+)',
            r'config\s*\[\s*["\'](\w+)',
        ]

        found_keys: set[str] = set()

        for ext in ["*.py", "*.ts", "*.js"]:
            for path in self.repo_path.rglob(ext):
                if self._is_ignored(path):
                    continue

                content = path.read_text(errors="ignore")

                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match not in found_keys:
                            found_keys.add(match)
                            # Check if already defined in .env
                            existing = next(
                                (c for c in self.config_contracts if c.name == match),
                                None,
                            )
                            if not existing:
                                self.config_contracts.append(
                                    ConfigContract(
                                        name=match,
                                        source=str(path.relative_to(self.repo_path)),
                                        required=True,
                                    )
                                )

    async def _find_integrations(self) -> None:
        """Find external integrations."""
        # Look for common integration patterns
        integrations_patterns = {
            "aws": ["boto3", "aws-sdk", "@aws-sdk"],
            "firebase": ["firebase", "firebase-admin"],
            "stripe": ["stripe"],
            "sendgrid": ["sendgrid", "@sendgrid"],
            "twilio": ["twilio"],
            "postgres": ["psycopg", "pg", "postgres"],
            "mongodb": ["pymongo", "mongodb", "mongoose"],
            "redis": ["redis", "ioredis"],
            "elasticsearch": ["elasticsearch"],
            "rabbitmq": ["pika", "amqplib"],
            "kafka": ["kafka", "kafkajs"],
            "graphql": ["graphql", "apollo"],
        }

        # Check package manifests
        for key, manifest_path in self.manifests.items():
            try:
                if "npm" in key:
                    with open(manifest_path) as f:
                        pkg = json.load(f)
                        deps = {
                            **pkg.get("dependencies", {}),
                            **pkg.get("devDependencies", {}),
                        }
                        for int_name, patterns in integrations_patterns.items():
                            for pattern in patterns:
                                if any(pattern in dep for dep in deps):
                                    self.external_integrations.append(
                                        ExternalIntegration(
                                            name=int_name,
                                            integration_type="package",
                                            file_paths=[str(manifest_path)],
                                        )
                                    )
                                    break

                elif "pyproject" in key or "pip" in key:
                    content = manifest_path.read_text()
                    for int_name, patterns in integrations_patterns.items():
                        for pattern in patterns:
                            if pattern in content.lower():
                                self.external_integrations.append(
                                    ExternalIntegration(
                                        name=int_name,
                                        integration_type="package",
                                        file_paths=[str(manifest_path)],
                                    )
                                )
                                break
            except (json.JSONDecodeError, OSError):
                continue

    async def _build_call_graph(self) -> None:
        """Build call graph for reachability analysis."""
        # This is a simplified implementation
        # A full implementation would use tree-sitter for precise AST parsing

        for entry in self.entry_points:
            self.call_graph.add_node(
                entry.file_path,
                node_type="entry_point",
                name=entry.name,
            )

        for route in self.api_routes:
            node_id = f"{route.handler_file}:{route.handler_function}"
            self.call_graph.add_node(
                node_id,
                node_type="route_handler",
                method=route.method,
                path=route.path,
            )

        for component in self.ui_components:
            node_id = f"{component.file_path}:{component.name}"
            self.call_graph.add_node(
                node_id,
                node_type="component",
                component_type=component.component_type.value,
            )

    def get_unreachable_nodes(self) -> list[str]:
        """Get nodes that are not reachable from any entry point."""
        if not self.call_graph.nodes():
            return []

        # Find all entry point nodes
        entry_nodes = [
            n for n, d in self.call_graph.nodes(data=True) if d.get("node_type") == "entry_point"
        ]

        if not entry_nodes:
            return list(self.call_graph.nodes())

        # Find all reachable nodes
        reachable: set[str] = set()
        for entry in entry_nodes:
            reachable.update(nx.descendants(self.call_graph, entry))
            reachable.add(entry)

        # Return unreachable nodes
        return [n for n in self.call_graph.nodes() if n not in reachable]

    def _is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored."""
        ignore_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".pytest_cache",
            ".mypy_cache",
        ]

        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)

    def _to_dict(self) -> dict[str, Any]:
        """Convert inventory to dictionary."""
        return {
            "repo_path": str(self.repo_path),
            "languages": [lang.value for lang in self.languages],
            "manifests": {k: str(v) for k, v in self.manifests.items()},
            "entry_points": [ep.model_dump() for ep in self.entry_points],
            "modules": [m.model_dump() for m in self.modules],
            "api_routes": [r.model_dump() for r in self.api_routes],
            "ui_components": [c.model_dump() for c in self.ui_components],
            "ui_routes": [r.model_dump() for r in self.ui_routes],
            "db_schemas": [s.model_dump() for s in self.db_schemas],
            "config_contracts": [c.model_dump() for c in self.config_contracts],
            "external_integrations": [i.model_dump() for i in self.external_integrations],
            "call_graph": {
                "nodes": len(self.call_graph.nodes()),
                "edges": len(self.call_graph.edges()),
                "unreachable": self.get_unreachable_nodes(),
            },
            "summary": {
                "total_entry_points": len(self.entry_points),
                "total_api_routes": len(self.api_routes),
                "total_ui_components": len(self.ui_components),
                "total_ui_routes": len(self.ui_routes),
                "total_db_schemas": len(self.db_schemas),
                "total_config_keys": len(self.config_contracts),
                "total_integrations": len(self.external_integrations),
            },
        }
