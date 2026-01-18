"""
Built-in Language Truth Profiles

These are the core profiles that ship with CodeTruth.
Each profile is rigorously defined with honest capability claims.
"""

from ..registry import ProfileRegistry

from .typescript_react import TYPESCRIPT_REACT_PROFILE
from .typescript import TYPESCRIPT_PROFILE
from .javascript import JAVASCRIPT_PROFILE
from .python import PYTHON_PROFILE
from .html import HTML_PROFILE
from .css import CSS_PROFILE
from .sql import SQL_PROFILE
from .dockerfile import DOCKERFILE_PROFILE
from .yaml_profile import YAML_PROFILE
from .json_profile import JSON_PROFILE
from .shell import SHELL_PROFILE
from .rust import RUST_PROFILE
from .go import GO_PROFILE


ALL_PROFILES = [
    TYPESCRIPT_REACT_PROFILE,
    TYPESCRIPT_PROFILE,
    JAVASCRIPT_PROFILE,
    PYTHON_PROFILE,
    HTML_PROFILE,
    CSS_PROFILE,
    SQL_PROFILE,
    DOCKERFILE_PROFILE,
    YAML_PROFILE,
    JSON_PROFILE,
    SHELL_PROFILE,
    RUST_PROFILE,
    GO_PROFILE,
]


def register_all(registry: ProfileRegistry) -> None:
    """Register all built-in profiles."""
    for profile in ALL_PROFILES:
        registry.register(profile)
