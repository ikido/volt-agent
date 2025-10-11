"""Default entity enrichment activity for generic Fibery entities."""

import os
from datetime import datetime
from typing import Any, Dict

from temporalio import activity

from src.fibery.client import FiberyClient


@activity.defn(name="default_enrich_entity")
async def default_enrich_entity(
    entity_id: str,
    entity_type: str,
    run_id: str
) -> Dict[str, Any]:
    """
    Default enrichment for entities without specific activity.

    Fetches common fields that most Fibery entities have:
    - State, dates, description, comments
    - Assignees, priority, labels

    Args:
        entity_id: Entity public ID
        entity_type: Entity type (e.g., "Scrum/Task")
        run_id: Run identifier for logging

    Returns:
        Dictionary with enriched entity data
    """
    activity.logger.debug(
        f"Default enrichment for {entity_type} #{entity_id} (run: {run_id})"
    )

    # Initialize Fibery client
    api_token = os.getenv("FIBERY_API_TOKEN")
    workspace_name = os.getenv("FIBERY_WORKSPACE_NAME")

    if not api_token or not workspace_name:
        raise ValueError("Missing Fibery credentials in environment")

    client = FiberyClient(api_token=api_token, workspace_name=workspace_name)

    # Parse entity type
    parts = entity_type.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid entity type format: {entity_type}")

    database, type_name = parts

    # Build a generic query for common fields
    query = f"""
query getEntity($searchId: String) {{
  find{type_name}s(publicId: {{is: $searchId}}) {{
    id
    publicId
    name
    description
    state {{
      name
    }}
    creationDate
    modificationDate
  }}
}}
"""

    result = client.graphql_query(
        database=database,
        query=query,
        variables={"searchId": entity_id}
    )

    if not result or "errors" in result:
        activity.logger.error(
            f"Failed to fetch entity {entity_type} #{entity_id}: {result}"
        )
        raise Exception(f"Failed to fetch entity {entity_type} #{entity_id}")

    # Extract entity data
    entities = result.get("data", {}).get(f"find{type_name}s", [])
    if not entities:
        activity.logger.warning(f"Entity {entity_type} #{entity_id} not found")
        raise Exception(f"Entity {entity_type} #{entity_id} not found")

    entity_data = entities[0]

    # Build enriched entity
    enriched = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "database": database,
        "public_id": entity_data.get("publicId"),
        "name": entity_data.get("name"),
        "enriched_data": {
            "id": entity_data.get("id"),
            "name": entity_data.get("name"),
            "description": entity_data.get("description"),
            "state": entity_data.get("state", {}).get("name") if entity_data.get("state") else None,
            "creation_date": entity_data.get("creationDate"),
            "modification_date": entity_data.get("modificationDate"),
        },
        "enriched_at": datetime.utcnow().isoformat() + "Z",
    }

    activity.logger.debug(
        f"Successfully enriched {entity_type} #{entity_id}: {entity_data.get('name')}"
    )

    return enriched
