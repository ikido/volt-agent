"""Scrum Bug enrichment activity with bug-specific fields."""

import os
from datetime import datetime
from typing import Any, Dict

from temporalio import activity

from src.fibery.client import FiberyClient


@activity.defn(name="enrich_scrum_bug")
async def enrich_scrum_bug(
    entity_id: str,
    entity_type: str,
    run_id: str
) -> Dict[str, Any]:
    """
    Enrich Scrum Bug with bug-specific fields.

    Fetches fields specific to Scrum Bugs:
    - Severity
    - Steps to Reproduce
    - Root Cause
    - Assignees

    Args:
        entity_id: Entity public ID
        entity_type: Entity type (should be "Scrum/Bug")
        run_id: Run identifier for logging

    Returns:
        Dictionary with enriched entity data
    """
    activity.logger.debug(
        f"Scrum Bug enrichment for #{entity_id} (run: {run_id})"
    )

    # Initialize Fibery client
    api_token = os.getenv("FIBERY_API_TOKEN")
    workspace_name = os.getenv("FIBERY_WORKSPACE_NAME")

    if not api_token or not workspace_name:
        raise ValueError("Missing Fibery credentials in environment")

    client = FiberyClient(api_token=api_token, workspace_name=workspace_name)

    # GraphQL query for Scrum Bug specific fields
    query = """
query getBug($searchId: String) {
  findBugs(publicId: {is: $searchId}) {
    id
    publicId
    name
    description
    state {
      name
    }
    severity: Severity {
      name
    }
    stepsToReproduce: Steps_to_Reproduce
    rootCause: Root_Cause
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
            f"Failed to fetch Scrum Bug #{entity_id}: {result}"
        )
        raise Exception(f"Failed to fetch Scrum Bug #{entity_id}")

    # Extract entity data
    bugs = result.get("data", {}).get("findBugs", [])
    if not bugs:
        activity.logger.warning(f"Scrum Bug #{entity_id} not found")
        raise Exception(f"Scrum Bug #{entity_id} not found")

    bug_data = bugs[0]

    # Build enriched entity
    enriched = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "database": "Scrum",
        "public_id": bug_data.get("publicId"),
        "name": bug_data.get("name"),
        "enriched_data": {
            "id": bug_data.get("id"),
            "name": bug_data.get("name"),
            "description": bug_data.get("description"),
            "state": bug_data.get("state", {}).get("name") if bug_data.get("state") else None,
            "severity": bug_data.get("severity", {}).get("name") if bug_data.get("severity") else None,
            "steps_to_reproduce": bug_data.get("stepsToReproduce"),
            "root_cause": bug_data.get("rootCause"),
            "assignee": {
                "name": bug_data.get("assignee", {}).get("name"),
                "email": bug_data.get("assignee", {}).get("email"),
            } if bug_data.get("assignee") else None,
            "creation_date": bug_data.get("creationDate"),
            "modification_date": bug_data.get("modificationDate"),
        },
        "enriched_at": datetime.utcnow().isoformat() + "Z",
    }

    activity.logger.debug(
        f"Successfully enriched Scrum Bug #{entity_id}: {bug_data.get('name')}"
    )

    return enriched
