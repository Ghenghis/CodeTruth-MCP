"""
Repository Discovery and Detection

Scans directories for repositories and detects their characteristics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


async def discover_repositories(
    root_paths: list[str],
    exclude_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """
    Discover repositories in the given root paths.

    Args:
        root_paths: List of directory paths to scan
        exclude_patterns: Glob patterns to exclude

    Returns:
        Dictionary with discovered repositories and their metadata
    """
    exclude_patterns = exclude_patterns or [
        "**/node_modules",
        "**/.git",
        "**/venv",
        "**/__pycache__",
        "**/dist",
        "**/build",
    ]

    discovered: list[dict[str, Any]] = []

    for root_path in root_paths:
        root = Path(root_path).expanduser().resolve()

        if not root.exists():
            continue

        # Check if root itself is a repo
        if (root / ".git").exists():
            repo_info = await _analyze_repository(root)
            discovered.append(repo_info)
            continue

        # Scan for repos in subdirectories
        for path in root.iterdir():
            if not path.is_dir():
                continue

            # Skip excluded patterns
            if any(_matches_pattern(path, pattern) for pattern in exclude_patterns):
                continue

            if (path / ".git").exists():
                repo_info = await _analyze_repository(path)
                discovered.append(repo_info)

    return {
        "scanned_paths": root_paths,
        "repositories_found": len(discovered),
        "repositories": discovered,
    }


async def _analyze_repository(repo_path: Path) -> dict[str, Any]:
    """Analyze a repository and extract metadata."""
    info: dict[str, Any] = {
        "path": str(repo_path),
        "name": repo_path.name,
        "languages": [],
        "frameworks": [],
        "package_managers": [],
        "has_tests": False,
        "has_ci": False,
        "has_docker": False,
    }

    # Detect languages
    language_indicators = {
        "python": ["*.py", "pyproject.toml", "setup.py", "requirements.txt"],
        "typescript": ["*.ts", "*.tsx", "tsconfig.json"],
        "javascript": ["*.js", "*.jsx", "package.json"],
        "rust": ["*.rs", "Cargo.toml"],
        "go": ["*.go", "go.mod"],
        "java": ["*.java", "pom.xml", "build.gradle"],
        "csharp": ["*.cs", "*.csproj"],
        "ruby": ["*.rb", "Gemfile"],
        "php": ["*.php", "composer.json"],
    }

    for lang, patterns in language_indicators.items():
        for pattern in patterns:
            if list(repo_path.glob(pattern))[:1]:
                if lang not in info["languages"]:
                    info["languages"].append(lang)
                break

    # Detect frameworks
    if (repo_path / "package.json").exists():
        try:
            with open(repo_path / "package.json") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                framework_indicators = {
                    "react": ["react", "react-dom"],
                    "next": ["next"],
                    "vue": ["vue"],
                    "nuxt": ["nuxt"],
                    "angular": ["@angular/core"],
                    "svelte": ["svelte"],
                    "express": ["express"],
                    "fastify": ["fastify"],
                    "nest": ["@nestjs/core"],
                }

                for framework, indicators in framework_indicators.items():
                    if any(ind in deps for ind in indicators):
                        info["frameworks"].append(framework)

                info["package_managers"].append("npm")
        except (json.JSONDecodeError, OSError):
            pass

    if (repo_path / "pyproject.toml").exists():
        info["package_managers"].append("poetry/pip")

        # Check for Python frameworks
        try:
            content = (repo_path / "pyproject.toml").read_text()
            if "fastapi" in content.lower():
                info["frameworks"].append("fastapi")
            if "django" in content.lower():
                info["frameworks"].append("django")
            if "flask" in content.lower():
                info["frameworks"].append("flask")
        except:
            pass

    # Detect tests
    test_patterns = [
        "test_*.py",
        "*_test.py",
        "*.test.ts",
        "*.test.js",
        "*.spec.ts",
        "*.spec.js",
        "tests/**",
        "__tests__/**",
    ]

    for pattern in test_patterns:
        if list(repo_path.glob(pattern))[:1]:
            info["has_tests"] = True
            break

    # Detect CI
    ci_files = [
        ".github/workflows",
        ".gitlab-ci.yml",
        ".circleci",
        "Jenkinsfile",
        ".travis.yml",
        "azure-pipelines.yml",
    ]

    for ci_file in ci_files:
        if (repo_path / ci_file).exists():
            info["has_ci"] = True
            break

    # Detect Docker
    if (repo_path / "Dockerfile").exists() or (repo_path / "docker-compose.yml").exists():
        info["has_docker"] = True

    return info


def _matches_pattern(path: Path, pattern: str) -> bool:
    """Check if path matches a glob pattern."""
    import fnmatch

    path_str = str(path)
    pattern = pattern.replace("**", "*")  # Simplified matching
    return fnmatch.fnmatch(path_str, f"*{pattern}*")
