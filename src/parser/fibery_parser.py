"""Parser for extracting Fibery.io entity metadata from time entry descriptions"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FiberyParser:
    """Parses Fibery.io entity metadata from time entry descriptions"""
    
    def __init__(self, entity_id_pattern: str = r"#(\d+)", 
                 tag_pattern: str = r"\[([^\]]+)\]"):
        """Initialize parser with regex patterns
        
        Args:
            entity_id_pattern: Regex pattern for entity ID
            tag_pattern: Regex pattern for bracketed tags
        """
        self.entity_id_pattern = re.compile(entity_id_pattern)
        self.tag_pattern = re.compile(tag_pattern)
    
    def parse(self, description: str) -> Dict[str, Any]:
        """Parse Fibery.io metadata from description
        
        Args:
            description: Time entry description
            
        Returns:
            Dictionary with parsed fields:
                - description_clean: Description without metadata
                - entity_id: Entity ID (e.g., "1112")
                - entity_database: Database name (e.g., "Scrum")
                - entity_type: Entity type (e.g., "Sub-bug")
                - project: Project name (e.g., "Moneyball")
                - is_matched: True if entity ID was found
        """
        if not description:
            return self._empty_result(description)
        
        # Find entity ID (search from the end)
        entity_id_match = None
        for match in self.entity_id_pattern.finditer(description):
            entity_id_match = match  # Keep last match (rightmost)
        
        # Find all bracketed tags
        tags = self.tag_pattern.findall(description)
        
        if not entity_id_match:
            # No entity ID found - unmatched entry
            return self._empty_result(description)
        
        # Extract entity ID
        entity_id = entity_id_match.group(1)
        
        # Find where metadata starts (the entity ID position)
        metadata_start = entity_id_match.start()
        
        # Clean description is everything before the metadata
        description_clean = description[:metadata_start].strip()
        
        # Parse tags (Database, Type, Project)
        # Tags are typically in order: [Database] [Type] [Project]
        entity_database = tags[0] if len(tags) >= 1 else None
        entity_type = tags[1] if len(tags) >= 2 else None
        project = tags[-1] if len(tags) >= 1 else None  # Last tag is project
        
        # If only one tag, it's ambiguous - could be database or project
        if len(tags) == 1:
            entity_database = tags[0]
            project = tags[0]
        
        result = {
            'description_clean': description_clean,
            'entity_id': entity_id,
            'entity_database': entity_database,
            'entity_type': entity_type,
            'project': project,
            'is_matched': True
        }
        
        logger.debug(f"Parsed: {description[:50]}... -> Entity #{entity_id}")
        return result
    
    def _empty_result(self, description: str) -> Dict[str, Any]:
        """Return empty result for unmatched entries
        
        Args:
            description: Original description
            
        Returns:
            Dictionary with description_clean and is_matched=False
        """
        return {
            'description_clean': description.strip() if description else '',
            'entity_id': None,
            'entity_database': None,
            'entity_type': None,
            'project': None,
            'is_matched': False
        }

