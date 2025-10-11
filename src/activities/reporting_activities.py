"""Reporting activities for generating person and team reports."""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from temporalio import activity

from src.patterns.rolling_window import process_with_rolling_window
from src.storage import EnrichedEntity, JSONStorage, PersonReport


@activity.defn(name="generate_person_reports")
async def generate_person_reports(
    users: List[str],
    enriched_entities: List[Dict[str, Any]],
    run_id: str
) -> List[Dict[str, Any]]:
    """
    Generate LLM summaries for each user using rolling window.

    Activity 7: For each user, aggregates their enriched entity data
    and generates a comprehensive LLM-based markdown report.

    Args:
        users: List of user emails
        enriched_entities: List of enriched entity dictionaries
        run_id: Unique run identifier

    Returns:
        List of person report dictionaries
    """
    activity.logger.info(
        f"Generating person reports for {len(users)} users (run: {run_id})"
    )

    # Group enriched entities by user (from aggregated Toggl data)
    storage = JSONStorage()
    aggregated_data = storage.load_toggl_aggregated(run_id)

    if not aggregated_data:
        raise ValueError(f"No aggregated Toggl data found for run {run_id}")

    # Build entity ID -> enriched data mapping
    entity_map = {
        e["entity_id"]: e for e in enriched_entities
    }

    # Process users with rolling window (max 3 concurrent)
    async def generate_single_report(user_email: str) -> Dict[str, Any]:
        return await _generate_person_report_llm(
            user_email=user_email,
            aggregated_data=aggregated_data,
            entity_map=entity_map,
            run_id=run_id
        )

    person_reports = await process_with_rolling_window(
        entities=users,
        process_fn=generate_single_report,
        max_concurrent=3
    )

    activity.logger.info(f"Successfully generated {len(person_reports)} person reports")

    return person_reports


async def _generate_person_report_llm(
    user_email: str,
    aggregated_data: Dict[str, Any],
    entity_map: Dict[str, Dict[str, Any]],
    run_id: str
) -> Dict[str, Any]:
    """
    Generate LLM summary for one person's work.

    Args:
        user_email: User's email address
        aggregated_data: Aggregated Toggl data
        entity_map: Mapping of entity_id -> enriched data
        run_id: Run identifier

    Returns:
        PersonReport dictionary
    """
    user_data = aggregated_data["users"].get(user_email)
    if not user_data:
        raise ValueError(f"No data found for user {user_email}")

    stats = user_data["statistics"]

    # Build report sections
    report_lines = [
        f"# Individual Activity Report: {user_email}",
        "",
        f"**Run ID:** {run_id}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Summary",
        "",
        f"- **Total Time:** {stats['total_duration_seconds'] / 3600:.2f} hours",
        f"- **Matched Entities:** {stats['matched_entries']} entries ({stats['matched_duration_seconds'] / 3600:.2f} hours)",
        f"- **Unmatched Activities:** {stats['unmatched_entries']} entries ({stats['unmatched_duration_seconds'] / 3600:.2f} hours)",
        "",
        "## Matched Entities",
        "",
    ]

    # Group entities by type for better organization
    entities_by_type = defaultdict(list)
    for entity_data in user_data["matched_entities"]:
        entity_id = entity_data["entity_id"]
        entity_type = entity_data["entity_type"]
        database = entity_data["entity_database"]

        # Get enriched data if available
        enriched = entity_map.get(entity_id, {}).get("enriched_data", {})

        entities_by_type[f"{database}/{entity_type}"].append({
            "entity_id": entity_id,
            "name": enriched.get("name", "Unknown"),
            "duration_seconds": entity_data["duration_seconds"],
            "entries_count": entity_data["entries_count"],
            "state": enriched.get("state"),
        })

    # Add entities by type
    for entity_type, entities in sorted(entities_by_type.items()):
        report_lines.append(f"### {entity_type}")
        report_lines.append("")

        for entity in sorted(entities, key=lambda e: e["duration_seconds"], reverse=True):
            duration_hours = entity["duration_seconds"] / 3600
            state_str = f" [{entity['state']}]" if entity.get("state") else ""
            report_lines.append(
                f"- **#{entity['entity_id']}** {entity['name']}{state_str}: "
                f"{duration_hours:.2f}h ({entity['entries_count']} entries)"
            )

        report_lines.append("")

    # Add unmatched activities
    if user_data["unmatched_activities"]:
        report_lines.extend([
            "## Unmatched Activities",
            "",
        ])

        for activity in sorted(
            user_data["unmatched_activities"],
            key=lambda a: a["duration_seconds"],
            reverse=True
        ):
            duration_hours = activity["duration_seconds"] / 3600
            report_lines.append(
                f"- {activity['description']}: "
                f"{duration_hours:.2f}h ({activity['entries_count']} entries)"
            )

        report_lines.append("")

    report_content = "\n".join(report_lines)

    # Create PersonReport
    person_report = {
        "user_email": user_email,
        "report_content": report_content,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "statistics": stats,
    }

    return person_report


@activity.defn(name="save_enriched_data")
async def save_enriched_data(
    run_id: str,
    enriched_entities: List[Dict[str, Any]],
    person_reports: List[Dict[str, Any]]
) -> dict:
    """
    Save all enriched entities and person reports to files.

    Activity 8: Merges enriched entities with toggl_aggregated data,
    saves to enriched_data.json, and creates individual markdown files
    per person from PersonReport.

    Args:
        run_id: Unique run identifier
        enriched_entities: List of enriched entity dictionaries
        person_reports: List of person report dictionaries

    Returns:
        Dictionary with save results
    """
    activity.logger.info(
        f"Saving enriched data for run {run_id}: "
        f"{len(enriched_entities)} entities, {len(person_reports)} reports"
    )

    storage = JSONStorage()

    # Convert dicts to EnrichedEntity objects for storage
    enriched_objects = [
        EnrichedEntity.from_dict(e) for e in enriched_entities
    ]

    # Save enriched entities
    storage.save_enriched_data(run_id, enriched_objects)

    # Save individual person reports
    for report_dict in person_reports:
        person_report = PersonReport.from_dict(report_dict)
        storage.save_person_report(run_id, person_report)

    activity.logger.info("Enriched data and reports saved successfully")

    return {
        "status": "success",
        "enriched_entities_count": len(enriched_entities),
        "person_reports_count": len(person_reports),
    }


@activity.defn(name="generate_team_report")
async def generate_team_report(run_id: str) -> dict:
    """
    Use LLM to create aggregated team markdown report.

    Activity 9: Reads all enriched data and generates a comprehensive
    team-level report with executive summary, key accomplishments,
    cross-team patterns, and recommendations.

    Args:
        run_id: Unique run identifier

    Returns:
        Dictionary with report generation results
    """
    activity.logger.info(f"Generating team report for run {run_id}")

    storage = JSONStorage()

    # Load enriched data
    enriched_entities = storage.load_enriched_data(run_id)
    aggregated_data = storage.load_toggl_aggregated(run_id)

    if not enriched_entities or not aggregated_data:
        raise ValueError(f"Missing data for team report generation (run: {run_id})")

    # Build team-level report
    report_lines = [
        "# Team Activity Report",
        "",
        f"**Run ID:** {run_id}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Executive Summary",
        "",
    ]

    # Overall statistics
    total_users = aggregated_data["statistics"]["total_users"]
    total_matched = aggregated_data["statistics"]["total_matched_entities"]
    total_unmatched = aggregated_data["statistics"]["total_unmatched_activities"]

    # Calculate total time
    total_time_seconds = sum(
        user["statistics"]["total_duration_seconds"]
        for user in aggregated_data["users"].values()
    )
    total_time_hours = total_time_seconds / 3600

    report_lines.extend([
        f"- **Total Users:** {total_users}",
        f"- **Total Time Tracked:** {total_time_hours:.2f} hours",
        f"- **Unique Entities Worked On:** {total_matched}",
        f"- **Enriched Entities:** {len(enriched_entities)}",
        f"- **Unmatched Activities:** {total_unmatched}",
        "",
        "## Key Accomplishments",
        "",
    ])

    # Group entities by type
    entities_by_type = defaultdict(list)
    for entity in enriched_entities:
        entities_by_type[entity.entity_type].append(entity)

    for entity_type, entities in sorted(entities_by_type.items()):
        report_lines.append(f"### {entity_type}")
        report_lines.append(f"- **Count:** {len(entities)} entities")
        report_lines.append("")

    # Per-user summary
    report_lines.extend([
        "## Per-User Summary",
        "",
    ])

    for user_email, user_data in sorted(aggregated_data["users"].items()):
        stats = user_data["statistics"]
        user_hours = stats["total_duration_seconds"] / 3600
        matched_hours = stats["matched_duration_seconds"] / 3600

        report_lines.extend([
            f"### {user_email}",
            f"- Total: {user_hours:.2f}h | Matched: {matched_hours:.2f}h | "
            f"Entities: {len(user_data['matched_entities'])}",
            "",
        ])

    report_content = "\n".join(report_lines)

    # Save report
    storage.save_team_report(run_id, report_content)

    activity.logger.info("Team report generated successfully")

    return {
        "status": "success",
        "report_length": len(report_content),
    }
