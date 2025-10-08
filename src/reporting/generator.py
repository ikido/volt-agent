"""Report generation module"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .individual_report import (
    generate_feature_summary_report,
    generate_project_entities_report,
    generate_other_activities_report
)

logger = logging.getLogger(__name__)


def generate_fibery_link(workspace: str, database: str, entity_type: str, public_id: str) -> str:
    """Generate Fibery URL for an entity
    
    Args:
        workspace: Fibery workspace name (e.g., "wearevolt")
        database: Database name (e.g., "Scrum")
        entity_type: Entity type (e.g., "Task", "Feature")
        public_id: Entity public ID (e.g., "7658")
        
    Returns:
        Full Fibery URL
    """
    return f"https://{workspace}.fibery.io/{database}/{entity_type}/{public_id}"


class ReportGenerator:
    """Generates markdown reports from processed time entries"""
    
    def __init__(self, output_dir: str = "./tmp", fibery_workspace: str = "wearevolt"):
        """Initialize report generator
        
        Args:
            output_dir: Directory for output files
            fibery_workspace: Fibery workspace name for link generation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fibery_workspace = fibery_workspace
        logger.info(f"Report output directory: {self.output_dir}")
    
    def format_entries_for_llm(self, entries: List[Dict[str, Any]]) -> str:
        """Format entries for LLM prompt
        
        Args:
            entries: List of processed entries
            
        Returns:
            Formatted text string
        """
        lines = []
        for entry in entries:
            hours = entry['total_duration'] / 3600
            
            if entry['is_matched']:
                # Matched entity
                entity_id = entry.get('entity_id', 'N/A')
                entity_db = entry.get('entity_database', 'N/A')
                entity_type = entry.get('entity_type', 'N/A')
                project = entry.get('project', 'N/A')
                description = entry.get('description_clean', '')
                
                lines.append(
                    f"- #{entity_id} [{entity_db}] [{entity_type}] [{project}]: "
                    f"{description} ({hours:.1f}h)"
                )
            else:
                # Unmatched activity
                description = entry.get('description_clean', 'Unknown activity')
                lines.append(f"- {description} ({hours:.1f}h)")
        
        return "\n".join(lines)
    
    def generate_individual_user_reports(
        self,
        user_email: str,
        start_date: str,
        end_date: str,
        matched_entries: List[Dict[str, Any]],
        unmatched_entries: List[Dict[str, Any]],
        unmatched_summary: str,
        enriched_entities: Optional[Dict[str, Dict[str, Any]]] = None,
        enriched_features: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Tuple[Path, Path, Path]:
        """Generate individual user reports in separate files
        
        Args:
            user_email: User email
            start_date: Report start date
            end_date: Report end date
            matched_entries: List of matched entries
            unmatched_entries: List of unmatched entries
            unmatched_summary: LLM summary of unmatched activities
            enriched_entities: Optional dict of enriched entity data
            enriched_features: Optional dict of enriched feature data
            
        Returns:
            Tuple of (feature_summary_path, project_entities_path, other_activities_path)
        """
        # Create user subfolder
        user_folder_name = user_email.replace('@', '_at_').replace('.', '_')
        user_folder = self.output_dir / user_folder_name
        user_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating reports for {user_email} in {user_folder}")
        
        # Generate feature summary report
        if enriched_features:
            feature_content = generate_feature_summary_report(
                user_email, start_date, end_date,
                enriched_features, enriched_entities or {},
                matched_entries,
                self.fibery_workspace
            )
        else:
            feature_content = f"""# Feature Summary: {user_email}
**Period:** {start_date} to {end_date}

No Fibery enrichment data available.
"""
        
        feature_path = user_folder / "feature_summary.md"
        with open(feature_path, 'w', encoding='utf-8') as f:
            f.write(feature_content)
        logger.info(f"  ✓ Feature summary: {feature_path}")
        
        # Generate project entities report
        if enriched_entities and matched_entries:
            entities_content = generate_project_entities_report(
                user_email, start_date, end_date,
                enriched_entities, matched_entries,
                self.fibery_workspace
            )
        else:
            entities_content = f"""# Project Entities: {user_email}
**Period:** {start_date} to {end_date}

No project entities worked on during this period.
"""
        
        entities_path = user_folder / "project_entities.md"
        with open(entities_path, 'w', encoding='utf-8') as f:
            f.write(entities_content)
        logger.info(f"  ✓ Project entities: {entities_path}")
        
        # Generate other activities report
        activities_content = generate_other_activities_report(
            user_email, start_date, end_date,
            unmatched_entries, unmatched_summary
        )
        
        activities_path = user_folder / "other_activities.md"
        with open(activities_path, 'w', encoding='utf-8') as f:
            f.write(activities_content)
        logger.info(f"  ✓ Other activities: {activities_path}")
        
        return feature_path, entities_path, activities_path
    
    def generate_individual_report(
        self,
        user_email: str,
        start_date: str,
        end_date: str,
        matched_entries: List[Dict[str, Any]],
        unmatched_entries: List[Dict[str, Any]],
        matched_summary: str,
        unmatched_summary: str,
        timestamp: str,
        enriched_entities: Optional[Dict[str, Dict[str, Any]]] = None,
        enriched_features: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Generate individual user report
        
        Args:
            user_email: User email
            start_date: Report start date
            end_date: Report end date
            matched_entries: List of matched entries
            unmatched_entries: List of unmatched entries
            matched_summary: LLM summary of matched entries
            unmatched_summary: LLM summary of unmatched entries
            timestamp: Report timestamp
            enriched_entities: Optional dict of enriched entity data (entity_id -> entity_dict)
            enriched_features: Optional dict of enriched feature data (feature_id -> feature_dict)
            
        Returns:
            Markdown report content
        """
        # Calculate statistics
        matched_seconds = sum(e['total_duration'] for e in matched_entries)
        unmatched_seconds = sum(e['total_duration'] for e in unmatched_entries)
        total_seconds = matched_seconds + unmatched_seconds
        
        matched_hours = matched_seconds / 3600
        unmatched_hours = unmatched_seconds / 3600
        total_hours = total_seconds / 3600
        
        matched_pct = (matched_seconds / total_seconds * 100) if total_seconds > 0 else 0
        unmatched_pct = (unmatched_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        # Build feature summary section if available
        feature_section = ""
        if enriched_features:
            feature_section = "## Feature Summary\n\n"
            feature_section += f"Working on **{len(enriched_features)} features** during this period:\n\n"
            
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
                
                feature_section += f"### Feature #{feature_id}: {feature_name}\n"
                feature_section += f"**Time Spent:** {stats.get('total_time_hours', 0)}h | "
                feature_section += f"**Status:** {state}"
                if is_overdue:
                    feature_section += " ⚠️ OVERDUE"
                feature_section += "\n\n"
                
                # Feature description/summary
                if not description_md and not summary_md:
                    feature_section += "⚠️ **Missing Context**: No description, no comments\n\n"
                elif summary_md:
                    feature_section += f"{summary_md}\n\n"
                elif description_md:
                    # Truncate long descriptions
                    short_desc = description_md[:200] + "..." if len(description_md) > 200 else description_md
                    feature_section += f"**About:** {short_desc}\n\n"
                
                # Feature dates
                dates = metadata.get('dates', {})
                if dates:
                    date_line = ""
                    if 'startedDate' in dates:
                        date_line += f"**Started:** {dates['startedDate'][:10]}"
                    if 'plannedEnd' in dates:
                        if date_line:
                            date_line += " | "
                        date_line += f"**ETA:** {dates['plannedEnd'][:10]}"
                        if is_overdue:
                            date_line += " ⚠️ OVERDUE"
                    if date_line:
                        feature_section += f"{date_line}\n\n"
                
                # Task breakdown
                total_tasks = stats.get('total_tasks', 0)
                completed_tasks = stats.get('completed_tasks', 0)
                remaining_tasks = stats.get('remaining_tasks', 0)
                overdue_tasks = stats.get('overdue_tasks', 0)
                
                feature_section += f"**Progress:** {completed_tasks}/{total_tasks} tasks completed"
                if overdue_tasks > 0:
                    feature_section += f" ({overdue_tasks} overdue ⚠️)"
                feature_section += "\n\n"
                
                # List tasks
                related_tasks = stats.get('related_tasks', [])
                if related_tasks:
                    feature_section += "**Tasks:**\n"
                    for task in related_tasks:
                        task_icon = "✅" if task['is_completed'] else "🔲"
                        task_status = task['state']
                        task_overdue = " ⚠️ OVERDUE" if task['is_overdue'] else ""
                        feature_section += f"- {task_icon} #{task['task_id']}: {task['task_name']} ({task_status}{task_overdue})\n"
                    feature_section += "\n"
                
                feature_section += "---\n\n"
            
            feature_section += "\n"
        
        # Build matched entities section with Fibery context if available
        matched_section = ""
        
        if enriched_entities and matched_entries:
            # Generate enriched section with entity details
            matched_section = "## Work on Project Entities\n\n"
            
            for entry in sorted(matched_entries, key=lambda x: x['total_duration'], reverse=True):
                entity_id = entry.get('entity_id')
                hours = entry['total_duration'] / 3600
                
                if entity_id and entity_id in enriched_entities:
                    entity = enriched_entities[entity_id]
                    entity_name = entity.get('entity_name', 'Unknown')
                    entity_type = entity.get('entity_type', 'Unknown')
                    summary = entity.get('summary_md', 'No summary available.')
                    
                    matched_section += f"### #{entity_id}: {entity_name}\n"
                    matched_section += f"**Time:** {hours:.1f} hours | **Type:** {entity_type}\n\n"
                    matched_section += f"{summary}\n\n"
                    matched_section += "---\n\n"
                else:
                    # Fallback if entity not enriched
                    entity_db = entry.get('entity_database', 'Unknown')
                    entity_type = entry.get('entity_type', 'Unknown')
                    description = entry.get('description_clean', '')
                    matched_section += f"### #{entity_id} [{entity_db}] [{entity_type}]\n"
                    matched_section += f"**Time:** {hours:.1f} hours\n"
                    matched_section += f"**Description:** {description}\n\n"
                    matched_section += "---\n\n"
        else:
            # Standard section without enrichment
            matched_section = f"""## Work on Project Entities

{matched_summary if matched_summary else "No matched entities found."}

---

"""
        
        # Build report
        report = f"""# Individual Activity Report: {user_email}
**Period:** {start_date} to {end_date}  
**Generated:** {timestamp}
{"**Report Type:** Enriched with Fibery Context" if enriched_entities else ""}

---

## Summary Statistics

- **Total Time Tracked:** {total_hours:.1f} hours
- **Time on Project Entities:** {matched_hours:.1f} hours ({matched_pct:.1f}%)
- **Time on Other Activities:** {unmatched_hours:.1f} hours ({unmatched_pct:.1f}%)

---

{feature_section}
{matched_section}

## Other Activities

{unmatched_summary if unmatched_summary else "No unmatched activities found."}

---
"""
        return report
    
    def generate_team_report(
        self,
        start_date: str,
        end_date: str,
        user_stats: List[Dict[str, Any]],
        team_summary: str,
        individual_report_paths: List[str],
        timestamp: str
    ) -> str:
        """Generate team summary report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            user_stats: List of per-user statistics
            team_summary: LLM-generated team summary
            individual_report_paths: Paths to individual reports
            timestamp: Report timestamp
            
        Returns:
            Markdown report content
        """
        # Calculate team totals
        total_seconds = sum(u['total_seconds'] for u in user_stats)
        matched_seconds = sum(u['matched_seconds'] for u in user_stats)
        unmatched_seconds = sum(u['unmatched_seconds'] for u in user_stats)
        
        total_hours = total_seconds / 3600
        matched_hours = matched_seconds / 3600
        unmatched_hours = unmatched_seconds / 3600
        
        matched_pct = (matched_seconds / total_seconds * 100) if total_seconds > 0 else 0
        unmatched_pct = (unmatched_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        user_count = len(user_stats)
        
        # Build user table
        table_rows = []
        for user in user_stats:
            email = user['user_email']
            total_h = user['total_seconds'] / 3600
            matched_h = user['matched_seconds'] / 3600
            unmatched_h = user['unmatched_seconds'] / 3600
            table_rows.append(f"| {email} | {total_h:.1f}h | {matched_h:.1f}h | {unmatched_h:.1f}h |")
        
        user_table = "\n".join(table_rows)
        
        # Build appendix links
        report_links = []
        for path in individual_report_paths:
            filename = Path(path).name
            report_links.append(f"- [{filename}]({filename})")
        
        links_text = "\n".join(report_links) if report_links else "No individual reports generated."
        
        # Build report
        report = f"""# Team Activity Report
**Period:** {start_date} to {end_date}  
**Generated:** {timestamp}  
**Team Members:** {user_count}

---

## Executive Summary

{team_summary}

---

## Team Statistics

- **Total Team Time Tracked:** {total_hours:.1f} hours
- **Time on Project Entities:** {matched_hours:.1f} hours ({matched_pct:.1f}%)
- **Time on Other Activities:** {unmatched_hours:.1f} hours ({unmatched_pct:.1f}%)

### Time Distribution by Team Member

| Team Member | Total Hours | Project Work | Other Work |
|-------------|-------------|--------------|------------|
{user_table}

---

## Appendix: Individual Reports

{links_text}

---
"""
        return report

