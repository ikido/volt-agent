"""Report generation module"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates markdown reports from processed time entries"""
    
    def __init__(self, output_dir: str = "./tmp"):
        """Initialize report generator
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
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
    
    def generate_individual_report(
        self,
        user_email: str,
        start_date: str,
        end_date: str,
        matched_entries: List[Dict[str, Any]],
        unmatched_entries: List[Dict[str, Any]],
        matched_summary: str,
        unmatched_summary: str,
        timestamp: str
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
        
        # Build report
        report = f"""# Individual Activity Report: {user_email}
**Period:** {start_date} to {end_date}  
**Generated:** {timestamp}

---

## Summary Statistics

- **Total Time Tracked:** {total_hours:.1f} hours
- **Time on Project Entities:** {matched_hours:.1f} hours ({matched_pct:.1f}%)
- **Time on Other Activities:** {unmatched_hours:.1f} hours ({unmatched_pct:.1f}%)

---

## Work on Project Entities

{matched_summary if matched_summary else "No matched entities found."}

---

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

