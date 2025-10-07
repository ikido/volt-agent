"""Main orchestration script for report generation"""

import os
import sys
import logging
import yaml
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dotenv import load_dotenv

from .database.db import Database
from .toggl.client import TogglClient
from .parser.fibery_parser import FiberyParser
from .llm.client import LLMClient
from .reporting.generator import ReportGenerator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def setup_logging(log_level: str, output_dir: str, timestamp: str):
    """Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        output_dir: Output directory for log files
        timestamp: Timestamp for log filename
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file = Path(output_dir) / f"toggl_report_log_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    logger.info(f"Configuration loaded from: {config_path}")
    return config


def process_entries(raw_entries: List[Dict[str, Any]], parser: FiberyParser) -> List[Dict[str, Any]]:
    """Process and aggregate raw time entries
    
    Args:
        raw_entries: List of raw time entries from Toggl
        parser: FiberyParser instance
        
    Returns:
        List of processed and aggregated entries
    """
    # Group entries by user_email + description
    groups = defaultdict(lambda: {
        'entries': [],
        'total_duration': 0,
        'user_email': None
    })
    
    for entry in raw_entries:
        description = entry.get('description', '')
        user_email = entry.get('user_email', '')
        
        # Parse metadata
        parsed = parser.parse(description)
        
        # Create group key
        key = (
            user_email,
            parsed['description_clean'],
            parsed.get('entity_id'),
            parsed.get('entity_database'),
            parsed.get('entity_type'),
            parsed.get('project')
        )
        
        groups[key]['entries'].append(entry)
        groups[key]['total_duration'] += entry.get('duration', 0)
        groups[key]['user_email'] = user_email
        groups[key]['parsed'] = parsed
    
    # Convert groups to list
    processed = []
    for key, group in groups.items():
        parsed = group['parsed']
        processed.append({
            'user_email': group['user_email'],
            'description_clean': parsed['description_clean'],
            'entity_id': parsed.get('entity_id'),
            'entity_database': parsed.get('entity_database'),
            'entity_type': parsed.get('entity_type'),
            'project': parsed.get('project'),
            'is_matched': parsed['is_matched'],
            'total_duration': group['total_duration'],
            'entry_count': len(group['entries'])
        })
    
    logger.info(f"Processed {len(raw_entries)} raw entries into {len(processed)} aggregated entries")
    return processed


def run_report_generation(
    start_date: str,
    end_date: str,
    user_emails: Optional[List[str]] = None,
    use_cache: bool = False,
    config_path: str = 'config/config.yaml',
    output_dir: str = './tmp',
    log_level: str = 'INFO'
):
    """Main function to run report generation
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        user_emails: List of user emails (None = all users)
        use_cache: Use cached data instead of fetching
        config_path: Path to config file
        output_dir: Output directory
        log_level: Logging level
    """
    # Generate timestamp and run ID
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    run_id = f"run_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    # Setup logging
    setup_logging(log_level, output_dir, timestamp)
    
    logger.info("="*80)
    logger.info("TOGGL TEAM ACTIVITY REPORT GENERATOR")
    logger.info("="*80)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Date Range: {start_date} to {end_date}")
    logger.info(f"Users: {', '.join(user_emails) if user_emails else 'ALL USERS'}")
    logger.info(f"Use Cache: {use_cache}")
    logger.info(f"Output Directory: {output_dir}")
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize components
    logger.info("Initializing components...")
    
    db = Database(config['database']['path'])
    db.create_run(run_id, start_date, end_date, user_emails or [])
    
    parser = FiberyParser(
        entity_id_pattern=config['parsing']['entity_id_pattern'],
        tag_pattern=config['parsing']['tag_pattern']
    )
    
    report_gen = ReportGenerator(output_dir)
    
    # Initialize LLM client if API key is available
    llm = None
    if os.getenv('OPENAI_API_KEY'):
        llm = LLMClient(
            api_key=os.getenv('OPENAI_API_KEY'),
            model=config['openai']['model'],
            max_tokens=config['openai']['max_tokens'],
            temperature=config['openai']['temperature'],
            timeout=config['openai']['timeout_seconds']
        )
        logger.info("OpenAI LLM client initialized")
    else:
        logger.warning("OPENAI_API_KEY not found - summaries will be skipped")
    
    # Fetch or load time entries
    if use_cache:
        logger.info("Using cached data...")
        raw_entries = db.get_time_entries_by_run(run_id)
        if not raw_entries:
            logger.error("No cached data found for this run")
            db.update_run_status(run_id, 'failed')
            return
    else:
        logger.info("Fetching data from Toggl API...")
        
        toggl = TogglClient(
            api_token=os.getenv('TOGGL_API_TOKEN'),
            workspace_id=int(os.getenv('TOGGL_WORKSPACE_ID')),
            base_url=config['toggl']['api_base_url'],
            timeout=config['toggl']['timeout_seconds'],
            max_retries=config['toggl']['max_retries']
        )
        
        # Get user IDs if user_emails specified
        user_ids = None  # None means all users
        
        raw_entries = toggl.get_time_entries(start_date, end_date, user_ids)
        
        if not raw_entries:
            logger.warning("No time entries found for the specified period")
            db.update_run_status(run_id, 'completed', 0)
            return
        
        # Cache entries
        db.upsert_time_entries(run_id, raw_entries)
    
    # Process entries
    logger.info("Processing time entries...")
    processed_entries = process_entries(raw_entries, parser)
    db.upsert_processed_entries(run_id, processed_entries)
    
    # Filter by user emails if specified
    if user_emails is None:
        # Get all unique user emails from processed entries
        all_processed = db.get_processed_entries_by_run(run_id)
        user_emails = sorted(list(set(e['user_email'] for e in all_processed if e.get('user_email'))))
        logger.info(f"Found {len(user_emails)} users in the data: {', '.join(user_emails)}")
    
    # Generate individual reports
    logger.info("Generating individual reports...")
    individual_filename = f"toggl_individual_reports_{timestamp}.md"
    individual_path = report_gen.output_dir / individual_filename
    
    # Open file for writing (will append each report as we generate it)
    individual_reports_text = []
    user_stats = []
    
    with open(individual_path, 'w', encoding='utf-8') as report_file:
        for idx, user_email in enumerate(user_emails):
            logger.info(f"Processing report for {user_email}...")
            
            # Get processed entries for this user
            user_entries = db.get_processed_entries_by_run(run_id, user_email)
            matched = [e for e in user_entries if e['is_matched']]
            unmatched = [e for e in user_entries if not e['is_matched']]
            
            # Generate summaries
            if llm and matched:
                matched_text = report_gen.format_entries_for_llm(matched)
                matched_summary = llm.generate_matched_summary(matched_text)
            else:
                matched_summary = "No matched entities found." if not matched else ""
            
            if llm and unmatched:
                unmatched_text = report_gen.format_entries_for_llm(unmatched)
                unmatched_summary = llm.generate_unmatched_summary(unmatched_text)
            else:
                unmatched_summary = "No unmatched activities found." if not unmatched else ""
            
            # Generate report
            report_content = report_gen.generate_individual_report(
                user_email=user_email,
                start_date=start_date,
                end_date=end_date,
                matched_entries=matched,
                unmatched_entries=unmatched,
                matched_summary=matched_summary,
                unmatched_summary=unmatched_summary,
                timestamp=timestamp
            )
            
            # Write to file immediately with separator
            if idx > 0:
                report_file.write("\n\n")
            report_file.write(report_content)
            report_file.flush()  # Ensure it's written to disk
            
            # Keep for team summary generation
            individual_reports_text.append(report_content)
            
            # Calculate user stats
            matched_seconds = sum(e['total_duration'] for e in matched)
            unmatched_seconds = sum(e['total_duration'] for e in unmatched)
            user_stats.append({
                'user_email': user_email,
                'total_seconds': matched_seconds + unmatched_seconds,
                'matched_seconds': matched_seconds,
                'unmatched_seconds': unmatched_seconds
            })
            
            logger.info(f"✓ Report for {user_email} written to {individual_path}")
    
    # Save to database
    individual_content = "\n\n".join(individual_reports_text)
    db.save_report(run_id, 'individual', individual_content, str(individual_path))
    logger.info(f"All individual reports saved to: {individual_path}")
    
    # Generate team summary
    logger.info("Generating team summary...")
    
    if llm:
        team_summary_text = llm.generate_team_summary(
            individual_reports=individual_content,
            start_date=start_date,
            end_date=end_date
        )
    else:
        team_summary_text = "Team summary generation skipped (no OpenAI API key)"
    
    team_report = report_gen.generate_team_report(
        start_date=start_date,
        end_date=end_date,
        user_stats=user_stats,
        team_summary=team_summary_text,
        individual_report_paths=[str(individual_path)],
        timestamp=timestamp
    )
    
    # Save team report
    team_filename = f"toggl_team_summary_{timestamp}.md"
    team_path = report_gen.output_dir / team_filename
    
    with open(team_path, 'w', encoding='utf-8') as f:
        f.write(team_report)
    
    db.save_report(run_id, 'team', team_report, str(team_path))
    logger.info(f"Team summary saved to: {team_path}")
    
    # Update run status
    db.update_run_status(run_id, 'completed', len(raw_entries))
    
    # Close database
    db.close()
    
    logger.info("="*80)
    logger.info("REPORT GENERATION COMPLETED SUCCESSFULLY")
    logger.info("="*80)
    logger.info(f"Individual Reports: {individual_path}")
    logger.info(f"Team Summary: {team_path}")
    logger.info(f"Log File: {report_gen.output_dir / f'toggl_report_log_{timestamp}.log'}")
    
    print("\n" + "="*80)
    print("✓ REPORT GENERATION COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"📄 Individual Reports: {individual_path}")
    print(f"📊 Team Summary: {team_path}")
    print(f"📝 Log File: {report_gen.output_dir / f'toggl_report_log_{timestamp}.log'}")
    print("="*80 + "\n")

