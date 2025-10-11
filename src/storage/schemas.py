"""Data schemas for pipeline storage."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
from enum import Enum


class RunStatus(str, Enum):
    """Status of a pipeline run."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StageType(str, Enum):
    """Pipeline stages."""
    TOGGL = "toggl"
    FIBERY = "fibery"


@dataclass
class PipelineInput:
    """Input parameters for pipeline workflow."""
    # Date range for Toggl data
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD

    # User filtering
    users: Optional[List[str]] = None  # User emails, None = all users

    # Stage control
    start_from: Literal["toggl", "fibery"] = "toggl"
    run_id: Optional[str] = None  # Required if start_from="fibery"

    # Processing configuration
    config: Optional[Dict[str, Any]] = None  # Override config values


@dataclass
class TemporalMetadata:
    """Temporal workflow metadata."""
    workflow_id: str
    run_id: str
    task_queue: str


@dataclass
class RunMetadata:
    """Metadata for a pipeline run."""
    run_id: str
    workflow_id: str
    created_at: str  # ISO 8601 format
    status: RunStatus
    pipeline_version: str
    parameters: Dict[str, Any]
    temporal_metadata: TemporalMetadata
    stages_completed: List[str] = field(default_factory=list)
    stages_failed: List[str] = field(default_factory=list)
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "created_at": self.created_at,
            "status": self.status.value,
            "pipeline_version": self.pipeline_version,
            "parameters": self.parameters,
            "temporal_metadata": {
                "workflow_id": self.temporal_metadata.workflow_id,
                "run_id": self.temporal_metadata.run_id,
                "task_queue": self.temporal_metadata.task_queue,
            },
            "stages_completed": self.stages_completed,
            "stages_failed": self.stages_failed,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunMetadata":
        """Create from dictionary."""
        temporal_meta = data["temporal_metadata"]
        return cls(
            run_id=data["run_id"],
            workflow_id=data["workflow_id"],
            created_at=data["created_at"],
            status=RunStatus(data["status"]),
            pipeline_version=data["pipeline_version"],
            parameters=data["parameters"],
            temporal_metadata=TemporalMetadata(
                workflow_id=temporal_meta["workflow_id"],
                run_id=temporal_meta["run_id"],
                task_queue=temporal_meta["task_queue"],
            ),
            stages_completed=data.get("stages_completed", []),
            stages_failed=data.get("stages_failed", []),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
        )


@dataclass
class EntityToEnrich:
    """Entity that needs Fibery enrichment."""
    entity_id: str
    entity_type: str
    database: str
    public_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class EnrichedEntity:
    """Fibery entity with enriched data."""
    entity_id: str
    entity_type: str
    database: str
    public_id: Optional[str]
    name: Optional[str]
    enriched_data: Dict[str, Any]
    enriched_at: str  # ISO 8601

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "database": self.database,
            "public_id": self.public_id,
            "name": self.name,
            "enriched_data": self.enriched_data,
            "enriched_at": self.enriched_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnrichedEntity":
        """Create from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            database=data["database"],
            public_id=data.get("public_id"),
            name=data.get("name"),
            enriched_data=data["enriched_data"],
            enriched_at=data["enriched_at"],
        )


@dataclass
class PersonReport:
    """LLM-generated report for one person's work."""
    user_email: str
    report_content: str  # Markdown format
    generated_at: str  # ISO 8601
    statistics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_email": self.user_email,
            "report_content": self.report_content,
            "generated_at": self.generated_at,
            "statistics": self.statistics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonReport":
        """Create from dictionary."""
        return cls(
            user_email=data["user_email"],
            report_content=data["report_content"],
            generated_at=data["generated_at"],
            statistics=data["statistics"],
        )


@dataclass
class ProgressInfo:
    """Progress information for workflow query."""
    current_stage: str
    current_activity: str
    percentage: float
    eta_seconds: Optional[int]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "current_stage": self.current_stage,
            "current_activity": self.current_activity,
            "percentage": self.percentage,
            "eta_seconds": self.eta_seconds,
            "details": self.details,
        }
