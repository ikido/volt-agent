"""Entity enrichment activities for different Fibery entity types."""

from typing import Any, Callable, Dict

from .default import default_enrich_entity
from .scrum_task import enrich_scrum_task
from .scrum_bug import enrich_scrum_bug
from .product_feature import enrich_product_feature


# Registry of enrichment activities
ENRICHMENT_REGISTRY: Dict[str, Callable] = {
    "Scrum/Task": enrich_scrum_task,
    "Scrum/Bug": enrich_scrum_bug,
    "Product/Feature": enrich_product_feature,
}


def get_enrichment_function(
    entity_type: str,
    config: Dict[str, Any]
) -> Callable:
    """
    Get the appropriate enrichment function for an entity type.

    Args:
        entity_type: Entity type (e.g., "Scrum/Task")
        config: Enrichment configuration

    Returns:
        Enrichment function (async callable)
    """
    # Check registry first
    if entity_type in ENRICHMENT_REGISTRY:
        return ENRICHMENT_REGISTRY[entity_type]

    # Check config for custom activity mapping
    enrichment_activities = config.get("enrichment_activities", {})
    type_config = enrichment_activities.get(entity_type)

    if type_config:
        activity_name = type_config.get("activity")
        if activity_name and activity_name in ENRICHMENT_REGISTRY:
            return ENRICHMENT_REGISTRY[activity_name]

    # Fall back to default enrichment
    return default_enrich_entity


__all__ = [
    "default_enrich_entity",
    "enrich_scrum_task",
    "enrich_scrum_bug",
    "enrich_product_feature",
    "get_enrichment_function",
    "ENRICHMENT_REGISTRY",
]
