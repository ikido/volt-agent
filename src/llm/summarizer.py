"""LLM-based entity summarization with template loading"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .client import LLMClient

logger = logging.getLogger(__name__)


class EntitySummarizer:
    """Generates AI summaries for Fibery entities using entity-type-specific prompts"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        prompts_dir: str = "config/prompts",
        entity_type_configs: Optional[list] = None
    ):
        """Initialize entity summarizer
        
        Args:
            llm_client: LLMClient instance
            prompts_dir: Directory containing prompt template files
            entity_type_configs: List of entity type configurations
        """
        self.llm = llm_client
        self.prompts_dir = Path(prompts_dir)
        self.entity_type_configs = entity_type_configs or []
        
        # Build mapping: storage_type -> prompt_template
        self.prompt_map = {}
        for config in self.entity_type_configs:
            storage_type = config.get('storage_type')
            prompt_template = config.get('prompt_template', 'generic')
            if storage_type:
                self.prompt_map[storage_type] = prompt_template
        
        logger.info(f"Entity summarizer initialized with {len(self.prompt_map)} type mappings")
    
    def summarize_entity(
        self,
        entity: Dict[str, Any],
        entity_type: str
    ) -> Optional[str]:
        """Generate summary for an entity
        
        Args:
            entity: Entity dictionary (including metadata)
            entity_type: Entity type (e.g., "Scrum/Task")
            
        Returns:
            Summary markdown or None on error
        """
        # Get prompt template name
        prompt_template = self.prompt_map.get(entity_type, 'generic')
        
        # Load prompt
        prompt = self._load_prompt(prompt_template)
        if not prompt:
            logger.error(f"Failed to load prompt template: {prompt_template}")
            return None
        
        # Prepare entity data as JSON
        entity_json = json.dumps(entity, indent=2)
        
        # Replace placeholder
        full_prompt = prompt.replace('{entity_json}', entity_json)
        
        # Generate summary
        try:
            logger.debug(f"Generating summary for {entity_type} #{entity.get('public_id')}")
            summary = self.llm.generate_completion(full_prompt)
            
            if summary:
                logger.info(f"Generated summary for #{entity.get('public_id')}")
                return summary.strip()
            else:
                logger.error(f"Empty summary returned for #{entity.get('public_id')}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None
    
    def _load_prompt(self, template_name: str) -> Optional[str]:
        """Load prompt template from file
        
        Args:
            template_name: Template name (without .txt extension)
            
        Returns:
            Prompt text or None if not found
        """
        prompt_path = self.prompts_dir / f"{template_name}.txt"
        
        if not prompt_path.exists():
            logger.warning(f"Prompt template not found: {prompt_path}")
            # Try generic fallback
            generic_path = self.prompts_dir / "generic.txt"
            if generic_path.exists():
                logger.info("Using generic prompt template as fallback")
                prompt_path = generic_path
            else:
                return None
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            logger.debug(f"Loaded prompt template: {prompt_path.name}")
            return prompt
        except Exception as e:
            logger.error(f"Error loading prompt {prompt_path}: {e}")
            return None
    
    def get_supported_types(self) -> list:
        """Get list of entity types with custom prompts
        
        Returns:
            List of entity types
        """
        return list(self.prompt_map.keys())

