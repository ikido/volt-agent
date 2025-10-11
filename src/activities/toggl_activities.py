"""Toggl data fetching and processing activities."""

import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.parser.fibery_parser import FiberyParser
from src.storage import JSONStorage
from src.toggl.client import TogglClient


@activity.defn(name="fetch_toggl_data")
async def fetch_toggl_data(
    start_date: str,
    end_date: str,
    user_emails: Optional[List[str]],
    run_id: str
) -> dict:
    """
    Fetch raw Toggl time entries from API.

    Activity 1: Fetches all time entries for the specified date range
    and user filter using day-by-day chunking to avoid pagination issues.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        user_emails: Optional list of user emails to filter (None = all users)
        run_id: Unique run identifier

    Returns:
        Dictionary with fetch results and statistics
    """
    activity.logger.info(
        f"Fetching Toggl data from {start_date} to {end_date} for run {run_id}"
    )

    # Initialize clients
    api_token = os.getenv("TOGGL_API_TOKEN")
    workspace_id = int(os.getenv("TOGGL_WORKSPACE_ID"))

    if not api_token or not workspace_id:
        raise ValueError("Missing Toggl credentials in environment")

    toggl_client = TogglClient(api_token=api_token, workspace_id=workspace_id)
    storage = JSONStorage()

    # Fetch time entries (day-by-day automatically)
    # Note: Toggl API doesn't support filtering by email directly,
    # so we fetch all and filter after
    time_entries = toggl_client.get_time_entries(
        start_date=start_date,
        end_date=end_date,
        user_ids=None  # Fetch all users
    )

    # Filter by email if specified
    if user_emails:
        user_emails_lower = [email.lower() for email in user_emails]
        time_entries = [
            entry for entry in time_entries
            if entry.get("user_email", "").lower() in user_emails_lower
        ]

    activity.logger.info(f"Retrieved {len(time_entries)} time entries")

    # Save raw data
    data = {
        "run_id": run_id,
        "start_date": start_date,
        "end_date": end_date,
        "user_emails_filter": user_emails,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "time_entries": time_entries,
        "statistics": {
            "total_entries": len(time_entries),
            "total_duration_seconds": sum(e.get("duration", 0) for e in time_entries),
        },
    }

    storage.save_raw_toggl_data(run_id, data)

    activity.logger.info("Raw Toggl data saved successfully")

    return {
        "status": "success",
        "entries_count": len(time_entries),
        "total_duration_seconds": data["statistics"]["total_duration_seconds"],
    }


@activity.defn(name="aggregate_toggl_data")
async def aggregate_toggl_data(run_id: str) -> dict:
    """
    Parse and aggregate Toggl data by user and entity.

    Activity 2: Reads raw Toggl data, parses Fibery entity metadata,
    and aggregates entries by user, matched/unmatched status, and entity/activity.

    Args:
        run_id: Unique run identifier

    Returns:
        Dictionary with aggregation results
    """
    activity.logger.info(f"Aggregating Toggl data for run {run_id}")

    storage = JSONStorage()
    parser = FiberyParser()

    # Load raw data
    raw_data = storage.load_raw_toggl_data(run_id)
    if not raw_data:
        raise ValueError(f"No raw Toggl data found for run {run_id}")

    time_entries = raw_data["time_entries"]

    # Aggregate by user
    user_data = defaultdict(lambda: {
        "user_email": None,
        "matched_entities": {},
        "unmatched_activities": {},
        "statistics": {
            "total_duration_seconds": 0,
            "matched_duration_seconds": 0,
            "unmatched_duration_seconds": 0,
            "total_entries": 0,
            "matched_entries": 0,
            "unmatched_entries": 0,
        },
    })

    for entry in time_entries:
        user_email = entry.get("user_email")
        if not user_email:
            continue

        description = entry.get("description", "")
        duration = entry.get("duration", 0)

        # Parse Fibery metadata
        parsed = parser.parse(description)

        # Update user data
        user_info = user_data[user_email]
        user_info["user_email"] = user_email
        user_info["statistics"]["total_duration_seconds"] += duration
        user_info["statistics"]["total_entries"] += 1

        if parsed["is_matched"]:
            # Matched entity
            entity_key = (
                parsed["entity_database"],
                parsed["entity_type"],
                parsed["entity_id"],
            )

            if entity_key not in user_info["matched_entities"]:
                user_info["matched_entities"][entity_key] = {
                    "entity_id": parsed["entity_id"],
                    "entity_database": parsed["entity_database"],
                    "entity_type": parsed["entity_type"],
                    "project": parsed["project"],
                    "duration_seconds": 0,
                    "entries_count": 0,
                    "entries": [],
                }

            entity_data = user_info["matched_entities"][entity_key]
            entity_data["duration_seconds"] += duration
            entity_data["entries_count"] += 1
            entity_data["entries"].append({
                "description_clean": parsed["description_clean"],
                "start": entry.get("start"),
                "stop": entry.get("stop"),
                "duration": duration,
            })

            user_info["statistics"]["matched_duration_seconds"] += duration
            user_info["statistics"]["matched_entries"] += 1

        else:
            # Unmatched activity
            activity_key = parsed["description_clean"]

            if activity_key not in user_info["unmatched_activities"]:
                user_info["unmatched_activities"][activity_key] = {
                    "description": parsed["description_clean"],
                    "duration_seconds": 0,
                    "entries_count": 0,
                }

            activity_data = user_info["unmatched_activities"][activity_key]
            activity_data["duration_seconds"] += duration
            activity_data["entries_count"] += 1

            user_info["statistics"]["unmatched_duration_seconds"] += duration
            user_info["statistics"]["unmatched_entries"] += 1

    # Convert to serializable format
    aggregated_data = {
        "run_id": run_id,
        "aggregated_at": datetime.utcnow().isoformat() + "Z",
        "users": {},
    }

    for user_email, user_info in user_data.items():
        # Convert matched entities dict to list
        matched_entities_list = [
            entity_data
            for entity_data in user_info["matched_entities"].values()
        ]

        # Convert unmatched activities dict to list
        unmatched_activities_list = [
            activity_data
            for activity_data in user_info["unmatched_activities"].values()
        ]

        aggregated_data["users"][user_email] = {
            "user_email": user_email,
            "matched_entities": matched_entities_list,
            "unmatched_activities": unmatched_activities_list,
            "statistics": user_info["statistics"],
        }

    # Add global statistics
    aggregated_data["statistics"] = {
        "total_users": len(aggregated_data["users"]),
        "total_matched_entities": sum(
            len(u["matched_entities"]) for u in aggregated_data["users"].values()
        ),
        "total_unmatched_activities": sum(
            len(u["unmatched_activities"]) for u in aggregated_data["users"].values()
        ),
    }

    # Save aggregated data
    storage.save_toggl_aggregated(run_id, aggregated_data)

    activity.logger.info("Toggl data aggregated successfully")

    return {
        "status": "success",
        "total_users": aggregated_data["statistics"]["total_users"],
        "total_matched_entities": aggregated_data["statistics"]["total_matched_entities"],
        "total_unmatched_activities": aggregated_data["statistics"]["total_unmatched_activities"],
    }


@activity.defn(name="generate_toggl_report")
async def generate_toggl_report(run_id: str) -> dict:
    """
    Generate LLM-based markdown summary report for Toggl data.

    Activity 3: Reads aggregated Toggl data and uses LLM to generate
    a comprehensive markdown report with executive summary, per-user
    summaries, and time distribution analysis.

    Args:
        run_id: Unique run identifier

    Returns:
        Dictionary with report generation results
    """
    activity.logger.info(f"Generating Toggl report for run {run_id}")

    storage = JSONStorage()

    # Load aggregated data
    aggregated_data = storage.load_toggl_aggregated(run_id)
    if not aggregated_data:
        raise ValueError(f"No aggregated Toggl data found for run {run_id}")

    # For now, generate a simple markdown report
    # TODO: Integrate with LLM for rich report generation
    report_lines = [
        "# Toggl Activity Report",
        "",
        f"**Run ID:** {run_id}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Executive Summary",
        "",
        f"- **Total Users:** {aggregated_data['statistics']['total_users']}",
        f"- **Matched Entities:** {aggregated_data['statistics']['total_matched_entities']}",
        f"- **Unmatched Activities:** {aggregated_data['statistics']['total_unmatched_activities']}",
        "",
        "## Per-User Summaries",
        "",
    ]

    for user_email, user_data in aggregated_data["users"].items():
        stats = user_data["statistics"]
        total_hours = stats["total_duration_seconds"] / 3600
        matched_hours = stats["matched_duration_seconds"] / 3600
        unmatched_hours = stats["unmatched_duration_seconds"] / 3600

        report_lines.extend([
            f"### {user_email}",
            "",
            f"- **Total Time:** {total_hours:.2f} hours",
            f"- **Matched Time:** {matched_hours:.2f} hours ({len(user_data['matched_entities'])} entities)",
            f"- **Unmatched Time:** {unmatched_hours:.2f} hours ({len(user_data['unmatched_activities'])} activities)",
            "",
        ])

    report_content = "\n".join(report_lines)

    # Save report
    storage.save_toggl_report(run_id, report_content)

    activity.logger.info("Toggl report generated successfully")

    return {
        "status": "success",
        "report_length": len(report_content),
    }
