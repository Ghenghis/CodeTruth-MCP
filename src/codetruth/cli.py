"""
CodeTruth CLI

Command-line interface for the CodeTruth MCP Server.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(
    name="codetruth",
    help="Evidence-Based Code Auditing - No claims without proof",
    add_completion=False,
)

console = Console()


@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Server host"),
    port: int = typer.Option(0, "--port", "-p", help="Server port (0 for stdio)"),
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio, sse"),
) -> None:
    """Start the CodeTruth MCP server."""
    from codetruth.core.server import CodeTruthServer
    from codetruth.core.config import CodeTruthConfig

    console.print("[bold blue]CodeTruth MCP Server[/bold blue]")
    console.print("Starting in", transport, "mode...")

    config = CodeTruthConfig()
    config.ensure_directories()

    server = CodeTruthServer(config)
    asyncio.run(server.run())


@app.command()
def audit(
    repo_path: Path = typer.Argument(Path("."), help="Repository path to audit"),
    profile: str = typer.Option("standard", "--profile", "-p", help="Audit profile: fast, standard, deep, forensics"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory for reports"),
    format: str = typer.Option("terminal", "--format", "-f", help="Output format: terminal, json, markdown"),
    create_folder: bool = typer.Option(True, "--create-folder/--no-folder", help="Create .codetruth audit folder"),
) -> None:
    """Run a complete audit on a repository."""
    from codetruth.core.config import CodeTruthConfig
    from codetruth.core.evidence import EvidenceVault
    from codetruth.core.inventory import RepoInventory
    from codetruth.core.gates import GateLadder
    from codetruth.core.truth_table import TruthTableGenerator
    from codetruth.reports.audit_folder import AuditFolderGenerator

    repo_path = repo_path.resolve()

    if not repo_path.exists():
        console.print(f"[red]Error:[/red] Repository not found: {repo_path}")
        raise typer.Exit(1)

    console.print(Panel.fit(
        f"[bold blue]CodeTruth Audit[/bold blue]\n"
        f"Repository: {repo_path}\n"
        f"Profile: {profile}",
        title="🔍 Starting Audit"
    ))

    async def run_audit() -> dict:
        config = CodeTruthConfig()
        config.ensure_directories()

        vault = EvidenceVault(config.db_path)
        await vault.initialize()

        results: dict = {
            "repo_path": str(repo_path),
            "profile": profile,
            "findings": [],
            "summary": {},
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            # Phase 1: Inventory
            task = progress.add_task("Building inventory...", total=None)
            inventory = RepoInventory(repo_path)
            results["inventory"] = await inventory.generate(include_ast=True)
            progress.update(task, completed=True)

            # Phase 2: Quality Gates
            task = progress.add_task("Running quality gates...", total=None)
            ladder = GateLadder(repo_path, vault)
            results["gates"] = await ladder.run(profile=profile)
            progress.update(task, completed=True)

            # Phase 3: Analyzers
            from codetruth.analyzers import (
                DeadCodeAnalyzer,
                UIWiringAnalyzer,
                LintAnalyzer,
                TypeCheckAnalyzer,
                SASTAnalyzer,
                SecretScanner,
                DependencyAuditor,
            )

            analyzers = [
                ("Dead code analysis", DeadCodeAnalyzer()),
                ("UI wiring audit", UIWiringAnalyzer()),
                ("Linting", LintAnalyzer()),
                ("Type checking", TypeCheckAnalyzer()),
                ("Security scan", SASTAnalyzer()),
                ("Secret scan", SecretScanner()),
                ("Dependency audit", DependencyAuditor()),
            ]

            for name, analyzer in analyzers:
                task = progress.add_task(f"{name}...", total=None)
                try:
                    result = await analyzer.run(repo_path, {}, vault)
                    results["findings"].extend(result.findings)
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] {name} failed: {e}")
                progress.update(task, completed=True)

            # Phase 4: Truth Table
            task = progress.add_task("Generating truth table...", total=None)
            generator = TruthTableGenerator(repo_path, vault)
            results["truth_table"] = await generator.generate()
            progress.update(task, completed=True)

        # Calculate summary
        findings = results["findings"]
        results["summary"] = {
            "total_findings": len(findings),
            "critical": len([f for f in findings if f.get("severity") == "critical"]),
            "errors": len([f for f in findings if f.get("severity") == "error"]),
            "warnings": len([f for f in findings if f.get("severity") == "warning"]),
        }

        return results

    results = asyncio.run(run_audit())

    # Create audit folder if requested
    if create_folder:
        async def create_folder_async() -> Path:
            generator = AuditFolderGenerator(repo_path)
            return await generator.generate(results)

        audit_dir = asyncio.run(create_folder_async())
        console.print(f"\n[green]✓[/green] Audit folder created: {audit_dir}")

    # Display results
    if format == "terminal":
        _display_results(results)
    elif format == "json":
        print(json.dumps(results, indent=2, default=str))
    elif format == "markdown":
        from codetruth.core.truth_table import TruthTable
        if "truth_table" in results and results["truth_table"].get("features"):
            tt = TruthTable(**results["truth_table"])
            print(tt.to_markdown())


def _display_results(results: dict) -> None:
    """Display audit results in terminal."""
    summary = results.get("summary", {})

    # Summary table
    table = Table(title="Audit Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="white")

    table.add_row("Total Findings", str(summary.get("total_findings", 0)))
    table.add_row("Critical", f"[red]{summary.get('critical', 0)}[/red]")
    table.add_row("Errors", f"[orange1]{summary.get('errors', 0)}[/orange1]")
    table.add_row("Warnings", f"[yellow]{summary.get('warnings', 0)}[/yellow]")

    console.print(table)

    # Gates summary
    gates = results.get("gates", {})
    if gates:
        console.print(f"\n[bold]Quality Gates:[/bold] {gates.get('gates_passed', 0)}/{gates.get('gates_run', 0)} passed")

    # Critical findings
    findings = results.get("findings", [])
    critical = [f for f in findings if f.get("severity") == "critical"][:5]

    if critical:
        console.print("\n[bold red]Critical Issues:[/bold red]")
        for f in critical:
            console.print(f"  • {f.get('message', 'Unknown')} ({f.get('file', 'unknown')})")

    console.print("\n[bold green]✓ Audit complete[/bold green]")


@app.command()
def init(
    repo_path: Path = typer.Argument(Path("."), help="Repository path"),
) -> None:
    """Initialize CodeTruth in a repository."""
    from codetruth.integrations.windsurf import WindsurfIntegration

    repo_path = repo_path.resolve()

    async def setup() -> dict:
        integration = WindsurfIntegration()
        return await integration.setup_workspace(repo_path)

    result = asyncio.run(setup())

    if result.get("success"):
        console.print("[green]✓[/green] CodeTruth initialized successfully!")
        console.print("\nCreated files:")
        for f in result.get("created_files", []):
            console.print(f"  • {f}")
    else:
        console.print("[red]Failed to initialize[/red]")


@app.command()
def truth_table(
    repo_path: Path = typer.Argument(Path("."), help="Repository path"),
    format: str = typer.Option("terminal", "--format", "-f", help="Output format: terminal, markdown, json, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
) -> None:
    """Generate Feature Truth Table for a repository."""
    from codetruth.core.config import CodeTruthConfig
    from codetruth.core.evidence import EvidenceVault
    from codetruth.core.truth_table import TruthTableGenerator

    repo_path = repo_path.resolve()

    async def generate() -> dict:
        config = CodeTruthConfig()
        vault = EvidenceVault(config.db_path)
        await vault.initialize()

        generator = TruthTableGenerator(repo_path, vault)
        return await generator.generate(output_format=format if format != "terminal" else "json")

    result = asyncio.run(generate())

    if format == "terminal":
        _display_truth_table(result)
    elif format == "json":
        content = json.dumps(result, indent=2, default=str)
        if output:
            output.write_text(content)
            console.print(f"[green]✓[/green] Truth table saved to {output}")
        else:
            print(content)
    elif format in ["markdown", "html"]:
        content = result.get("markdown") or result.get("html", "")
        if output:
            output.write_text(content)
            console.print(f"[green]✓[/green] Truth table saved to {output}")
        else:
            print(content)


def _display_truth_table(result: dict) -> None:
    """Display truth table in terminal."""
    features = result.get("features", [])

    table = Table(title="Feature Truth Table")
    table.add_column("Feature", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Status", style="white")
    table.add_column("Reachable", style="white")
    table.add_column("Wired", style="white")
    table.add_column("Tested", style="white")

    status_colors = {
        "working": "green",
        "partial": "yellow",
        "stubbed": "dim",
        "unwired": "orange1",
        "dead": "dim",
        "broken": "red",
        "unknown": "blue",
    }

    for f in features[:30]:  # Limit display
        status = f.get("status", "unknown")
        color = status_colors.get(status, "white")

        table.add_row(
            f.get("name", "Unknown")[:30],
            f.get("feature_type", "")[:15],
            f"[{color}]{status}[/{color}]",
            "✓" if f.get("is_reachable") else "✗" if f.get("is_reachable") is False else "?",
            "✓" if f.get("is_wired") else "✗" if f.get("is_wired") is False else "?",
            "✓" if f.get("is_tested") else "✗" if f.get("is_tested") is False else "?",
        )

    console.print(table)

    # Summary
    console.print(f"\nTotal: {result.get('total_features', 0)} features")
    console.print(f"  Working: {result.get('working_count', 0)}")
    console.print(f"  Broken: {result.get('broken_count', 0)}")
    console.print(f"  Unwired: {result.get('unwired_count', 0)}")


@app.command()
def version() -> None:
    """Show version information."""
    from codetruth import __version__
    console.print(f"CodeTruth-MCP v{__version__}")


if __name__ == "__main__":
    app()
