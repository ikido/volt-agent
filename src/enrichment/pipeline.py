"""Main enrichment pipeline for Fibery entity context integration"""

import logging
from typing import Dict, Any, List, Optional
from ..database.db import Database
from ..fibery.client import FiberyClient
from ..fibery.entity_fetcher import EntityFetcher
from ..fibery.models import FiberyUser
from ..llm.client import LLMClient
from ..llm.summarizer import EntitySummarizer

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """Orchestrates Fibery entity enrichment process"""
    
    def __init__(
        self,
        db: Database,
        fibery_client: FiberyClient,
        entity_fetcher: EntityFetcher,
        llm_client: Optional[LLMClient] = None,
        summarizer: Optional[EntitySummarizer] = None,
        skip_summarization: bool = False
    ):
        """Initialize enrichment pipeline
        
        Args:
            db: Database instance
            fibery_client: FiberyClient instance
            entity_fetcher: EntityFetcher instance
            llm_client: Optional LLMClient instance
            summarizer: Optional EntitySummarizer instance
            skip_summarization: Skip LLM summarization (dev mode)
        """
        self.db = db
        self.fibery_client = fibery_client
        self.entity_fetcher = entity_fetcher
        self.llm_client = llm_client
        self.summarizer = summarizer
        self.skip_summarization = skip_summarization
        
        self.stats = {
            'entities_fetched': 0,
            'entities_cached': 0,
            'summaries_generated': 0,
            'summaries_cached': 0,
            'errors': 0,
            'unknown_types': []
        }
        
        logger.info("Enrichment pipeline initialized")
    
    def fetch_and_cache_users(self) -> int:
        """Fetch Fibery users and cache in database
        
        Returns:
            Number of users cached
        """
        logger.info("Fetching Fibery users...")
        
        users_data = self.fibery_client.get_users()
        if not users_data:
            logger.warning("No users fetched from Fibery")
            return 0
        
        # Convert to FiberyUser objects
        users = [FiberyUser(user_data).to_dict() for user_data in users_data]
        
        # Cache in database
        count = self.db.upsert_fibery_users(users)
        logger.info(f"Cached {count} Fibery users")
        
        return count
    
    def enrich_entity(
        self,
        entity_id: str,
        entity_type: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Enrich a single entity with Fibery context
        
        Args:
            entity_id: Public ID (e.g., "7658")
            entity_type: Entity type (e.g., "Scrum/Task")
            use_cache: Whether to use cached data
            
        Returns:
            Enriched entity dictionary or None on error
        """
        logger.debug(f"Enriching entity {entity_type} #{entity_id}")
        
        # Check cache first
        if use_cache:
            cached_entity = self.db.get_fibery_entity_by_public_id(entity_id)
            if cached_entity:
                logger.debug(f"Using cached entity #{entity_id}")
                return cached_entity
        
        # Fetch from Fibery
        entity = self.entity_fetcher.fetch_entity(entity_type, entity_id)
        
        if not entity:
            logger.error(f"Failed to fetch entity {entity_type} #{entity_id}")
            self.stats['errors'] += 1
            return None
        
        self.stats['entities_fetched'] += 1
        
        # Cache entity
        entity_dict = entity.to_dict()
        self.db.upsert_fibery_entity(entity_dict)
        self.stats['entities_cached'] += 1
        
        # Generate summary if LLM is available
        if not self.skip_summarization and self.summarizer:
            # Check if summary already exists
            if use_cache:
                cached_summary = self.db.get_fibery_entity_summary(entity_id)
                if cached_summary:
                    logger.debug(f"Using cached summary for #{entity_id}")
                    entity_dict['summary_md'] = cached_summary
                    self.stats['summaries_cached'] += 1
                    return entity_dict
            
            # Generate new summary
            summary = self.summarizer.summarize_entity(entity_dict, entity_type)
            
            if summary:
                # Update entity and database
                entity_dict['summary_md'] = summary
                self.db.update_fibery_entity_summary(entity_id, summary)
                self.stats['summaries_generated'] += 1
            else:
                logger.warning(f"Failed to generate summary for #{entity_id}")
        
        # Track unknown types
        if not self.entity_fetcher.is_type_configured(entity_type):
            if entity_type not in self.stats['unknown_types']:
                self.stats['unknown_types'].append(entity_type)
        
        return entity_dict
    
    def enrich_entities_batch(
        self,
        entities: List[Dict[str, Any]],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Enrich multiple entities
        
        Args:
            entities: List of entity dictionaries with 'entity_id' and 'entity_type'
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary mapping entity_id -> enriched_entity
        """
        logger.info(f"Enriching {len(entities)} entities...")
        
        enriched = {}
        
        for entity_info in entities:
            entity_id = entity_info.get('entity_id')
            entity_type = entity_info.get('entity_type')
            
            if not entity_id or not entity_type:
                logger.warning(f"Skipping entity with missing info: {entity_info}")
                continue
            
            enriched_entity = self.enrich_entity(entity_id, entity_type, use_cache)
            
            if enriched_entity:
                enriched[entity_id] = enriched_entity
        
        logger.info(f"Enriched {len(enriched)} / {len(entities)} entities")
        return enriched
    
    def enrich_features_from_tasks(
        self,
        enriched_tasks: Dict[str, Dict[str, Any]],
        user_entries: List[Dict[str, Any]],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch and aggregate Feature entities from tasks
        
        Args:
            enriched_tasks: Dictionary of enriched tasks (entity_id -> entity_data)
            user_entries: List of user time entries to calculate time spent
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary mapping feature_id -> aggregated_feature_data
        """
        logger.info("Extracting and enriching features from tasks...")
        
        # Extract unique feature IDs from tasks
        feature_ids = set()
        task_to_feature_map = {}  # Maps task_id -> feature_id
        
        for task_id, task_data in enriched_tasks.items():
            metadata = task_data.get('metadata', {})
            relations = metadata.get('relations', {})
            
            if 'feature' in relations:
                feature = relations['feature']
                # Try both camelCase and snake_case
                feature_id = feature.get('publicId') or feature.get('public_id')
                if feature_id:
                    feature_ids.add(feature_id)
                    task_to_feature_map[task_id] = feature_id
        
        if not feature_ids:
            logger.info("No features found in tasks")
            return {}
        
        logger.info(f"Found {len(feature_ids)} unique features to fetch")
        
        # Fetch each feature
        enriched_features = {}
        for feature_id in feature_ids:
            feature_entity = self.enrich_entity(feature_id, "Scrum/Feature", use_cache)
            if feature_entity:
                enriched_features[feature_id] = feature_entity
        
        # Aggregate statistics for each feature
        for feature_id, feature_data in enriched_features.items():
            # Get ALL tasks from feature metadata (not just worked-on tasks)
            metadata = feature_data.get('metadata', {})
            collections = metadata.get('collections', {})
            all_feature_tasks = collections.get('tasks', [])
            
            # Find tasks that were worked on this period
            worked_tasks = [
                task_id for task_id, fid in task_to_feature_map.items() if fid == feature_id
            ]
            
            # Calculate total time spent on this feature (only for worked tasks)
            total_time = 0
            for entry in user_entries:
                if entry.get('entity_id') in worked_tasks:
                    total_time += entry.get('total_duration', 0)
            
            # Build task list from ALL tasks in feature
            feature_tasks = []
            completed_count = 0
            overdue_count = 0
            
            for task_obj in all_feature_tasks:
                task_id = task_obj.get('publicId')
                task_name = task_obj.get('name', 'Unknown')
                
                # State can be a dict with 'name' key or a plain string
                state_obj = task_obj.get('state', {})
                if isinstance(state_obj, dict):
                    state = state_obj.get('name', 'Unknown')
                elif isinstance(state_obj, str):
                    state = state_obj
                else:
                    state = 'Unknown'
                    
                started = task_obj.get('startedDate')
                eta = task_obj.get('plannedEnd')
                completion_date = task_obj.get('completionDate')
                time_spent_h = task_obj.get('timeSpentH', 0)  # Extract total time from feature tasks
                
                # Handle assignees - could be list, None, or dict
                assignees_raw = task_obj.get('assignees', [])
                if isinstance(assignees_raw, list):
                    assignees = assignees_raw
                elif isinstance(assignees_raw, dict):
                    assignees = [assignees_raw]
                else:
                    assignees = []
                
                is_completed = state.lower() in ['done', 'completed', 'closed']
                
                # Calculate overdue
                is_overdue = False
                if eta and not is_completed:
                    try:
                        from datetime import datetime
                        eta_date = datetime.fromisoformat(eta.replace('Z', '+00:00'))
                        today = datetime.now(eta_date.tzinfo) if eta_date.tzinfo else datetime.now()
                        if today > eta_date:
                            is_overdue = True
                    except:
                        pass
                
                if is_completed:
                    completed_count += 1
                if is_overdue:
                    overdue_count += 1
                
                feature_tasks.append({
                    'task_id': task_id,
                    'task_name': task_name,
                    'state': state,
                    'is_completed': is_completed,
                    'is_overdue': is_overdue,
                    'started': started,
                    'eta': eta,
                    'completion_date': completion_date,
                    'assignees': assignees,
                    'time_spent_h': time_spent_h,  # Total time from Fibery
                    'worked_this_period': task_id in worked_tasks
                })
            
            # Add aggregated stats to feature
            feature_data['aggregated_stats'] = {
                'total_time_seconds': total_time,
                'total_time_hours': round(total_time / 3600, 1),
                'related_tasks': feature_tasks,
                'total_tasks': len(feature_tasks),
                'completed_tasks': completed_count,
                'remaining_tasks': len(feature_tasks) - completed_count,
                'overdue_tasks': overdue_count
            }
        
        logger.info(f"Enriched {len(enriched_features)} features with aggregated statistics")
        print(f"✓ Enriched {len(enriched_features)} features with task aggregations")
        return enriched_features
    
    def get_enrichment_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset enrichment statistics"""
        self.stats = {
            'entities_fetched': 0,
            'entities_cached': 0,
            'summaries_generated': 0,
            'summaries_cached': 0,
            'errors': 0,
            'unknown_types': []
        }

