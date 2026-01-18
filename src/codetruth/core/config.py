"""
CodeTruth Configuration Management

Handles all configuration for the audit server including:
- Database paths
- Analyzer settings
- Quality gate thresholds
- Tool integrations
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class GateConfig(BaseModel):
    """Configuration for quality gates."""

    enabled: list[int] = Field(default=[0, 1, 2, 3, 4, 5, 6])
    fail_fast: bool = Field(default=False, description="Stop on first gate failure")

    # Gate-specific thresholds
    coverage_threshold: float = Field(default=80.0, description="Minimum test coverage %")
    lint_error_threshold: int = Field(default=0, description="Max lint errors allowed")
    type_error_threshold: int = Field(default=0, description="Max type errors allowed")
    security_critical_threshold: int = Field(default=0, description="Max critical vulns")


class PythonConfig(BaseModel):
    """Python-specific analyzer configuration."""

    enabled: bool = True
    type_checker: str = Field(default="mypy", description="Type checker: mypy, pyright")
    linter: str = Field(default="ruff", description="Linter: ruff, flake8, pylint")
    formatter: str = Field(default="black", description="Formatter: black, ruff")
    min_python_version: str = Field(default="3.11")


class TypeScriptConfig(BaseModel):
    """TypeScript/JavaScript-specific analyzer configuration."""

    enabled: bool = True
    strict: bool = True
    linter: str = Field(default="eslint", description="Linter: eslint, biome")
    formatter: str = Field(default="prettier", description="Formatter: prettier, biome")


class ReactConfig(BaseModel):
    """React-specific analyzer configuration."""

    enabled: bool = True
    check_hooks_rules: bool = True
    check_prop_types: bool = True
    check_accessibility: bool = True


class SecurityConfig(BaseModel):
    """Security scanning configuration."""

    gitleaks_enabled: bool = True
    trufflehog_enabled: bool = False
    trufflehog_verify: bool = Field(default=False, description="Verify if secrets are live")

    semgrep_enabled: bool = True
    semgrep_rulesets: list[str] = Field(
        default=["p/default", "p/owasp-top-ten", "p/security-audit"]
    )

    dependency_scan_enabled: bool = True
    osv_enabled: bool = True
    trivy_enabled: bool = False


class E2EConfig(BaseModel):
    """E2E testing configuration."""

    enabled: bool = True
    browser: str = Field(default="chromium", description="Browser: chromium, firefox, webkit")
    headless: bool = True
    trace: str = Field(default="on-first-retry", description="Trace mode")
    video: str = Field(default="retain-on-failure", description="Video recording mode")
    screenshot: str = Field(default="only-on-failure", description="Screenshot mode")
    timeout: int = Field(default=30000, description="Default timeout in ms")


class DockerConfig(BaseModel):
    """Docker sandbox configuration."""

    enabled: bool = True
    image: str = Field(default="codetruth-sandbox:latest")
    memory_limit: str = Field(default="2g")
    cpu_limit: float = Field(default=2.0)
    timeout: int = Field(default=600, description="Max execution time in seconds")
    network_mode: str = Field(default="none", description="Network isolation")


class StorageConfig(BaseModel):
    """Storage configuration."""

    # SQLite Evidence Vault
    sqlite_enabled: bool = True
    sqlite_path: Path = Field(default=Path.home() / ".codetruth" / "evidence.db")

    # Supabase (optional)
    supabase_enabled: bool = False
    supabase_url: str | None = None
    supabase_key: str | None = None

    # Mem0 AI Memory
    mem0_enabled: bool = True
    mem0_api_key: str | None = None


class AnalyzersConfig(BaseModel):
    """All analyzer configurations."""

    python: PythonConfig = Field(default_factory=PythonConfig)
    typescript: TypeScriptConfig = Field(default_factory=TypeScriptConfig)
    react: ReactConfig = Field(default_factory=ReactConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    e2e: E2EConfig = Field(default_factory=E2EConfig)


class CodeTruthConfig(BaseSettings):
    """
    Main configuration for CodeTruth MCP Server.

    Loads from environment variables with CODETRUTH_ prefix,
    or from codetruth.toml in the project root.
    """

    model_config = {"env_prefix": "CODETRUTH_", "env_nested_delimiter": "__"}

    # Core settings
    profile: str = Field(
        default="standard",
        description="Default analysis profile: fast, standard, deep, forensics",
    )
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Paths
    db_path: Path = Field(
        default=Path.home() / ".codetruth" / "evidence.db",
        description="Path to evidence vault database",
    )
    cache_dir: Path = Field(
        default=Path.home() / ".codetruth" / "cache",
        description="Cache directory for analysis artifacts",
    )
    output_dir: Path = Field(
        default=Path.home() / ".codetruth" / "reports",
        description="Default output directory for reports",
    )

    # Component configs
    gates: GateConfig = Field(default_factory=GateConfig)
    analyzers: AnalyzersConfig = Field(default_factory=AnalyzersConfig)
    docker: DockerConfig = Field(default_factory=DockerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # Analysis profiles
    profiles: dict[str, dict[str, Any]] = Field(
        default={
            "fast": {
                "gates": [0, 1],
                "analyzers": ["lint", "type_check"],
                "e2e": False,
                "coverage": False,
            },
            "standard": {
                "gates": [0, 1, 2, 3, 4, 5],
                "analyzers": [
                    "lint",
                    "type_check",
                    "dead_code",
                    "ui_wiring",
                    "security",
                    "dependencies",
                ],
                "e2e": True,
                "coverage": True,
            },
            "deep": {
                "gates": [0, 1, 2, 3, 4, 5, 6],
                "analyzers": "all",
                "e2e": True,
                "coverage": True,
                "visual_regression": True,
            },
            "forensics": {
                "gates": [0, 1, 2, 3, 4, 5, 6],
                "analyzers": "all",
                "e2e": True,
                "e2e_trace": True,
                "e2e_video": True,
                "coverage": True,
                "visual_regression": True,
                "trace_correlation": True,
            },
        }
    )

    def get_profile_config(self, profile: str | None = None) -> dict[str, Any]:
        """Get configuration for a specific profile."""
        profile = profile or self.profile
        return self.profiles.get(profile, self.profiles["standard"])

    @classmethod
    def from_toml(cls, path: Path) -> "CodeTruthConfig":
        """Load configuration from a TOML file."""
        import toml

        if not path.exists():
            return cls()

        data = toml.load(path)
        config_data = data.get("codetruth", {})
        return cls(**config_data)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
