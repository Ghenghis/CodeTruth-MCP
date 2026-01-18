"""
Mem0 AI Memory Integration

Provides persistent memory for audit sessions using Mem0.
Remembers:
- Previous audit findings
- User preferences
- Fix patterns
- Codebase context
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Mem0Config(BaseModel):
    """Configuration for Mem0 integration."""

    # API settings
    api_key: str | None = Field(default=None)
    base_url: str = Field(default="https://api.mem0.ai")

    # Local settings (for open-source self-hosted)
    use_local: bool = Field(default=True)
    local_db_path: str = Field(default="~/.codetruth/mem0.db")

    # Memory settings
    user_id: str = Field(default="codetruth-default")
    agent_id: str = Field(default="codetruth-auditor")


class Mem0Integration:
    """
    Integration with Mem0 for AI memory.

    Mem0 provides a memory layer for AI applications,
    enabling context persistence across sessions.

    Uses:
    - Remember audit history for a repo
    - Track fix patterns and user preferences
    - Provide contextual suggestions based on past audits
    - Remember codebase architecture insights
    """

    def __init__(self, config: Mem0Config | None = None):
        self.config = config or Mem0Config()
        self._client: Any = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Mem0 client."""
        try:
            if self.config.use_local:
                # Use local Mem0 (open-source version)
                from mem0 import Memory

                self._client = Memory()
                self._initialized = True
                logger.info("Mem0 initialized with local storage")
                return True
            else:
                # Use Mem0 API
                if not self.config.api_key:
                    logger.warning("Mem0 API key not provided")
                    return False

                from mem0 import MemoryClient

                self._client = MemoryClient(api_key=self.config.api_key)
                self._initialized = True
                logger.info("Mem0 initialized with API")
                return True

        except ImportError as e:
            logger.warning(f"Mem0 not installed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            return False

    async def add_audit_memory(
        self,
        repo_path: str,
        audit_summary: dict[str, Any],
        findings: list[dict[str, Any]],
    ) -> str | None:
        """
        Store memory of an audit run.

        Args:
            repo_path: Repository path
            audit_summary: Audit summary data
            findings: List of findings

        Returns:
            Memory ID if successful
        """
        if not self._initialized:
            await self.initialize()

        if not self._client:
            return None

        # Prepare memory content
        content = f"""Audit of repository: {repo_path}
Date: {datetime.utcnow().isoformat()}

Summary:
- Total findings: {audit_summary.get('total_findings', 0)}
- Critical: {audit_summary.get('critical', 0)}
- Errors: {audit_summary.get('errors', 0)}
- Warnings: {audit_summary.get('warnings', 0)}

Key findings:
"""
        for finding in findings[:10]:  # Top 10 findings
            content += f"- [{finding.get('severity', 'info')}] {finding.get('message', 'Unknown')}\n"

        try:
            result = self._client.add(
                content,
                user_id=self.config.user_id,
                agent_id=self.config.agent_id,
                metadata={
                    "type": "audit",
                    "repo_path": repo_path,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return result.get("id") if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error(f"Failed to add audit memory: {e}")
            return None

    async def add_fix_pattern(
        self,
        finding_type: str,
        before_code: str,
        after_code: str,
        language: str,
    ) -> str | None:
        """
        Remember a successful fix pattern.

        Args:
            finding_type: Type of finding that was fixed
            before_code: Code before fix
            after_code: Code after fix
            language: Programming language

        Returns:
            Memory ID if successful
        """
        if not self._initialized:
            await self.initialize()

        if not self._client:
            return None

        content = f"""Fix pattern for: {finding_type}
Language: {language}

Before:
```{language}
{before_code}
```

After:
```{language}
{after_code}
```
"""

        try:
            result = self._client.add(
                content,
                user_id=self.config.user_id,
                agent_id=self.config.agent_id,
                metadata={
                    "type": "fix_pattern",
                    "finding_type": finding_type,
                    "language": language,
                },
            )
            return result.get("id") if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error(f"Failed to add fix pattern: {e}")
            return None

    async def add_codebase_insight(
        self,
        repo_path: str,
        insight_type: str,
        insight: str,
    ) -> str | None:
        """
        Store an insight about a codebase.

        Args:
            repo_path: Repository path
            insight_type: Type of insight (architecture, patterns, etc.)
            insight: The insight text

        Returns:
            Memory ID if successful
        """
        if not self._initialized:
            await self.initialize()

        if not self._client:
            return None

        content = f"""Codebase insight for: {repo_path}
Type: {insight_type}

{insight}
"""

        try:
            result = self._client.add(
                content,
                user_id=self.config.user_id,
                agent_id=self.config.agent_id,
                metadata={
                    "type": "codebase_insight",
                    "repo_path": repo_path,
                    "insight_type": insight_type,
                },
            )
            return result.get("id") if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error(f"Failed to add codebase insight: {e}")
            return None

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        memory_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search memories.

        Args:
            query: Search query
            limit: Maximum results
            memory_type: Filter by memory type

        Returns:
            List of matching memories
        """
        if not self._initialized:
            await self.initialize()

        if not self._client:
            return []

        try:
            results = self._client.search(
                query,
                user_id=self.config.user_id,
                agent_id=self.config.agent_id,
                limit=limit,
            )

            memories = results if isinstance(results, list) else results.get("results", [])

            # Filter by type if specified
            if memory_type:
                memories = [
                    m for m in memories
                    if m.get("metadata", {}).get("type") == memory_type
                ]

            return memories

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_repo_context(
        self,
        repo_path: str,
    ) -> dict[str, Any]:
        """
        Get all remembered context for a repository.

        Args:
            repo_path: Repository path

        Returns:
            Context including past audits, insights, and patterns
        """
        context: dict[str, Any] = {
            "repo_path": repo_path,
            "past_audits": [],
            "insights": [],
            "fix_patterns": [],
        }

        # Search for past audits
        audits = await self.search_memories(
            f"audit {repo_path}",
            limit=5,
            memory_type="audit",
        )
        context["past_audits"] = audits

        # Search for insights
        insights = await self.search_memories(
            f"insight {repo_path}",
            limit=10,
            memory_type="codebase_insight",
        )
        context["insights"] = insights

        # Get fix patterns
        patterns = await self.search_memories(
            "fix pattern",
            limit=20,
            memory_type="fix_pattern",
        )
        context["fix_patterns"] = patterns

        return context

    async def get_similar_fixes(
        self,
        finding: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Find similar fixes from memory.

        Args:
            finding: The finding to find fixes for

        Returns:
            List of similar fix patterns
        """
        query = f"fix {finding.get('type', '')} {finding.get('message', '')}"

        return await self.search_memories(
            query,
            limit=5,
            memory_type="fix_pattern",
        )

    async def clear_repo_memories(self, repo_path: str) -> bool:
        """
        Clear all memories for a repository.

        Args:
            repo_path: Repository path

        Returns:
            True if successful
        """
        if not self._initialized:
            await self.initialize()

        if not self._client:
            return False

        try:
            # Search and delete
            memories = await self.search_memories(repo_path, limit=100)

            for memory in memories:
                memory_id = memory.get("id")
                if memory_id:
                    self._client.delete(memory_id)

            return True

        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False
