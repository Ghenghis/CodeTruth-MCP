"""
Windsurf IDE Integration

Provides seamless integration with Windsurf IDE including:
- MCP server configuration
- Audit folder generation in project
- Real-time notifications
- Inline diagnostics
- Quick fix suggestions
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WindsurfConfig(BaseModel):
    """Configuration for Windsurf IDE integration."""

    # MCP settings
    server_name: str = Field(default="codetruth-mcp")
    auto_start: bool = Field(default=True)

    # Audit folder settings
    audit_folder_name: str = Field(default=".codetruth")
    create_audit_folder: bool = Field(default=True)
    include_diagrams: bool = Field(default=True)
    include_evidence: bool = Field(default=True)

    # Diagnostics settings
    show_inline_diagnostics: bool = Field(default=True)
    diagnostic_severity_threshold: str = Field(default="warning")

    # Notifications
    show_notifications: bool = Field(default=True)
    notification_level: str = Field(default="info")


class WindsurfIntegration:
    """
    Integration with Windsurf IDE.

    Windsurf uses MCP for AI assistant integration.
    This class provides helpers for:
    - Generating MCP configuration
    - Creating IDE-friendly audit folders
    - Formatting findings for IDE display
    - Managing workspace settings
    """

    def __init__(self, config: WindsurfConfig | None = None):
        self.config = config or WindsurfConfig()

    def generate_mcp_config(self) -> dict[str, Any]:
        """
        Generate MCP server configuration for Windsurf.

        Returns configuration to add to Windsurf's MCP settings.
        """
        return {
            "mcpServers": {
                self.config.server_name: {
                    "command": "codetruth",
                    "args": ["serve"],
                    "env": {
                        "CODETRUTH_PROFILE": "standard",
                        "CODETRUTH_LOG_LEVEL": "INFO",
                    },
                }
            }
        }

    def generate_windsurf_settings(self, workspace_path: Path) -> dict[str, Any]:
        """
        Generate Windsurf workspace settings.

        Args:
            workspace_path: Path to the workspace

        Returns:
            Settings dictionary for .windsurf/settings.json
        """
        return {
            "codetruth": {
                "enabled": True,
                "auditFolder": self.config.audit_folder_name,
                "autoAudit": False,
                "diagrams": {
                    "enabled": self.config.include_diagrams,
                    "types": ["architecture", "call-graph", "ui-flow"],
                },
                "diagnostics": {
                    "enabled": self.config.show_inline_diagnostics,
                    "severity": self.config.diagnostic_severity_threshold,
                },
                "notifications": {
                    "enabled": self.config.show_notifications,
                    "level": self.config.notification_level,
                },
            }
        }

    async def setup_workspace(self, workspace_path: Path) -> dict[str, Any]:
        """
        Set up CodeTruth in a Windsurf workspace.

        Creates:
        - .windsurf/settings.json with CodeTruth config
        - .codetruth/ directory structure
        - Initial configuration files

        Args:
            workspace_path: Path to the workspace

        Returns:
            Setup result with created files
        """
        created_files = []

        # Create .windsurf directory
        windsurf_dir = workspace_path / ".windsurf"
        windsurf_dir.mkdir(exist_ok=True)

        # Generate and save settings
        settings_path = windsurf_dir / "settings.json"

        existing_settings = {}
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    existing_settings = json.load(f)
            except json.JSONDecodeError:
                pass

        # Merge with existing settings
        new_settings = self.generate_windsurf_settings(workspace_path)
        existing_settings.update(new_settings)

        with open(settings_path, "w") as f:
            json.dump(existing_settings, f, indent=2)

        created_files.append(str(settings_path))

        # Create .codetruth directory
        codetruth_dir = workspace_path / self.config.audit_folder_name
        codetruth_dir.mkdir(exist_ok=True)

        # Create .gitignore for codetruth folder
        gitignore_path = codetruth_dir / ".gitignore"
        gitignore_content = """# CodeTruth audit artifacts
audit-*/evidence/
audit-*/data/
*.log
"""
        gitignore_path.write_text(gitignore_content)
        created_files.append(str(gitignore_path))

        # Create README
        readme_path = codetruth_dir / "README.md"
        readme_content = f"""# CodeTruth Audit Folder

This folder contains audit reports generated by CodeTruth-MCP.

## Structure

```
{self.config.audit_folder_name}/
├── audit-YYYYMMDD-HHMMSS/   # Individual audit runs
│   ├── README.md            # Executive summary
│   ├── FINDINGS.md          # All findings
│   ├── TRUTH_TABLE.md       # Feature truth table
│   ├── FIX_PLAN.md          # Prioritized fixes
│   ├── diagrams/            # SVG visualizations
│   ├── reports/             # Category reports
│   ├── evidence/            # Proof artifacts
│   └── data/                # Raw JSON data
└── latest -> audit-xxx      # Symlink to latest audit
```

## Usage

Run an audit:
```bash
codetruth audit .
```

Or use the MCP tool in Windsurf:
```
@codetruth full_audit repo_path=.
```

---
*Generated by CodeTruth-MCP*
"""
        readme_path.write_text(readme_content)
        created_files.append(str(readme_path))

        return {
            "success": True,
            "workspace_path": str(workspace_path),
            "created_files": created_files,
            "message": f"CodeTruth workspace setup complete in {workspace_path}",
        }

    def format_diagnostics(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Format findings as IDE diagnostics.

        Converts CodeTruth findings to a format suitable
        for IDE inline display (similar to LSP diagnostics).

        Args:
            findings: List of CodeTruth findings

        Returns:
            List of IDE-compatible diagnostics
        """
        severity_map = {
            "critical": 1,  # Error
            "error": 1,  # Error
            "warning": 2,  # Warning
            "note": 3,  # Information
            "info": 4,  # Hint
        }

        diagnostics = []

        for finding in findings:
            severity = finding.get("severity", "info")
            threshold = severity_map.get(self.config.diagnostic_severity_threshold, 2)

            if severity_map.get(severity, 4) > threshold:
                continue

            diagnostic = {
                "range": {
                    "start": {
                        "line": (finding.get("line", 1) or 1) - 1,
                        "character": (finding.get("column", 0) or 0),
                    },
                    "end": {
                        "line": (finding.get("end_line") or finding.get("line", 1) or 1) - 1,
                        "character": (finding.get("end_column") or 1000),
                    },
                },
                "severity": severity_map.get(severity, 4),
                "source": "codetruth",
                "message": finding.get("message", "Unknown issue"),
                "code": finding.get("rule_id") or finding.get("type"),
                "data": {
                    "finding_id": finding.get("id"),
                    "type": finding.get("type"),
                    "suggested_fix": finding.get("suggested_fix"),
                },
            }

            diagnostics.append(diagnostic)

        return diagnostics

    def format_code_actions(
        self,
        finding: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Generate code actions (quick fixes) for a finding.

        Args:
            finding: The finding to generate actions for

        Returns:
            List of code actions
        """
        actions = []

        # Suggested fix action
        if finding.get("suggested_fix"):
            actions.append({
                "title": f"Fix: {finding.get('type', 'issue')}",
                "kind": "quickfix",
                "diagnostics": [finding.get("id")],
                "isPreferred": True,
                "data": {
                    "finding_id": finding.get("id"),
                    "fix_type": "suggested",
                },
            })

        # Ignore action
        actions.append({
            "title": f"Ignore this {finding.get('type', 'issue')}",
            "kind": "quickfix.ignore",
            "data": {
                "finding_id": finding.get("id"),
                "fix_type": "ignore",
            },
        })

        # View details action
        actions.append({
            "title": "View details in audit report",
            "kind": "quickfix.info",
            "data": {
                "finding_id": finding.get("id"),
                "fix_type": "view_details",
            },
        })

        return actions

    def create_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        actions: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create an IDE notification.

        Args:
            title: Notification title
            message: Notification message
            level: Severity level (info, warning, error)
            actions: Optional action buttons

        Returns:
            Notification object for IDE
        """
        type_map = {
            "info": 3,
            "warning": 2,
            "error": 1,
        }

        return {
            "type": type_map.get(level, 3),
            "title": title,
            "message": message,
            "source": "CodeTruth",
            "actions": actions or [],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def create_progress_notification(
        self,
        phase: str,
        progress: float,
        message: str,
    ) -> dict[str, Any]:
        """
        Create a progress notification.

        Args:
            phase: Current phase name
            progress: Progress percentage (0-100)
            message: Status message

        Returns:
            Progress notification object
        """
        return {
            "type": "progress",
            "title": f"CodeTruth: {phase}",
            "message": message,
            "progress": {
                "percentage": progress,
                "cancellable": True,
            },
            "source": "CodeTruth",
        }

    async def update_latest_symlink(self, audit_dir: Path) -> None:
        """
        Update the 'latest' symlink to point to the most recent audit.

        Args:
            audit_dir: Path to the new audit directory
        """
        codetruth_dir = audit_dir.parent
        latest_link = codetruth_dir / "latest"

        # Remove existing symlink
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()

        # Create new symlink
        try:
            latest_link.symlink_to(audit_dir.name)
        except OSError as e:
            logger.warning(f"Could not create symlink: {e}")
