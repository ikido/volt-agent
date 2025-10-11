"""Scrum Task enrichment activity with task-specific fields."""

import os
from datetime import datetime
from typing import Any, Dict

from temporalio import activity

from src.fibery.client import FiberyClient


@activity.defn(name="enrich_scrum_task")
async def enrich_scrum_task(
    entity_id: str,
    entity_type: str,
    run_id: str
) -> Dict[str, Any]:
    """
    Enrich Scrum Task with task-specific fields.

    Fetches fields specific to Scrum Tasks:
    - Story Points, Sprint, Epic
    - Acceptance Criteria
    - Test Cases linked
    - Assignees

    Args:
        entity_id: Entity public ID
        entity_type: Entity type (should be "Scrum/Task")
        run_id: Run identifier for logging

    Returns:
        Dictionary with enriched entity data
    """
    activity.logger.debug(
        f"Scrum Task enrichment for #{entity_id} (run: {run_id})"
    )

    # Initialize Fibery client
    api_token = os.getenv("FIBERY_API_TOKEN")
    workspace_name = os.getenv("FIBERY_WORKSPACE_NAME")

    if not api_token or not workspace_name:
        raise ValueError("Missing Fibery credentials in environment")

    client = FiberyClient(api_token=api_token, workspace_name=workspace_name)

    # GraphQL query for Scrum Task specific fields
    query = """
query getTask($searchId: String) {
  findTasks(publicId: {is: $searchId}) {
    id
    publicId
    name
    description
    state {
      name
    }
    storyPoints: Story_Points
    sprint: Sprint {
      name
    }
    epic: Epic {
      name
    }
    acceptanceCriteria: Acceptance_Criteria
    assignee: Assignee {
      name
      email
    }
    creationDate
    modificationDate
  }
}
"""

    result = client.graphql_query(
        database="Scrum",
        query=query,
        variables={"searchId": entity_id}
    )

    if not result or "errors" in result:
        activity.logger.error(
            f"Failed to fetch Scrum Task #{entity_id}: {result}"
        )
        raise Exception(f"Failed to fetch Scrum Task #{entity_id}")

    # Extract entity data
    tasks = result.get("data", {}).get("findTasks", [])
    if not tasks:
        activity.logger.warning(f"Scrum Task #{entity_id} not found")
        raise Exception(f"Scrum Task #{entity_id} not found")

    task_data = tasks[0]

    # Build enriched entity
    enriched = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "database": "Scrum",
        "public_id": task_data.get("publicId"),
        "name": task_data.get("name"),
        "enriched_data": {
            "id": task_data.get("id"),
            "name": task_data.get("name"),
            "description": task_data.get("description"),
            "state": task_data.get("state", {}).get("name") if task_data.get("state") else None,
            "story_points": task_data.get("storyPoints"),
            "sprint": task_data.get("sprint", {}).get("name") if task_data.get("sprint") else None,
            "epic": task_data.get("epic", {}).get("name") if task_data.get("epic") else None,
            "acceptance_criteria": task_data.get("acceptanceCriteria"),
            "assignee": {
                "name": task_data.get("assignee", {}).get("name"),
                "email": task_data.get("assignee", {}).get("email"),
            } if task_data.get("assignee") else None,
            "creation_date": task_data.get("creationDate"),
            "modification_date": task_data.get("modificationDate"),
        },
        "enriched_at": datetime.utcnow().isoformat() + "Z",
    }

    activity.logger.debug(
        f"Successfully enriched Scrum Task #{entity_id}: {task_data.get('name')}"
    )

    return enriched
