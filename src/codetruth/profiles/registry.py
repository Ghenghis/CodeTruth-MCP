"""
Language Truth Profile Registry

Central registry for all Language Truth Profiles.
Provides lookup, validation, and completeness checking.
"""

from pathlib import Path
from typing import Iterator

from .schema import LanguageTruthProfile, ProofLevel


class ProfileRegistry:
    """
    Registry for Language Truth Profiles.

    The registry enforces:
    1. All profiles must be complete (no undefined capabilities)
    2. All profiles must declare their blindspots
    3. Proof levels must be honest (no overclaiming)
    """

    def __init__(self) -> None:
        self._profiles: dict[str, LanguageTruthProfile] = {}
        self._file_extension_map: dict[str, list[str]] = {}

    def register(self, profile: LanguageTruthProfile) -> None:
        """
        Register a Language Truth Profile.

        Raises:
            ValueError: If profile is incomplete or invalid
        """
        # Validate profile completeness
        self._validate_profile(profile)

        self._profiles[profile.language_id] = profile

        # Build extension map
        for ext in profile.file_extensions:
            if ext not in self._file_extension_map:
                self._file_extension_map[ext] = []
            self._file_extension_map[ext].append(profile.language_id)

    def _validate_profile(self, profile: LanguageTruthProfile) -> None:
        """Validate a profile meets minimum requirements."""
        errors = []

        # Must have parse capability
        if profile.parse is None:
            errors.append(f"{profile.language_id}: Missing parse capability")

        # Must have at least one evidence artifact
        if not profile.evidence_artifacts:
            errors.append(f"{profile.language_id}: No evidence artifacts defined")

        # Must declare blindspots (honest systems admit limits)
        if not profile.blindspots:
            errors.append(
                f"{profile.language_id}: No blindspots declared. "
                "All languages have blindspots - declare them honestly."
            )

        # If claiming wiring capability, must have proof level
        if profile.wiring and profile.wiring.can_prove_unreachable:
            if profile.wiring.unreachability_proof_level == ProofLevel.IMPOSSIBLE:
                errors.append(
                    f"{profile.language_id}: Claims can_prove_unreachable but "
                    "unreachability_proof_level is IMPOSSIBLE"
                )

        # Profile completeness must be declared
        if profile.profile_completeness == 0.0:
            errors.append(
                f"{profile.language_id}: profile_completeness not set. "
                "Must honestly declare how complete the profile is."
            )

        if errors:
            raise ValueError(
                f"Invalid Language Truth Profile:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    def get(self, language_id: str) -> LanguageTruthProfile | None:
        """Get a profile by language ID."""
        return self._profiles.get(language_id)

    def get_for_file(self, file_path: Path | str) -> list[LanguageTruthProfile]:
        """Get all profiles that apply to a file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        ext = file_path.suffix.lstrip(".")
        language_ids = self._file_extension_map.get(ext, [])

        # Also check patterns
        results = []
        for profile in self._profiles.values():
            if ext in [e.lstrip(".") for e in profile.file_extensions]:
                if profile not in results:
                    results.append(profile)
            else:
                # Check glob patterns
                import fnmatch
                for pattern in profile.file_patterns:
                    if fnmatch.fnmatch(str(file_path), pattern):
                        if profile not in results:
                            results.append(profile)
                        break

        return results

    def list_all(self) -> list[LanguageTruthProfile]:
        """List all registered profiles."""
        return list(self._profiles.values())

    def list_by_tier(self, tier: int) -> list[LanguageTruthProfile]:
        """List profiles by stack tier."""
        return [p for p in self._profiles.values() if p.stack_tier == tier]

    def get_coverage_summary(self) -> dict:
        """Get a summary of what the registry can and cannot prove."""
        summary = {
            "total_profiles": len(self._profiles),
            "by_tier": {},
            "by_proof_level": {},
            "total_blindspots": 0,
            "critical_blindspots": 0,
            "can_prove_completeness": [],
            "cannot_prove_completeness": [],
        }

        for tier in range(1, 6):
            tier_profiles = self.list_by_tier(tier)
            summary["by_tier"][tier] = {
                "count": len(tier_profiles),
                "languages": [p.language_id for p in tier_profiles],
            }

        proof_level_counts: dict[str, int] = {}
        for profile in self._profiles.values():
            level = profile.get_overall_proof_level().value
            proof_level_counts[level] = proof_level_counts.get(level, 0) + 1

            summary["total_blindspots"] += len(profile.blindspots)
            summary["critical_blindspots"] += len(profile.get_critical_blindspots())

            if profile.can_prove_completeness():
                summary["can_prove_completeness"].append(profile.language_id)
            else:
                summary["cannot_prove_completeness"].append(profile.language_id)

        summary["by_proof_level"] = proof_level_counts

        return summary

    def __iter__(self) -> Iterator[LanguageTruthProfile]:
        return iter(self._profiles.values())

    def __len__(self) -> int:
        return len(self._profiles)

    def __contains__(self, language_id: str) -> bool:
        return language_id in self._profiles


# Global registry instance
_global_registry: ProfileRegistry | None = None


def get_registry() -> ProfileRegistry:
    """Get the global profile registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ProfileRegistry()
    return _global_registry


def get_profile(language_id: str) -> LanguageTruthProfile | None:
    """Get a profile from the global registry."""
    return get_registry().get(language_id)


def list_profiles() -> list[LanguageTruthProfile]:
    """List all profiles in the global registry."""
    return get_registry().list_all()
