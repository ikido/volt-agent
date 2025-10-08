"""Individual user report generation with separate file outputs"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def calculate_days_since(date_str: str) -> Optional[int]:
    """Calculate days since a given date
    
    Args:
        date_str: ISO date string
        
    Returns:
        Number of days or None if parsing fails
    """
    if not date_str:
        return None
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        today = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
        return (today - date).days
    except (ValueError, TypeError):
        return None


def calculate_days_between(start_str: str, end_str: str) -> Optional[int]:
    """Calculate days between two dates
    
    Args:
        start_str: ISO date string (start)
        end_str: ISO date string (end)
        
    Returns:
        Number of days or None if parsing fails
    """
    if not start_str or not end_str:
        return None
    try:
        start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        return (end - start).days
    except (ValueError, TypeError):
        return None


def generate_fibery_link(workspace: str, database: str, entity_type: str, public_id: str) -> str:
    """Generate Fibery URL for an entity"""
    return f"https://{workspace}.fibery.io/{database}/{entity_type}/{public_id}"


def generate_feature_summary_report(
    user_email: str,
    start_date: str,
    end_date: str,
    enriched_features: Dict[str, Dict[str, Any]],
    enriched_entities: Dict[str, Dict[str, Any]],
    matched_entries: List[Dict[str, Any]],
    fibery_workspace: str = "wearevolt"
) -> str:
    """Generate feature summary report
    
    Args:
        user_email: User email
        start_date: Report start date
        end_date: Report end date
        enriched_features: Dict of enriched feature data
        enriched_entities: Dict of enriched entity data (for assignee info)
        matched_entries: List of matched time entries (for per-task time calculation)
        fibery_workspace: Fibery workspace name
        
    Returns:
        Markdown content for feature summary
    """
    if not enriched_features:
        return f"""# Feature Summary: {user_email}
**Period:** {start_date} to {end_date}

No features worked on during this period.
"""
    
    report = f"""# Feature Summary: {user_email}
**Period:** {start_date} to {end_date}

Working on **{len(enriched_features)} features** during this period:

---

"""
    
    # Sort features by time spent (descending)
    sorted_features = sorted(
        enriched_features.items(),
        key=lambda x: x[1].get('aggregated_stats', {}).get('total_time_seconds', 0),
        reverse=True
    )
    
    for feature_id, feature_data in sorted_features:
        feature_name = feature_data.get('entity_name', 'Unknown Feature')
        metadata = feature_data.get('metadata', {})
        state = metadata.get('state', {}).get('name', 'Unknown')
        description_md = feature_data.get('description_md', '')
        summary_md = feature_data.get('summary_md', '')
        stats = feature_data.get('aggregated_stats', {})
        is_overdue = metadata.get('is_overdue', False)
        dates = metadata.get('dates', {})
        
        # Extract database and entity type from entity_type field
        entity_type_full = feature_data.get('entity_type', 'Scrum/Feature')
        parts = entity_type_full.split('/')
        database = parts[0] if len(parts) > 0 else 'Scrum'
        entity_type = parts[1] if len(parts) > 1 else 'Feature'
        
        # Generate Fibery link
        feature_link = generate_fibery_link(fibery_workspace, database, entity_type, feature_id)
        
        # Header with link
        report += f"## [{feature_name}]({feature_link})\n"
        report += f"**Feature ID:** #{feature_id}\n\n"
        
        # Time tracking
        time_this_week = stats.get('total_time_hours', 0)
        report += f"**Time This Week:** {time_this_week}h"
        
        # Total time from Fibery (tasksTimeSpent field - already in hours)
        custom_fields = metadata.get('custom_fields', {})
        tasks_time_spent_h = custom_fields.get('tasksTimeSpent', 0) or custom_fields.get('featureTimeSpentH', 0)
        if tasks_time_spent_h and tasks_time_spent_h > 0:
            report += f" | **Total Time (Fibery):** {tasks_time_spent_h:.1f}h"
        
        report += "\n\n"
        
        # Feature Overview - check and flag missing fields
        comments = feature_data.get('comments', [])
        has_description = bool(description_md and description_md.strip())
        has_comments = bool(comments and len(comments) > 0)
        
        report += "**Feature Overview:**\n"
        if has_description or has_comments or summary_md:
            if summary_md:
                # Clean summary - should be simple now with updated prompt
                clean_summary = summary_md.strip()
                report += f"{clean_summary}\n"
            elif has_description:
                # Truncate long descriptions
                short_desc = description_md[:300] + "..." if len(description_md) > 300 else description_md
                report += f"{short_desc}\n"
            
            # Flag what's missing
            missing = []
            if not has_description:
                missing.append("no description")
            if not has_comments:
                missing.append("no comments")
            if missing:
                report += f"\n⚠️ *Missing: {', '.join(missing)}*\n"
        else:
            report += "⚠️ No description, no comments\n"
        report += "\n"
        
        # Timeline with days since started and ETA (use Feature-specific date fields)
        if dates:
            timeline_parts = []
            # For Features, use devActualStartDate
            start_date_field = dates.get('devActualStartDate') or dates.get('startedDate')
            if start_date_field:
                start = start_date_field[:10] if len(start_date_field) > 10 else start_date_field
                days_since = calculate_days_since(start_date_field)
                if days_since is not None:
                    timeline_parts.append(f"**Started:** {start} ({days_since} days ago)")
                else:
                    timeline_parts.append(f"**Started:** {start}")
            
            # For Features, use devPlannedEndDate        
            eta_date_field = dates.get('devPlannedEndDate') or dates.get('plannedEnd')
            if eta_date_field:
                eta = eta_date_field[:10] if len(eta_date_field) > 10 else eta_date_field
                eta_part = f"**ETA:** {eta}"
                if is_overdue:
                    eta_part += " ⚠️ **OVERDUE**"
                timeline_parts.append(eta_part)
                
            if timeline_parts:
                report += " | ".join(timeline_parts) + "\n\n"
        
        # Combined Progress section
        related_tasks = stats.get('related_tasks', [])
        completed_tasks = stats.get('completed_tasks', 0)
        total_tasks = len(related_tasks)  # Use actual count from related_tasks
        overdue_tasks = stats.get('overdue_tasks', 0)
        
        report += f"**Progress:** {completed_tasks}/{total_tasks} tasks completed"
        if overdue_tasks > 0:
            report += f" ({overdue_tasks} overdue ⚠️)"
        report += f" | **Status:** {state}\n\n"
        
        # Task breakdown - show ALL tasks
        if related_tasks:
            report += "**Tasks:**\n\n"
            for task in related_tasks:
                task_id = task.get('task_id', '')
                task_name = task.get('task_name', 'Unknown')
                task_state = task.get('state', 'Unknown')
                task_started = task.get('started', '')
                task_eta = task.get('eta', '')
                completion_date = task.get('completion_date', '')
                is_completed = task.get('is_completed', False)
                is_task_overdue = task.get('is_overdue', False)
                task_assignees = task.get('assignees', [])
                
                # Get task entity data for link and summary (if enriched)
                task_entity = enriched_entities.get(task_id, {})
                
                # Get assignee name - try enriched entity first, then task data
                assignee_name = 'Unassigned'
                if task_entity:
                    # Check collections.assignees in enriched entity
                    entity_metadata = task_entity.get('metadata', {})
                    entity_assignees = entity_metadata.get('collections', {}).get('assignees', [])
                    if entity_assignees and len(entity_assignees) > 0:
                        first_assignee = entity_assignees[0]
                        if isinstance(first_assignee, dict):
                            assignee_name = first_assignee.get('name', 'Unassigned')
                        elif isinstance(first_assignee, str):
                            assignee_name = first_assignee
                
                # Fall back to task_assignees from feature data if not found
                if assignee_name == 'Unassigned' and task_assignees and len(task_assignees) > 0:
                    first_assignee = task_assignees[0]
                    if isinstance(first_assignee, dict):
                        assignee_name = first_assignee.get('name', 'Unassigned')
                    elif isinstance(first_assignee, str):
                        assignee_name = first_assignee
                if task_entity:
                    task_type_full = task_entity.get('entity_type', 'Scrum/Task')
                    task_description = task_entity.get('description_md', '')
                    task_summary = task_entity.get('summary_md', '')
                    task_comments = task_entity.get('comments', [])
                    task_custom_fields = task_entity.get('metadata', {}).get('custom_fields', {})
                else:
                    task_type_full = 'Scrum/Task'
                    task_description = ''
                    task_summary = ''
                    task_comments = []
                    task_custom_fields = {}
                
                task_parts = task_type_full.split('/')
                task_db = task_parts[0] if len(task_parts) > 0 else 'Scrum'
                task_type = task_parts[1] if len(task_parts) > 1 else 'Task'
                task_link = generate_fibery_link(fibery_workspace, task_db, task_type, task_id)
                
                # Calculate time tracking from matched_entries (time this week)
                task_time_seconds = sum(
                    entry['total_duration'] for entry in matched_entries 
                    if entry.get('entity_id') == task_id
                )
                task_time_hours = task_time_seconds / 3600
                
                # Get total time from Fibery (timeSpentH - already in hours)
                # Try enriched entity first, then fall back to task data from feature
                total_time_fibery_hours = task_custom_fields.get('timeSpentH', 0)
                if not total_time_fibery_hours:
                    # Fall back to time from feature's tasks collection
                    total_time_fibery_hours = task.get('time_spent_h', 0)
                
                # Icon
                icon = "✅" if is_completed else "🔲"
                
                # Format task line
                report += f"- {icon} [#{task_id}: {task_name}]({task_link})\n"
                report += f"  - **Status:** {task_state}"
                if is_task_overdue:
                    report += " ⚠️ OVERDUE"
                report += "\n"
                
                # Started date with days since
                if task_started:
                    start_str = task_started[:10] if len(task_started) > 10 else task_started
                    days_since = calculate_days_since(task_started)
                    if days_since is not None:
                        report += f"  - **Started:** {start_str} ({days_since} days ago)\n"
                    else:
                        report += f"  - **Started:** {start_str}\n"
                
                # Completion date with days to complete (for completed tasks)
                if is_completed and completion_date:
                    completion = completion_date[:10] if len(completion_date) > 10 else completion_date
                    report += f"  - **Completed:** {completion}"
                    if task_started:
                        days_to_complete = calculate_days_between(task_started, completion_date)
                        if days_to_complete is not None:
                            report += f" ({days_to_complete} days to complete)"
                    report += "\n"
                elif task_eta:  # ETA for incomplete tasks
                    eta_str = task_eta[:10] if len(task_eta) > 10 else task_eta
                    report += f"  - **ETA:** {eta_str}"
                    if is_task_overdue:
                        report += " ⚠️"
                    report += "\n"
                
                report += f"  - **Assigned:** {assignee_name}\n"
                
                # Time tracking - show for all tasks
                if task_time_hours > 0:
                    report += f"  - **Time This Week:** {task_time_hours:.1f}h"
                    if total_time_fibery_hours > 0:
                        report += f" | **Total (Fibery):** {total_time_fibery_hours:.1f}h"
                    report += "\n"
                elif total_time_fibery_hours > 0:
                    # Show total time even if not worked this week
                    report += f"  - **Total (Fibery):** {total_time_fibery_hours:.1f}h\n"
                
                # Task summary - show for all tasks
                has_description = bool(task_description and task_description.strip())
                has_comments = bool(task_comments and len(task_comments) > 0)
                
                if has_description or has_comments or task_summary:
                    if task_summary:
                        # Extract first line/sentence, skip the missing context warning if present
                        first_line = task_summary.split('\n')[0].strip()
                        if first_line.startswith('⚠️'):
                            # If summary is just the missing warning, skip it and flag below
                            if has_description:
                                first_line = task_description.split('\n')[0].strip()[:150]
                                report += f"  - **Summary:** {first_line}\n"
                        elif first_line.startswith('**'):
                            # Skip formatting lines
                            lines = [l.strip() for l in task_summary.split('\n') if l.strip() and not l.strip().startswith('**') and not l.strip().startswith('⚠️')]
                            if lines:
                                first_line = lines[0][:150]
                                report += f"  - **Summary:** {first_line}\n"
                        else:
                            report += f"  - **Summary:** {first_line[:150]}\n"
                    elif has_description:
                        first_line = task_description.split('\n')[0].strip()[:150]
                        report += f"  - **Summary:** {first_line}\n"
                    
                    # Flag what's missing (only once)
                    missing = []
                    if not has_description:
                        missing.append("no description")
                    if not has_comments:
                        missing.append("no comments")
                    if missing:
                        report += f"  - ⚠️ *Missing: {', '.join(missing)}*\n"
                else:
                    report += f"  - ⚠️ *Missing: no description, no comments*\n"
                
                report += "\n"
        
        report += "---\n\n"
    
    return report


def generate_project_entities_report(
    user_email: str,
    start_date: str,
    end_date: str,
    enriched_entities: Dict[str, Dict[str, Any]],
    matched_entries: List[Dict[str, Any]],
    fibery_workspace: str = "wearevolt"
) -> str:
    """Generate project entities report
    
    Args:
        user_email: User email
        start_date: Report start date
        end_date: Report end date
        enriched_entities: Dict of enriched entity data
        matched_entries: List of matched time entries
        fibery_workspace: Fibery workspace name
        
    Returns:
        Markdown content for project entities
    """
    if not enriched_entities or not matched_entries:
        return f"""# Project Entities: {user_email}
**Period:** {start_date} to {end_date}

No project entities worked on during this period.
"""
    
    report = f"""# Project Entities: {user_email}
**Period:** {start_date} to {end_date}

---

"""
    
    # Sort entities by time spent (descending)
    sorted_entries = sorted(matched_entries, key=lambda x: x['total_duration'], reverse=True)
    
    for entry in sorted_entries:
        entity_id = entry.get('entity_id')
        time_this_week = entry['total_duration'] / 3600
        
        if not entity_id or entity_id not in enriched_entities:
            continue
        
        entity = enriched_entities[entity_id]
        entity_name = entity.get('entity_name', 'Unknown')
        entity_type_full = entity.get('entity_type', 'Unknown')
        description_md = entity.get('description_md', '')
        summary_md = entity.get('summary_md', '')
        metadata = entity.get('metadata', {})
        
        # Extract database and entity type
        parts = entity_type_full.split('/')
        database = parts[0] if len(parts) > 0 else 'Scrum'
        entity_type = parts[1] if len(parts) > 1 else 'Task'
        
        # Generate links
        entity_link = generate_fibery_link(fibery_workspace, database, entity_type, entity_id)
        
        # Get related feature for context
        relations = metadata.get('relations', {})
        feature_context = ""
        if 'feature' in relations:
            feature = relations['feature']
            feature_id = feature.get('publicId') or feature.get('public_id')
            feature_name = feature.get('name', 'Unknown Feature')
            if feature_id:
                feature_link = generate_fibery_link(fibery_workspace, database, 'Feature', feature_id)
                feature_context = f"**Feature:** [#{feature_id}: {feature_name}]({feature_link})\n"
        
        # Header with link
        report += f"## [#{entity_id}: {entity_name}]({entity_link})\n"
        report += f"**Type:** {entity_type_full}\n\n"
        
        # Details as bullet points
        state = metadata.get('state', {}).get('name', 'Unknown')
        dates = metadata.get('dates', {})
        is_overdue = metadata.get('is_overdue', False)
        is_completed = state.lower() in ['done', 'completed', 'closed']
        
        # Time tracking
        report += f"- **Time This Week:** {time_this_week:.1f}h"
        custom_fields = metadata.get('custom_fields', {})
        total_time_fibery_h = custom_fields.get('timeSpentH', 0)
        if total_time_fibery_h and total_time_fibery_h > 0:
            report += f" | **Total (Fibery):** {total_time_fibery_h:.1f}h"
        report += "\n"
        
        if 'startedDate' in dates and dates['startedDate']:
            start_str = dates['startedDate'][:10]
            days_since = calculate_days_since(dates['startedDate'])
            if days_since is not None:
                report += f"- **Started:** {start_str} ({days_since} days ago)\n"
            else:
                report += f"- **Started:** {start_str}\n"
        
        # Show completion date for completed tasks, ETA for others
        completion_date_field = dates.get('completionDate') or dates.get('completedDate')
        if is_completed and completion_date_field:
            completion_str = completion_date_field[:10]
            report += f"- **Completed:** {completion_str}"
            if 'startedDate' in dates and dates['startedDate']:
                days_to_complete = calculate_days_between(dates['startedDate'], completion_date_field)
                if days_to_complete is not None:
                    report += f" ({days_to_complete} days to complete)"
            report += "\n"
        elif 'plannedEnd' in dates and dates['plannedEnd']:
            eta_str = dates['plannedEnd'][:10]
            report += f"- **ETA:** {eta_str}"
            if is_overdue:
                report += " ⚠️ **OVERDUE**"
            report += "\n"
        
        report += f"- **Status:** {state}\n"
        
        if feature_context:
            report += f"- {feature_context}"
        
        # Summary with specific missing flags
        comments = entity.get('comments', [])
        has_description = bool(description_md and description_md.strip())
        has_comments = bool(comments and len(comments) > 0)
        
        if has_description or has_comments or summary_md:
            if summary_md:
                # Clean up the summary for bullet-point format
                summary_lines = summary_md.strip().split('\n')
                report += f"- **Summary:** {summary_lines[0]}\n"
            elif has_description:
                first_line = description_md.split('\n')[0].strip()[:150]
                report += f"- **Summary:** {first_line}\n"
            
            # Flag what's missing
            missing = []
            if not has_description:
                missing.append("no description")
            if not has_comments:
                missing.append("no comments")
            if missing:
                report += f"- ⚠️ *Missing: {', '.join(missing)}*\n"
        else:
            report += "- ⚠️ **Missing Context**: No description, no comments\n"
        
        report += "\n---\n\n"
    
    return report


def generate_other_activities_report(
    user_email: str,
    start_date: str,
    end_date: str,
    unmatched_entries: List[Dict[str, Any]],
    unmatched_summary: str
) -> str:
    """Generate other activities report
    
    Args:
        user_email: User email
        start_date: Report start date
        end_date: Report end date
        unmatched_entries: List of unmatched time entries
        unmatched_summary: LLM summary of unmatched activities
        
    Returns:
        Markdown content for other activities
    """
    if not unmatched_entries:
        return f"""# Other Activities: {user_email}
**Period:** {start_date} to {end_date}

No other activities tracked during this period.
"""
    
    total_hours = sum(e['total_duration'] for e in unmatched_entries) / 3600
    
    report = f"""# Other Activities: {user_email}
**Period:** {start_date} to {end_date}

**Total Time:** {total_hours:.1f}h

---

"""
    
    # Add LLM summary if available
    if unmatched_summary and unmatched_summary != "No unmatched activities found.":
        report += unmatched_summary + "\n\n---\n\n"
    
    # List individual activities
    report += "## Activity Breakdown\n\n"
    sorted_unmatched = sorted(unmatched_entries, key=lambda x: x['total_duration'], reverse=True)
    
    for entry in sorted_unmatched:
        description = entry.get('description_clean', 'Unknown activity')
        hours = entry['total_duration'] / 3600
        report += f"- **{description}** ({hours:.1f}h)\n"
    
    return report

