"""Temporal workflow for Toggl-Fibery pipeline orchestration."""

import yaml
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.storage import PipelineInput, ProgressInfo, RunMetadata, RunStatus, TemporalMetadata


@workflow.defn(name="TogglFiberyPipeline")
class TogglFiberyPipeline:
    """
    Temporal workflow orchestrating the Toggl-Fibery analysis pipeline.

    This workflow coordinates all pipeline stages:
    1. Toggl data collection (if start_from == "toggl")
    2. Fibery entity enrichment
    3. Report generation

    Workflow ID format: toggl-fibery-{run_id}
    Task Queue: volt-agent-pipeline
    """

    def __init__(self):
        """Initialize workflow state."""
        self.progress = ProgressInfo(
            current_stage="initializing",
            current_activity="",
            percentage=0.0,
            eta_seconds=None,
            details={}
        )

    @workflow.run
    async def run(self, pipeline_input: PipelineInput) -> Dict[str, Any]:
        """
        Execute the pipeline workflow.

        Args:
            pipeline_input: Pipeline input parameters

        Returns:
            Final run summary with statistics
        """
        workflow.logger.info(f"Starting pipeline workflow: {pipeline_input}")

        # Generate run_id if not provided
        run_id = pipeline_input.run_id
        if not run_id:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
            run_id = f"run_{timestamp}"

        workflow_id = workflow.info().workflow_id

        # Load configuration
        config = await self._load_config(pipeline_input.config)

        # Create run metadata
        await self._create_run_metadata(run_id, workflow_id, pipeline_input)

        try:
            # Stage 1: Toggl Collection (if starting from toggl)
            if pipeline_input.start_from == "toggl":
                await self._execute_toggl_stage(run_id, pipeline_input)
            else:
                # Validate that Toggl data exists
                workflow.logger.info(f"Skipping Toggl stage, using existing data from run {run_id}")
                # TODO: Add validation activity to check Toggl data exists

            # Stage 2: Fibery Enrichment
            await self._execute_fibery_stage(run_id, config, pipeline_input)

            # Mark run as completed
            await self._update_run_status(run_id, RunStatus.COMPLETED)

            workflow.logger.info(f"Pipeline workflow completed successfully: {run_id}")

            return {
                "status": "success",
                "run_id": run_id,
                "workflow_id": workflow_id,
            }

        except Exception as e:
            workflow.logger.error(f"Pipeline workflow failed: {str(e)}")
            await self._update_run_status(run_id, RunStatus.FAILED, str(e))
            raise

    async def _execute_toggl_stage(
        self,
        run_id: str,
        pipeline_input: PipelineInput
    ) -> None:
        """Execute Toggl collection stage."""
        workflow.logger.info(f"Executing Toggl stage for run {run_id}")
        self.progress.current_stage = "toggl"

        # Activity 0: Cleanup Toggl stage
        self.progress.current_activity = "cleanup_toggl_stage"
        self.progress.percentage = 5.0
        await workflow.execute_activity(
            "cleanup_toggl_stage",
            run_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 1: Fetch Toggl data
        self.progress.current_activity = "fetch_toggl_data"
        self.progress.percentage = 10.0
        await workflow.execute_activity(
            "fetch_toggl_data",
            args=[
                pipeline_input.start_date,
                pipeline_input.end_date,
                pipeline_input.users,
                run_id,
            ],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 2: Aggregate Toggl data
        self.progress.current_activity = "aggregate_toggl_data"
        self.progress.percentage = 25.0
        await workflow.execute_activity(
            "aggregate_toggl_data",
            run_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 3: Generate Toggl report
        self.progress.current_activity = "generate_toggl_report"
        self.progress.percentage = 30.0
        await workflow.execute_activity(
            "generate_toggl_report",
            run_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=self._get_retry_policy(),
        )

        # Mark Toggl stage as completed
        await self._add_completed_stage(run_id, "toggl")
        workflow.logger.info(f"Toggl stage completed for run {run_id}")

    async def _execute_fibery_stage(
        self,
        run_id: str,
        config: Dict[str, Any],
        pipeline_input: PipelineInput
    ) -> None:
        """Execute Fibery enrichment stage."""
        workflow.logger.info(f"Executing Fibery stage for run {run_id}")
        self.progress.current_stage = "fibery"

        # Activity 4: Cleanup Fibery stage
        self.progress.current_activity = "cleanup_fibery_stage"
        self.progress.percentage = 35.0
        await workflow.execute_activity(
            "cleanup_fibery_stage",
            run_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 5: Extract Fibery entities
        self.progress.current_activity = "extract_fibery_entities"
        self.progress.percentage = 40.0
        entities_by_type = await workflow.execute_activity(
            "extract_fibery_entities",
            run_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 6: Enrich entities by type
        self.progress.current_activity = "enrich_entities_by_type"
        self.progress.percentage = 50.0
        enriched_entities = await workflow.execute_activity(
            "enrich_entities_by_type",
            args=[entities_by_type, run_id, config],
            start_to_close_timeout=timedelta(minutes=60),
            retry_policy=self._get_retry_policy(),
        )

        # Extract user list from pipeline input or aggregated data
        users = pipeline_input.users if pipeline_input.users else await self._get_users_from_data(run_id)

        # Activity 7: Generate person reports
        self.progress.current_activity = "generate_person_reports"
        self.progress.percentage = 75.0
        person_reports = await workflow.execute_activity(
            "generate_person_reports",
            args=[users, enriched_entities, run_id],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 8: Save enriched data
        self.progress.current_activity = "save_enriched_data"
        self.progress.percentage = 85.0
        await workflow.execute_activity(
            "save_enriched_data",
            args=[run_id, enriched_entities, person_reports],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=self._get_retry_policy(),
        )

        # Activity 9: Generate team report
        self.progress.current_activity = "generate_team_report"
        self.progress.percentage = 95.0
        await workflow.execute_activity(
            "generate_team_report",
            run_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=self._get_retry_policy(),
        )

        # Mark Fibery stage as completed
        await self._add_completed_stage(run_id, "fibery")
        self.progress.percentage = 100.0
        workflow.logger.info(f"Fibery stage completed for run {run_id}")

    async def _create_run_metadata(
        self,
        run_id: str,
        workflow_id: str,
        pipeline_input: PipelineInput
    ) -> None:
        """Create and save run metadata."""
        # Note: We can't use JSONStorage directly in workflow
        # This would need to be an activity in production
        # For now, we'll skip this and let the first activity handle it
        pass

    async def _update_run_status(
        self,
        run_id: str,
        status: RunStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update run status in metadata."""
        # This would be an activity in production
        pass

    async def _add_completed_stage(self, run_id: str, stage: str) -> None:
        """Mark stage as completed."""
        # This would be an activity in production
        pass

    async def _get_users_from_data(self, run_id: str) -> List[str]:
        """Extract user emails from aggregated data."""
        # This would be an activity in production that reads aggregated data
        # For now, return empty list (should be handled by activities)
        return []

    async def _load_config(self, config_override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Load enrichment configuration."""
        # Load from file
        try:
            with open("config/enrichment_config.yaml", "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            workflow.logger.warning(f"Failed to load enrichment config: {e}")
            config = {"enrichment_activities": {"default": {"max_concurrent": 5}}}

        # Apply overrides
        if config_override:
            config.update(config_override)

        return config

    def _get_retry_policy(self) -> RetryPolicy:
        """Get default retry policy for activities."""
        return RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_attempts=1,  # Fail fast
            non_retryable_error_types=["ValueError", "ValidationError"],
        )

    @workflow.query
    def get_progress(self) -> Dict[str, Any]:
        """
        Query handler for real-time progress updates.

        Returns:
            Current progress information
        """
        return self.progress.to_dict()
