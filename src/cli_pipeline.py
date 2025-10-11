"""CLI for pipeline-based architecture using Temporal workflows."""

import asyncio
import click
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from temporalio.client import Client

from src.storage import PipelineInput, JSONStorage, RunStatus
from src.workflows import TogglFiberyPipeline

console = Console()


@click.group()
def pipeline():
    """Pipeline commands for Temporal-based workflow execution."""
    pass


@pipeline.command(name="run")
@click.option(
    '--start-date',
    type=str,
    help='Start date (YYYY-MM-DD) - required if start-from=toggl'
)
@click.option(
    '--end-date',
    type=str,
    help='End date (YYYY-MM-DD) - required if start-from=toggl'
)
@click.option(
    '--users',
    type=str,
    help='Comma-separated user emails (optional, defaults to all users)'
)
@click.option(
    '--start-from',
    type=click.Choice(['toggl', 'fibery'], case_sensitive=False),
    default='toggl',
    help='Stage to start from'
)
@click.option(
    '--run-id',
    type=str,
    help='Existing run ID (required if start-from=fibery)'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default='./tmp/runs',
    help='Output directory for runs'
)
def run_pipeline(start_date, end_date, users, start_from, run_id, output_dir):
    """
    Run the Toggl-Fibery pipeline workflow.

    Examples:

    \b
    # Start from beginning (Toggl collection)
    volt-agent pipeline run --start-date 2025-10-07 --end-date 2025-10-13

    \b
    # Start from Fibery enrichment (re-run enrichment only)
    volt-agent pipeline run --start-from fibery --run-id run_2025-10-10-15-30-45

    \b
    # Run for specific users only
    volt-agent pipeline run --start-date 2025-10-07 --end-date 2025-10-13 \\
        --users john@example.com,jane@example.com
    """
    asyncio.run(_run_pipeline_async(
        start_date, end_date, users, start_from, run_id, output_dir
    ))


async def _run_pipeline_async(
    start_date: Optional[str],
    end_date: Optional[str],
    users: Optional[str],
    start_from: str,
    run_id: Optional[str],
    output_dir: str
):
    """Async implementation of pipeline run."""
    # Validate inputs
    if start_from == "toggl" and (not start_date or not end_date):
        console.print("[red]Error: --start-date and --end-date required when start-from=toggl[/red]")
        sys.exit(1)

    if start_from == "fibery" and not run_id:
        console.print("[red]Error: --run-id required when start-from=fibery[/red]")
        sys.exit(1)

    # Parse user emails
    user_list = None
    if users:
        user_list = [email.strip() for email in users.split(',')]

    # Create pipeline input
    pipeline_input = PipelineInput(
        start_date=start_date or "",
        end_date=end_date or "",
        users=user_list,
        start_from=start_from,
        run_id=run_id,
    )

    # Generate run_id if not provided
    if not run_id:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        run_id = f"run_{timestamp}"

    workflow_id = f"toggl-fibery-{run_id}"

    console.print(Panel.fit(
        f"[bold]Toggl-Fibery Pipeline[/bold]\n"
        f"Run ID: {run_id}\n"
        f"Starting from: {start_from}",
        border_style="blue"
    ))

    try:
        # Connect to Temporal
        console.print("[blue]Connecting to Temporal server...[/blue]")
        client = await Client.connect("localhost:7233")
        console.print("[green]✓ Connected to Temporal[/green]")

        # Start workflow
        console.print(f"[blue]Starting workflow: {workflow_id}[/blue]")
        handle = await client.start_workflow(
            TogglFiberyPipeline.run,
            pipeline_input,
            id=workflow_id,
            task_queue="volt-agent-pipeline",
        )

        console.print(f"[green]✓ Workflow started[/green]")
        console.print(f"[dim]Workflow ID: {workflow_id}[/dim]")
        console.print(f"[dim]Run ID: {handle.id}[/dim]\n")

        # Monitor progress
        await _monitor_workflow_progress(handle, run_id)

        # Get result
        result = await handle.result()

        console.print("\n[green]✓ Pipeline completed successfully![/green]")
        console.print(f"[dim]Results saved to: {output_dir}/{run_id}[/dim]")

    except Exception as e:
        console.print(f"\n[red]✗ Pipeline failed: {str(e)}[/red]")
        sys.exit(1)


async def _monitor_workflow_progress(handle, run_id: str):
    """Monitor workflow progress with rich display."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        task = progress.add_task("[cyan]Processing...", total=100)

        while True:
            try:
                # Query progress
                progress_info = await handle.query("get_progress")

                # Update progress bar
                progress.update(
                    task,
                    completed=progress_info["percentage"],
                    description=f"[cyan]{progress_info['current_stage']}: {progress_info['current_activity']}"
                )

                # Check if complete
                if progress_info["percentage"] >= 100:
                    break

                await asyncio.sleep(2)  # Poll every 2 seconds

            except Exception as e:
                # Workflow might have completed
                break


@pipeline.command(name="list-runs")
@click.option(
    '--status',
    type=click.Choice(['completed', 'failed', 'in_progress'], case_sensitive=False),
    help='Filter by status'
)
@click.option(
    '--limit',
    type=int,
    default=10,
    help='Maximum number of runs to display'
)
def list_runs(status, limit):
    """List all pipeline runs."""
    storage = JSONStorage()

    # Map string to RunStatus enum
    status_filter = None
    if status:
        status_filter = RunStatus(status)

    runs = storage.list_runs(status=status_filter, limit=limit)

    if not runs:
        console.print("[yellow]No runs found[/yellow]")
        return

    # Create table
    table = Table(title=f"Pipeline Runs (showing {len(runs)})")
    table.add_column("Run ID", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Created", style="green")
    table.add_column("Duration", style="blue")
    table.add_column("Stages", style="white")

    for run in runs:
        # Calculate duration
        duration = "N/A"
        if run.completed_at:
            start = datetime.fromisoformat(run.created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(run.completed_at.replace("Z", "+00:00"))
            duration_seconds = (end - start).total_seconds()
            duration = f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"

        # Format stages
        stages = ", ".join(run.stages_completed) if run.stages_completed else "None"

        # Status with color
        status_display = run.status.value
        if run.status == RunStatus.COMPLETED:
            status_display = f"[green]{status_display}[/green]"
        elif run.status == RunStatus.FAILED:
            status_display = f"[red]{status_display}[/red]"
        else:
            status_display = f"[yellow]{status_display}[/yellow]"

        table.add_row(
            run.run_id,
            status_display,
            run.created_at[:19],  # Trim timestamp
            duration,
            stages
        )

    console.print(table)


@pipeline.command(name="show-run")
@click.argument('run_id')
def show_run(run_id):
    """Show details of a specific run."""
    storage = JSONStorage()
    metadata = storage.load_run_metadata(run_id)

    if not metadata:
        console.print(f"[red]Run not found: {run_id}[/red]")
        sys.exit(1)

    # Display run details
    console.print(Panel.fit(
        f"[bold]Run Details: {run_id}[/bold]\n\n"
        f"Status: {metadata.status.value}\n"
        f"Created: {metadata.created_at}\n"
        f"Pipeline Version: {metadata.pipeline_version}\n"
        f"Workflow ID: {metadata.workflow_id}\n\n"
        f"[bold]Stages Completed:[/bold] {', '.join(metadata.stages_completed) if metadata.stages_completed else 'None'}\n"
        f"[bold]Stages Failed:[/bold] {', '.join(metadata.stages_failed) if metadata.stages_failed else 'None'}\n"
        + (f"\n[red]Error: {metadata.error_message}[/red]" if metadata.error_message else ""),
        border_style="blue"
    ))

    # Show parameters
    console.print("\n[bold]Parameters:[/bold]")
    for key, value in metadata.parameters.items():
        console.print(f"  {key}: {value}")


@pipeline.command(name="cancel-run")
@click.argument('run_id')
def cancel_run(run_id):
    """Cancel a running workflow."""
    asyncio.run(_cancel_run_async(run_id))


async def _cancel_run_async(run_id: str):
    """Async implementation of cancel run."""
    workflow_id = f"toggl-fibery-{run_id}"

    try:
        client = await Client.connect("localhost:7233")
        handle = client.get_workflow_handle(workflow_id)

        await handle.cancel()

        console.print(f"[green]✓ Workflow cancelled: {workflow_id}[/green]")

    except Exception as e:
        console.print(f"[red]✗ Failed to cancel workflow: {str(e)}[/red]")
        sys.exit(1)


@pipeline.command(name="temporal-ui")
@click.option('--run-id', help='Optional run ID to open directly')
def open_temporal_ui(run_id):
    """Open Temporal UI in browser."""
    import webbrowser

    url = "http://localhost:8080"
    if run_id:
        workflow_id = f"toggl-fibery-{run_id}"
        url = f"http://localhost:8080/namespaces/default/workflows/{workflow_id}"

    console.print(f"[blue]Opening Temporal UI: {url}[/blue]")
    webbrowser.open(url)


if __name__ == '__main__':
    pipeline()
