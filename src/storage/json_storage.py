"""JSON-based storage for pipeline data."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import EnrichedEntity, PersonReport, RunMetadata, RunStatus


class JSONStorage:
    """Handles JSON file storage for pipeline runs."""

    def __init__(self, base_dir: str = "./tmp/runs"):
        """Initialize JSON storage.

        Args:
            base_dir: Base directory for all runs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_run_dir(self, run_id: str) -> Path:
        """Get directory path for a specific run.

        Args:
            run_id: Unique run identifier

        Returns:
            Path to run directory
        """
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def get_reports_dir(self, run_id: str) -> Path:
        """Get reports directory for a run.

        Args:
            run_id: Unique run identifier

        Returns:
            Path to reports directory
        """
        reports_dir = self.get_run_dir(run_id) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir

    def get_individual_reports_dir(self, run_id: str) -> Path:
        """Get individual reports directory for a run.

        Args:
            run_id: Unique run identifier

        Returns:
            Path to individual reports directory
        """
        individual_dir = self.get_reports_dir(run_id) / "individual"
        individual_dir.mkdir(parents=True, exist_ok=True)
        return individual_dir

    # Run Metadata Management

    def save_run_metadata(self, metadata: RunMetadata) -> None:
        """Save run metadata.

        Args:
            metadata: Run metadata to save
        """
        run_dir = self.get_run_dir(metadata.run_id)
        metadata_path = run_dir / "run_metadata.json"

        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def load_run_metadata(self, run_id: str) -> Optional[RunMetadata]:
        """Load run metadata.

        Args:
            run_id: Unique run identifier

        Returns:
            Run metadata or None if not found
        """
        run_dir = self.get_run_dir(run_id)
        metadata_path = run_dir / "run_metadata.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, 'r') as f:
            data = json.load(f)
            return RunMetadata.from_dict(data)

    def update_run_status(
        self,
        run_id: str,
        status: RunStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update run status.

        Args:
            run_id: Unique run identifier
            status: New status
            error_message: Optional error message if failed
        """
        metadata = self.load_run_metadata(run_id)
        if metadata:
            metadata.status = status
            if status == RunStatus.COMPLETED or status == RunStatus.FAILED:
                metadata.completed_at = datetime.utcnow().isoformat() + "Z"
            if error_message:
                metadata.error_message = error_message
            self.save_run_metadata(metadata)

    def add_completed_stage(self, run_id: str, stage: str) -> None:
        """Mark stage as completed.

        Args:
            run_id: Unique run identifier
            stage: Stage name
        """
        metadata = self.load_run_metadata(run_id)
        if metadata and stage not in metadata.stages_completed:
            metadata.stages_completed.append(stage)
            self.save_run_metadata(metadata)

    def add_failed_stage(self, run_id: str, stage: str) -> None:
        """Mark stage as failed.

        Args:
            run_id: Unique run identifier
            stage: Stage name
        """
        metadata = self.load_run_metadata(run_id)
        if metadata and stage not in metadata.stages_failed:
            metadata.stages_failed.append(stage)
            self.save_run_metadata(metadata)

    # Raw Toggl Data

    def save_raw_toggl_data(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save raw Toggl time entries.

        Args:
            run_id: Unique run identifier
            data: Raw Toggl data
        """
        run_dir = self.get_run_dir(run_id)
        data_path = run_dir / "raw_toggl_data.json"

        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_raw_toggl_data(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Load raw Toggl time entries.

        Args:
            run_id: Unique run identifier

        Returns:
            Raw Toggl data or None if not found
        """
        run_dir = self.get_run_dir(run_id)
        data_path = run_dir / "raw_toggl_data.json"

        if not data_path.exists():
            return None

        with open(data_path, 'r') as f:
            return json.load(f)

    # Aggregated Toggl Data

    def save_toggl_aggregated(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save aggregated Toggl data.

        Args:
            run_id: Unique run identifier
            data: Aggregated Toggl data
        """
        run_dir = self.get_run_dir(run_id)
        data_path = run_dir / "toggl_aggregated.json"

        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_toggl_aggregated(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Load aggregated Toggl data.

        Args:
            run_id: Unique run identifier

        Returns:
            Aggregated Toggl data or None if not found
        """
        run_dir = self.get_run_dir(run_id)
        data_path = run_dir / "toggl_aggregated.json"

        if not data_path.exists():
            return None

        with open(data_path, 'r') as f:
            return json.load(f)

    # Enriched Data

    def save_enriched_data(
        self,
        run_id: str,
        enriched_entities: List[EnrichedEntity]
    ) -> None:
        """Save enriched entity data.

        Args:
            run_id: Unique run identifier
            enriched_entities: List of enriched entities
        """
        run_dir = self.get_run_dir(run_id)
        data_path = run_dir / "enriched_data.json"

        data = {
            "enriched_entities": [e.to_dict() for e in enriched_entities]
        }

        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_enriched_data(self, run_id: str) -> Optional[List[EnrichedEntity]]:
        """Load enriched entity data.

        Args:
            run_id: Unique run identifier

        Returns:
            List of enriched entities or None if not found
        """
        run_dir = self.get_run_dir(run_id)
        data_path = run_dir / "enriched_data.json"

        if not data_path.exists():
            return None

        with open(data_path, 'r') as f:
            data = json.load(f)
            return [
                EnrichedEntity.from_dict(e)
                for e in data.get("enriched_entities", [])
            ]

    # Reports

    def save_toggl_report(self, run_id: str, report_content: str) -> None:
        """Save Toggl summary report.

        Args:
            run_id: Unique run identifier
            report_content: Markdown report content
        """
        reports_dir = self.get_reports_dir(run_id)
        report_path = reports_dir / "toggl_summary.md"

        with open(report_path, 'w') as f:
            f.write(report_content)

    def save_person_report(self, run_id: str, person_report: PersonReport) -> None:
        """Save individual person report.

        Args:
            run_id: Unique run identifier
            person_report: Person report to save
        """
        individual_dir = self.get_individual_reports_dir(run_id)

        # Create safe filename from email
        safe_name = person_report.user_email.replace("@", "_at_").replace(".", "_")
        report_path = individual_dir / f"{safe_name}.md"

        with open(report_path, 'w') as f:
            f.write(person_report.report_content)

    def save_team_report(self, run_id: str, report_content: str) -> None:
        """Save team summary report.

        Args:
            run_id: Unique run identifier
            report_content: Markdown report content
        """
        reports_dir = self.get_reports_dir(run_id)
        report_path = reports_dir / "team_summary.md"

        with open(report_path, 'w') as f:
            f.write(report_content)

    # Cleanup Operations

    def cleanup_toggl_stage(self, run_id: str) -> None:
        """Remove Toggl stage outputs.

        Args:
            run_id: Unique run identifier
        """
        run_dir = self.get_run_dir(run_id)
        reports_dir = self.get_reports_dir(run_id)

        # Remove Toggl files
        files_to_remove = [
            run_dir / "raw_toggl_data.json",
            run_dir / "toggl_aggregated.json",
            reports_dir / "toggl_summary.md",
        ]

        for file_path in files_to_remove:
            if file_path.exists():
                file_path.unlink()

    def cleanup_fibery_stage(self, run_id: str) -> None:
        """Remove Fibery stage outputs.

        Args:
            run_id: Unique run identifier
        """
        run_dir = self.get_run_dir(run_id)
        reports_dir = self.get_reports_dir(run_id)
        individual_dir = self.get_individual_reports_dir(run_id)

        # Remove enriched data
        enriched_path = run_dir / "enriched_data.json"
        if enriched_path.exists():
            enriched_path.unlink()

        # Remove team report
        team_report_path = reports_dir / "team_summary.md"
        if team_report_path.exists():
            team_report_path.unlink()

        # Remove individual reports
        if individual_dir.exists():
            for report_file in individual_dir.glob("*.md"):
                report_file.unlink()

    def list_runs(
        self,
        status: Optional[RunStatus] = None,
        limit: Optional[int] = None
    ) -> List[RunMetadata]:
        """List all pipeline runs.

        Args:
            status: Optional status filter
            limit: Maximum number of runs to return

        Returns:
            List of run metadata, sorted by creation date (newest first)
        """
        runs = []

        for run_dir in self.base_dir.iterdir():
            if run_dir.is_dir():
                metadata_path = run_dir / "run_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        data = json.load(f)
                        metadata = RunMetadata.from_dict(data)

                        if status is None or metadata.status == status:
                            runs.append(metadata)

        # Sort by creation date (newest first)
        runs.sort(key=lambda r: r.created_at, reverse=True)

        if limit:
            runs = runs[:limit]

        return runs

    def run_exists(self, run_id: str) -> bool:
        """Check if a run exists.

        Args:
            run_id: Unique run identifier

        Returns:
            True if run exists
        """
        return self.load_run_metadata(run_id) is not None

    def has_toggl_data(self, run_id: str) -> bool:
        """Check if run has Toggl aggregated data.

        Args:
            run_id: Unique run identifier

        Returns:
            True if Toggl data exists
        """
        run_dir = self.get_run_dir(run_id)
        return (run_dir / "toggl_aggregated.json").exists()
