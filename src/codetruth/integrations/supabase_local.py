"""
Supabase Local Integration

Provides integration with self-hosted Supabase for:
- Persistent audit data storage
- Real-time audit subscriptions
- Team collaboration features
- Historical audit tracking
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SupabaseConfig(BaseModel):
    """Configuration for local Supabase."""

    # Connection settings
    url: str = Field(default="http://localhost:54321")
    anon_key: str = Field(default="")
    service_role_key: str = Field(default="")

    # Database settings
    schema: str = Field(default="codetruth")

    # Features
    enable_realtime: bool = Field(default=True)
    enable_storage: bool = Field(default=True)


class SupabaseLocalClient:
    """
    Client for local Supabase instance.

    Supabase provides:
    - PostgreSQL database for structured audit data
    - Real-time subscriptions for live updates
    - Storage for evidence artifacts
    - Row-level security for team access

    Self-hosting is free and keeps all data local.
    """

    def __init__(self, config: SupabaseConfig | None = None):
        self.config = config or SupabaseConfig()
        self._client: Any = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Supabase client."""
        try:
            from supabase import create_client

            self._client = create_client(
                self.config.url,
                self.config.anon_key,
            )
            self._initialized = True

            # Initialize schema
            await self._init_schema()

            logger.info("Supabase local client initialized")
            return True

        except ImportError:
            logger.warning("Supabase client not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return False

    async def _init_schema(self) -> None:
        """Initialize database schema."""
        if not self._client:
            return

        # Schema will be created via migrations
        # This is a placeholder for schema verification
        pass

    async def store_audit_run(
        self,
        repo_path: str,
        audit_data: dict[str, Any],
    ) -> str | None:
        """
        Store an audit run.

        Args:
            repo_path: Repository path
            audit_data: Complete audit data

        Returns:
            Audit run ID if successful
        """
        if not self._initialized or not self._client:
            return None

        try:
            result = self._client.table("audit_runs").insert({
                "repo_path": repo_path,
                "profile": audit_data.get("profile", "standard"),
                "started_at": audit_data.get("started_at", datetime.utcnow().isoformat()),
                "completed_at": datetime.utcnow().isoformat(),
                "summary": json.dumps(audit_data.get("summary", {})),
                "gates_passed": audit_data.get("gates_passed", 0),
                "total_findings": audit_data.get("total_findings", 0),
                "critical_count": audit_data.get("critical", 0),
                "error_count": audit_data.get("errors", 0),
                "warning_count": audit_data.get("warnings", 0),
            }).execute()

            if result.data:
                return result.data[0].get("id")
            return None

        except Exception as e:
            logger.error(f"Failed to store audit run: {e}")
            return None

    async def store_findings(
        self,
        audit_run_id: str,
        findings: list[dict[str, Any]],
    ) -> int:
        """
        Store audit findings.

        Args:
            audit_run_id: Audit run ID
            findings: List of findings

        Returns:
            Number of findings stored
        """
        if not self._initialized or not self._client:
            return 0

        stored = 0

        try:
            for finding in findings:
                self._client.table("findings").insert({
                    "audit_run_id": audit_run_id,
                    "evidence_type": finding.get("type"),
                    "severity": finding.get("severity"),
                    "message": finding.get("message"),
                    "file_path": finding.get("file"),
                    "line_number": finding.get("line"),
                    "rule_id": finding.get("rule_id"),
                    "tool_name": finding.get("tool"),
                    "raw_data": json.dumps(finding),
                }).execute()
                stored += 1

            return stored

        except Exception as e:
            logger.error(f"Failed to store findings: {e}")
            return stored

    async def store_truth_table(
        self,
        audit_run_id: str,
        truth_table: dict[str, Any],
    ) -> bool:
        """
        Store feature truth table.

        Args:
            audit_run_id: Audit run ID
            truth_table: Truth table data

        Returns:
            True if successful
        """
        if not self._initialized or not self._client:
            return False

        try:
            features = truth_table.get("features", [])

            for feature in features:
                self._client.table("features").insert({
                    "audit_run_id": audit_run_id,
                    "name": feature.get("name"),
                    "feature_type": feature.get("feature_type"),
                    "status": feature.get("status"),
                    "is_reachable": feature.get("is_reachable"),
                    "is_wired": feature.get("is_wired"),
                    "is_tested": feature.get("is_tested"),
                    "blockers": json.dumps(feature.get("blockers", [])),
                }).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to store truth table: {e}")
            return False

    async def get_audit_history(
        self,
        repo_path: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get audit history for a repository.

        Args:
            repo_path: Repository path
            limit: Maximum results

        Returns:
            List of audit runs
        """
        if not self._initialized or not self._client:
            return []

        try:
            result = self._client.table("audit_runs").select("*").eq(
                "repo_path", repo_path
            ).order("completed_at", desc=True).limit(limit).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get audit history: {e}")
            return []

    async def get_findings_trend(
        self,
        repo_path: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get findings trend over time.

        Args:
            repo_path: Repository path
            days: Number of days to look back

        Returns:
            Trend data with daily counts
        """
        if not self._initialized or not self._client:
            return {"dates": [], "critical": [], "errors": [], "warnings": []}

        try:
            # This would use a more sophisticated query in practice
            history = await self.get_audit_history(repo_path, limit=days)

            trend: dict[str, Any] = {
                "dates": [],
                "critical": [],
                "errors": [],
                "warnings": [],
            }

            for audit in reversed(history):
                trend["dates"].append(audit.get("completed_at", "")[:10])
                trend["critical"].append(audit.get("critical_count", 0))
                trend["errors"].append(audit.get("error_count", 0))
                trend["warnings"].append(audit.get("warning_count", 0))

            return trend

        except Exception as e:
            logger.error(f"Failed to get findings trend: {e}")
            return {"dates": [], "critical": [], "errors": [], "warnings": []}

    async def upload_evidence(
        self,
        audit_run_id: str,
        file_path: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str | None:
        """
        Upload evidence artifact to storage.

        Args:
            audit_run_id: Audit run ID
            file_path: Path for the file in storage
            file_data: File content
            content_type: MIME type

        Returns:
            Public URL if successful
        """
        if not self._initialized or not self._client or not self.config.enable_storage:
            return None

        try:
            storage_path = f"evidence/{audit_run_id}/{file_path}"

            result = self._client.storage.from_("codetruth").upload(
                storage_path,
                file_data,
                {"content-type": content_type},
            )

            if result:
                return self._client.storage.from_("codetruth").get_public_url(storage_path)
            return None

        except Exception as e:
            logger.error(f"Failed to upload evidence: {e}")
            return None

    async def subscribe_to_audit(
        self,
        audit_run_id: str,
        on_update: Any,
    ) -> None:
        """
        Subscribe to real-time audit updates.

        Args:
            audit_run_id: Audit run ID
            on_update: Callback for updates
        """
        if not self._initialized or not self._client or not self.config.enable_realtime:
            return

        try:
            self._client.channel(f"audit:{audit_run_id}").on(
                "UPDATE",
                lambda payload: on_update(payload),
            ).subscribe()

        except Exception as e:
            logger.error(f"Failed to subscribe to audit: {e}")
