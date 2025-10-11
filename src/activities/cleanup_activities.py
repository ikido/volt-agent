"""Cleanup activities for ensuring idempotency."""

from temporalio import activity

from src.storage import JSONStorage


@activity.defn(name="cleanup_toggl_stage")
async def cleanup_toggl_stage(run_id: str) -> dict:
    """
    Clean up previous Toggl stage outputs to ensure idempotency.

    This activity removes:
    - raw_toggl_data.json
    - toggl_aggregated.json
    - reports/toggl_summary.md

    Preserves:
    - enriched_data.json
    - reports/individual/*.md
    - reports/team_summary.md

    Args:
        run_id: Unique run identifier

    Returns:
        Dictionary with cleanup results
    """
    activity.logger.info(f"Cleaning up Toggl stage for run: {run_id}")

    storage = JSONStorage()
    storage.cleanup_toggl_stage(run_id)

    activity.logger.info("Toggl stage cleanup completed")

    return {
        "status": "success",
        "message": "Toggl stage outputs removed"
    }


@activity.defn(name="cleanup_fibery_stage")
async def cleanup_fibery_stage(run_id: str) -> dict:
    """
    Clean up previous Fibery stage outputs to ensure idempotency.

    This activity removes:
    - enriched_data.json
    - reports/individual/*.md
    - reports/team_summary.md

    Preserves:
    - raw_toggl_data.json
    - toggl_aggregated.json
    - reports/toggl_summary.md

    Args:
        run_id: Unique run identifier

    Returns:
        Dictionary with cleanup results
    """
    activity.logger.info(f"Cleaning up Fibery stage for run: {run_id}")

    storage = JSONStorage()
    storage.cleanup_fibery_stage(run_id)

    activity.logger.info("Fibery stage cleanup completed")

    return {
        "status": "success",
        "message": "Fibery stage outputs removed"
    }
