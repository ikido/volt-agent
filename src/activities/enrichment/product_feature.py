"""Product Feature enrichment activity with feature-specific fields."""

import os
from datetime import datetime
from typing import Any, Dict

from temporalio import activity

from src.fibery.client import FiberyClient


@activity.defn(name="enrich_product_feature")
async def enrich_product_feature(
    entity_id: str,
    entity_type: str,
    run_id: str
) -> Dict[str, Any]:
    """
    Enrich Product Feature with feature-specific fields.

    Fetches fields specific to Product Features:
    - Product Area, Customer Requests
    - Revenue Impact
    - Launch Date
    - Assignees

    Args:
        entity_id: Entity public ID
        entity_type: Entity type (should be "Product/Feature")
        run_id: Run identifier for logging

    Returns:
        Dictionary with enriched entity data
    """
    activity.logger.debug(
        f"Product Feature enrichment for #{entity_id} (run: {run_id})"
    )

    # Initialize Fibery client
    api_token = os.getenv("FIBERY_API_TOKEN")
    workspace_name = os.getenv("FIBERY_WORKSPACE_NAME")

    if not api_token or not workspace_name:
        raise ValueError("Missing Fibery credentials in environment")

    client = FiberyClient(api_token=api_token, workspace_name=workspace_name)

    # GraphQL query for Product Feature specific fields
    query = """
query getFeature($searchId: String) {
  findFeatures(publicId: {is: $searchId}) {
    id
    publicId
    name
    description
    state {
      name
    }
    productArea: Product_Area {
      name
    }
    customerRequests: Customer_Requests {
      name
    }
    revenueImpact: Revenue_Impact
    launchDate: Launch_Date
    owner: Owner {
      name
      email
    }
    creationDate
    modificationDate
  }
}
"""

    result = client.graphql_query(
        database="Product",
        query=query,
        variables={"searchId": entity_id}
    )

    if not result or "errors" in result:
        activity.logger.error(
            f"Failed to fetch Product Feature #{entity_id}: {result}"
        )
        raise Exception(f"Failed to fetch Product Feature #{entity_id}")

    # Extract entity data
    features = result.get("data", {}).get("findFeatures", [])
    if not features:
        activity.logger.warning(f"Product Feature #{entity_id} not found")
        raise Exception(f"Product Feature #{entity_id} not found")

    feature_data = features[0]

    # Build enriched entity
    enriched = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "database": "Product",
        "public_id": feature_data.get("publicId"),
        "name": feature_data.get("name"),
        "enriched_data": {
            "id": feature_data.get("id"),
            "name": feature_data.get("name"),
            "description": feature_data.get("description"),
            "state": feature_data.get("state", {}).get("name") if feature_data.get("state") else None,
            "product_area": feature_data.get("productArea", {}).get("name") if feature_data.get("productArea") else None,
            "customer_requests": [
                req.get("name") for req in feature_data.get("customerRequests", [])
            ] if feature_data.get("customerRequests") else [],
            "revenue_impact": feature_data.get("revenueImpact"),
            "launch_date": feature_data.get("launchDate"),
            "owner": {
                "name": feature_data.get("owner", {}).get("name"),
                "email": feature_data.get("owner", {}).get("email"),
            } if feature_data.get("owner") else None,
            "creation_date": feature_data.get("creationDate"),
            "modification_date": feature_data.get("modificationDate"),
        },
        "enriched_at": datetime.utcnow().isoformat() + "Z",
    }

    activity.logger.debug(
        f"Successfully enriched Product Feature #{entity_id}: {feature_data.get('name')}"
    )

    return enriched
