"""
Language Truth Profile Loader

Loads profiles from YAML files and Python definitions.
"""

from pathlib import Path
from typing import Any

import yaml

from .schema import LanguageTruthProfile
from .registry import ProfileRegistry, get_registry


def load_profile(path: Path) -> LanguageTruthProfile:
    """Load a single profile from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    return LanguageTruthProfile.from_dict(data)


def load_all_profiles(
    directory: Path | None = None,
    registry: ProfileRegistry | None = None,
) -> ProfileRegistry:
    """
    Load all profiles from a directory into a registry.

    If no directory specified, loads built-in profiles.
    """
    if registry is None:
        registry = get_registry()

    if directory is None:
        # Load built-in profiles
        from . import builtin
        builtin.register_all(registry)
    else:
        # Load from directory
        for yaml_file in directory.glob("*.yaml"):
            try:
                profile = load_profile(yaml_file)
                registry.register(profile)
            except Exception as e:
                raise ValueError(f"Failed to load profile {yaml_file}: {e}")

    return registry


def save_profile(profile: LanguageTruthProfile, path: Path) -> None:
    """Save a profile to a YAML file."""
    data = profile.to_dict()

    # Convert enums to strings
    def convert_enums(obj: Any) -> Any:
        if hasattr(obj, "value"):
            return obj.value
        elif isinstance(obj, dict):
            return {k: convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(v) for v in obj]
        return obj

    data = convert_enums(data)

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
