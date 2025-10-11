"""Fibery entity extraction and enrichment orchestration activities."""

import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple

from temporalio import activity

from src.fibery.client import FiberyClient
from src.patterns.rolling_window import process_with_rolling_window
from src.storage import EntityToEnrich, EnrichedEntity, JSONStorage


@activity.defn(name="extract_fibery_entities")
async def extract_fibery_entities(run_id: str) -> Dict[Tuple[str, str], List[str]]:
    """
    Extract unique Fibery entities from aggregated Toggl data.

    Activity 5: Reads toggl_aggregated.json and builds a list of unique
    entities grouped by (database, entity_type) for enrichment.

    Args:
        run_id: Unique run identifier

    Returns:
        Dictionary mapping (database, entity_type) -> list of entity IDs
    """
    activity.logger.info(f"Extracting Fibery entities for run {run_id}")

    storage = JSONStorage()

    # Load aggregated Toggl data
    aggregated_data = storage.load_toggl_aggregated(run_id)
    if not aggregated_data:
        raise ValueError(f"No aggregated Toggl data found for run {run_id}")

    # Track unique entities by (database, type)
    entities_by_type: Dict[Tuple[str, str], Dict[str, EntityToEnrich]] = defaultdict(dict)

    # Extract entities from all users
    for user_email, user_data in aggregated_data["users"].items():
        for entity_data in user_data["matched_entities"]:
            entity_id = entity_data["entity_id"]
            entity_database = entity_data["entity_database"]
            entity_type = entity_data["entity_type"]

            # Skip if missing required fields
            if not entity_id or not entity_database or not entity_type:
                activity.logger.warning(
                    f"Skipping entity with missing fields: {entity_data}"
                )
                continue

            # Build entity key
            type_key = (entity_database, entity_type)

            # Add to set (using dict for deduplication)
            if entity_id not in entities_by_type[type_key]:
                entities_by_type[type_key][entity_id] = EntityToEnrich(
                    entity_id=entity_id,
                    entity_type=f"{entity_database}/{entity_type}",
                    database=entity_database,
                    public_id=entity_id,
                    name=None,  # Will be fetched during enrichment
                )

    # Convert to list format
    result: Dict[Tuple[str, str], List[str]] = {}
    for type_key, entities_dict in entities_by_type.items():
        result[type_key] = list(entities_dict.keys())

    total_entities = sum(len(ids) for ids in result.values())
    activity.logger.info(
        f"Extracted {total_entities} unique entities across {len(result)} types"
    )

    return result


@activity.defn(name="enrich_entities_by_type")
async def enrich_entities_by_type(
    entities_by_type: Dict[Tuple[str, str], List[str]],
    run_id: str,
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Orchestrate entity enrichment using type-specific activities.

    Activity 6: For each (database, entity_type) pair, looks up the appropriate
    enrichment activity from config and processes entities using rolling window.

    Args:
        entities_by_type: Dictionary mapping (db, type) -> entity IDs
        run_id: Unique run identifier
        config: Enrichment configuration (from enrichment_config.yaml)

    Returns:
        List of enriched entity dictionaries
    """
    activity.logger.info(
        f"Starting entity enrichment for run {run_id} "
        f"with {len(entities_by_type)} entity types"
    )

    all_enriched = []

    # Import enrichment activities
    from src.activities.enrichment import get_enrichment_function

    for (database, entity_type), entity_ids in entities_by_type.items():
        type_name = f"{database}/{entity_type}"
        activity.logger.info(
            f"Processing {len(entity_ids)} entities of type {type_name}"
        )

        # Get enrichment function for this type
        enrichment_fn = get_enrichment_function(type_name, config)

        # Get max_concurrent from config
        max_concurrent = config.get("enrichment_activities", {}) \
            .get(type_name, {}) \
            .get("max_concurrent", 5)

        # Get default max_concurrent if not specified
        if not max_concurrent:
            max_concurrent = config.get("enrichment_activities", {}) \
                .get("default", {}) \
                .get("max_concurrent", 5)

        # Create wrapper function that passes run_id
        async def enrich_wrapper(entity_id: str) -> Dict[str, Any]:
            return await enrichment_fn(
                entity_id=entity_id,
                entity_type=type_name,
                run_id=run_id
            )

        # Process entities with rolling window
        try:
            enriched = await process_with_rolling_window(
                entities=entity_ids,
                process_fn=enrich_wrapper,
                max_concurrent=max_concurrent
            )
            all_enriched.extend(enriched)
            activity.logger.info(
                f"Successfully enriched {len(enriched)} entities of type {type_name}"
            )
        except Exception as e:
            activity.logger.error(
                f"Failed to enrich entities of type {type_name}: {str(e)}"
            )
            # Re-raise to fail the workflow
            raise

    activity.logger.info(
        f"Completed entity enrichment: {len(all_enriched)} total entities"
    )

    return all_enriched
