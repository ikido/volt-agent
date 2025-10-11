"""Temporal worker for pipeline activities."""

import asyncio
import logging
import sys

from temporalio.client import Client
from temporalio.worker import Worker

# Import workflows
from src.workflows import TogglFiberyPipeline

# Import all activities
from src.activities.cleanup_activities import cleanup_toggl_stage, cleanup_fibery_stage
from src.activities.toggl_activities import (
    fetch_toggl_data,
    aggregate_toggl_data,
    generate_toggl_report,
)
from src.activities.fibery_activities import extract_fibery_entities, enrich_entities_by_type
from src.activities.reporting_activities import (
    generate_person_reports,
    save_enriched_data,
    generate_team_report,
)
from src.activities.enrichment import (
    enrich_scrum_task,
    enrich_scrum_bug,
    enrich_product_feature,
    default_enrich_entity,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def main():
    """Start the Temporal worker."""
    logger.info("Connecting to Temporal server...")

    # Connect to Temporal server
    client = await Client.connect("localhost:7233")

    logger.info("Connected to Temporal server")

    # Create worker with all workflows and activities
    worker = Worker(
        client,
        task_queue="volt-agent-pipeline",
        workflows=[TogglFiberyPipeline],
        activities=[
            # Cleanup activities
            cleanup_toggl_stage,
            cleanup_fibery_stage,
            # Toggl activities
            fetch_toggl_data,
            aggregate_toggl_data,
            generate_toggl_report,
            # Fibery activities
            extract_fibery_entities,
            enrich_entities_by_type,
            # Enrichment activities (type-specific)
            enrich_scrum_task,
            enrich_scrum_bug,
            enrich_product_feature,
            default_enrich_entity,
            # Reporting activities
            generate_person_reports,
            save_enriched_data,
            generate_team_report,
        ],
        max_concurrent_activities=10,
        max_concurrent_workflow_tasks=1,
        max_concurrent_local_activities=10,
    )

    logger.info("Worker configured with all activities and workflows")
    logger.info("Task queue: volt-agent-pipeline")
    logger.info("Starting worker...")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
