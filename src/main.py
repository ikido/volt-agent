"""Main orchestration script for report generation"""

import os
import sys
import logging
import yaml
import uuid
import signal
import psutil
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


def kill_previous_runs():
    """Kill any previous report generation processes"""
    current_pid = os.getpid()
    script_name = "generate_report.py"
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue
            
            cmdline = proc.info.get('cmdline', [])
            if cmdline and script_name in ' '.join(cmdline):
                logger.info(f"Killing previous run (PID: {proc.info['pid']})")
                proc.kill()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed_count > 0:
        logger.info(f"Killed {killed_count} previous run(s)")
    else:
        logger.info("No previous runs to kill")


def run_report_generation(
    start_date: str,
    end_date: str,
    user_emails: Optional[List[str]] = None,
    use_cache: bool = False,
    config_path: str = 'config/config.yaml',
    output_dir: str = './tmp',
    log_level: str = 'INFO',
    enrich_fibery: bool = False,
    fibery_analysis: bool = False,
    skip_summarization: bool = False
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
        enrich_fibery: Enable Fibery entity enrichment
        fibery_analysis: Enable work alignment analysis
        skip_summarization: Skip LLM summarization (dev mode)
    """
    # Kill any previous runs first
    print("Checking for previous runs...")
    kill_previous_runs()
    
    # Generate timestamp and run ID
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    run_id = f"run_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    # Create run-specific output directory
    run_output_dir = Path(output_dir) / f"run_{timestamp}"
    run_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for organized output
    toggl_data_dir = run_output_dir / "toggl_data"
    toggl_data_dir.mkdir(exist_ok=True)
    
    if enrich_fibery:
        fibery_analysis_dir = run_output_dir / "fibery_analysis"
        fibery_analysis_dir.mkdir(exist_ok=True)
    
    # Setup logging (use run-specific directory)
    setup_logging(log_level, str(run_output_dir), timestamp)
    
    logger.info("="*80)
    logger.info("TOGGL TEAM ACTIVITY REPORT GENERATOR")
    logger.info("="*80)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Date Range: {start_date} to {end_date}")
    logger.info(f"Users: {', '.join(user_emails) if user_emails else 'ALL USERS'}")
    logger.info(f"Use Cache: {use_cache}")
    logger.info(f"Fibery Enrichment: {enrich_fibery}")
    logger.info(f"Fibery Analysis: {fibery_analysis}")
    logger.info(f"Skip Summarization: {skip_summarization}")
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
    
    report_gen = ReportGenerator(str(run_output_dir))
    
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
    
    # Initialize Fibery components if enrichment is enabled
    enrichment_pipeline = None
    if enrich_fibery:
        logger.info("Initializing Fibery enrichment components...")
        
        from .fibery.client import FiberyClient
        from .fibery.entity_fetcher import EntityFetcher
        from .llm.summarizer import EntitySummarizer
        from .enrichment.pipeline import EnrichmentPipeline
        
        # Check for Fibery credentials
        if not os.getenv('FIBERY_API_TOKEN'):
            logger.error("FIBERY_API_TOKEN not found in environment")
            raise ValueError("Fibery enrichment enabled but FIBERY_API_TOKEN not set")
        
        if not os.getenv('FIBERY_WORKSPACE_NAME'):
            logger.error("FIBERY_WORKSPACE_NAME not found in environment")
            raise ValueError("Fibery enrichment enabled but FIBERY_WORKSPACE_NAME not set")
        
        # Initialize Fibery client
        fibery_client = FiberyClient(
            api_token=os.getenv('FIBERY_API_TOKEN'),
            workspace_name=os.getenv('FIBERY_WORKSPACE_NAME'),
            base_url=config['fibery']['api_base_url'],
            timeout=config['fibery']['timeout_seconds'],
            max_retries=config['fibery']['max_retries']
        )
        
        # Initialize entity fetcher
        entity_fetcher = EntityFetcher(
            client=fibery_client,
            entity_type_configs=config['fibery']['entity_types']
        )
        
        # Initialize summarizer if LLM is available
        summarizer = None
        if llm and not skip_summarization:
            summarizer = EntitySummarizer(
                llm_client=llm,
                prompts_dir='config/prompts',
                entity_type_configs=config['fibery']['entity_types']
            )
        
        # Initialize enrichment pipeline
        enrichment_pipeline = EnrichmentPipeline(
            db=db,
            fibery_client=fibery_client,
            entity_fetcher=entity_fetcher,
            llm_client=llm,
            summarizer=summarizer,
            skip_summarization=skip_summarization
        )
        
        # Fetch and cache Fibery users
        try:
            user_count = enrichment_pipeline.fetch_and_cache_users()
            logger.info(f"Fetched and cached {user_count} Fibery users")
        except Exception as e:
            logger.error(f"Failed to fetch Fibery users: {e}")
            logger.warning("Continuing without user data...")
        
        logger.info("Fibery enrichment components initialized successfully")
    
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
    
    individual_reports_text = []
    user_stats = []
    all_user_paths = []
    
    for idx, user_email in enumerate(user_emails):
        logger.info(f"Processing report for {user_email}...")
        print(f"\n📝 Generating report for {user_email} ({idx+1}/{len(user_emails)})...")
        
        # Get processed entries for this user
        user_entries = db.get_processed_entries_by_run(run_id, user_email)
        matched = [e for e in user_entries if e['is_matched']]
        unmatched = [e for e in user_entries if not e['is_matched']]
        
        # Enrich entities with Fibery context if enabled
        enriched_entities = {}
        enriched_features = {}
        if enrich_fibery and enrichment_pipeline and matched:
            logger.info(f"Enriching {len(matched)} entities for {user_email}...")
            print(f"  🔄 Enriching {len(matched)} matched entities...")
            
            # Prepare entity info for enrichment
            entities_to_enrich = []
            for entry in matched:
                if entry.get('entity_id') and entry.get('entity_database') and entry.get('entity_type'):
                    # Construct storage type (e.g., "Scrum/Task")
                    storage_type = f"{entry['entity_database']}/{entry['entity_type']}"
                    entities_to_enrich.append({
                        'entity_id': entry['entity_id'],
                        'entity_type': storage_type
                    })
            
            # Enrich entities
            enriched_entities = enrichment_pipeline.enrich_entities_batch(
                entities_to_enrich,
                use_cache=use_cache
            )
            
            logger.info(f"Enriched {len(enriched_entities)} entities for {user_email}")
            print(f"  ✓ Enriched {len(enriched_entities)} entities")
            
            # Enrich features from enriched tasks
            if enriched_entities:
                enriched_features = enrichment_pipeline.enrich_features_from_tasks(
                    enriched_entities,
                    user_entries,
                    use_cache=use_cache
                )
                logger.info(f"Enriched {len(enriched_features)} features for {user_email}")
        
        # Generate summaries for other activities
        if llm and unmatched:
            unmatched_text = report_gen.format_entries_for_llm(unmatched)
            unmatched_summary = llm.generate_unmatched_summary(unmatched_text)
        else:
            unmatched_summary = "No unmatched activities found." if not unmatched else ""
        
        # Generate individual user reports (3 separate files)
        feature_path, entities_path, activities_path = report_gen.generate_individual_user_reports(
            user_email=user_email,
            start_date=start_date,
            end_date=end_date,
            matched_entries=matched,
            unmatched_entries=unmatched,
            unmatched_summary=unmatched_summary,
            enriched_entities=enriched_entities if enrich_fibery else None,
            enriched_features=enriched_features if enrich_fibery else None
        )
        
        all_user_paths.append({
            'email': user_email,
            'feature_summary': feature_path,
            'project_entities': entities_path,
            'other_activities': activities_path
        })
        
        # Keep simplified report content for team summary generation
        simple_report = f"# {user_email}\nTotal hours: {sum(e['total_duration'] for e in user_entries) / 3600:.1f}h\n"
        individual_reports_text.append(simple_report)
        
        # Calculate user stats
        matched_seconds = sum(e['total_duration'] for e in matched)
        unmatched_seconds = sum(e['total_duration'] for e in unmatched)
        user_stats.append({
            'user_email': user_email,
            'total_seconds': matched_seconds + unmatched_seconds,
            'matched_seconds': matched_seconds,
            'unmatched_seconds': unmatched_seconds
        })
        
        logger.info(f"✓ Reports for {user_email} generated successfully")
        print(f"  ✅ Reports generated for {user_email}")
    
    # Save summary to database
    individual_content = "\n\n".join(individual_reports_text)
    db.save_report(run_id, 'individual', individual_content, str(run_output_dir))
    logger.info(f"All individual reports saved in user subfolders under: {run_output_dir}")
    
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
    
    # Collect all individual report paths for reference
    individual_report_paths = []
    for user_path in all_user_paths:
        individual_report_paths.append(f"{user_path['email']}/feature_summary.md")
        individual_report_paths.append(f"{user_path['email']}/project_entities.md")
        individual_report_paths.append(f"{user_path['email']}/other_activities.md")
    
    team_report = report_gen.generate_team_report(
        start_date=start_date,
        end_date=end_date,
        user_stats=user_stats,
        team_summary=team_summary_text,
        individual_report_paths=individual_report_paths,
        timestamp=timestamp
    )
    
    # Save team report
    team_filename = "team_summary.md"
    team_path = run_output_dir / team_filename
    
    with open(team_path, 'w', encoding='utf-8') as f:
        f.write(team_report)
    
    db.save_report(run_id, 'team', team_report, str(team_path))
    logger.info(f"Team summary saved to: {team_path}")
    
    # Update run status
    db.update_run_status(run_id, 'completed', len(raw_entries))
    
    # Print enrichment stats if enabled
    if enrich_fibery and enrichment_pipeline:
        stats = enrichment_pipeline.get_enrichment_stats()
        logger.info("="*80)
        logger.info("FIBERY ENRICHMENT STATISTICS")
        logger.info("="*80)
        logger.info(f"Entities Fetched: {stats['entities_fetched']}")
        logger.info(f"Entities Cached: {stats['entities_cached']}")
        logger.info(f"Summaries Generated: {stats['summaries_generated']}")
        logger.info(f"Summaries Cached: {stats['summaries_cached']}")
        logger.info(f"Errors: {stats['errors']}")
        if stats['unknown_types']:
            logger.warning(f"Unknown Entity Types: {', '.join(stats['unknown_types'])}")
    
    # Close database
    db.close()
    
    logger.info("="*80)
    logger.info("REPORT GENERATION COMPLETED SUCCESSFULLY")
    logger.info("="*80)
    logger.info(f"Run Directory: {run_output_dir}")
    logger.info(f"Individual Reports: {len(all_user_paths)} users in subfolders")
    for user_path in all_user_paths:
        logger.info(f"  - {user_path['email']}: {user_path['feature_summary'].parent}")
    logger.info(f"Team Summary: {team_path}")
    logger.info(f"Log File: {run_output_dir / f'toggl_report_log_{timestamp}.log'}")
    
    print("\n" + "="*80)
    print("✓ REPORT GENERATION COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"📁 Run Directory: {run_output_dir}")
    print(f"📄 Individual Reports: {len(all_user_paths)} users in subfolders")
    for user_path in all_user_paths:
        print(f"   └─ {user_path['email']}/")
        print(f"      ├─ feature_summary.md")
        print(f"      ├─ project_entities.md")
        print(f"      └─ other_activities.md")
    print(f"📊 Team Summary: {team_path}")
    print(f"📝 Log File: {run_output_dir / f'toggl_report_log_{timestamp}.log'}")
    
    if enrich_fibery and enrichment_pipeline:
        stats = enrichment_pipeline.get_enrichment_stats()
        print("\n" + "="*80)
        print("📊 FIBERY ENRICHMENT STATISTICS")
        print("="*80)
        print(f"✓ Entities Fetched: {stats['entities_fetched']}")
        print(f"✓ Entities Cached: {stats['entities_cached']}")
        print(f"✓ Summaries Generated: {stats['summaries_generated']}")
        print(f"✓ Summaries Cached: {stats['summaries_cached']}")
        if stats['errors'] > 0:
            print(f"⚠️  Errors: {stats['errors']}")
        if stats['unknown_types']:
            print(f"⚠️  Unknown Types: {', '.join(stats['unknown_types'])}")
        print("="*80)
    
    print("="*80 + "\n")

