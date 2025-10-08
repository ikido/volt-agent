"""Entity fetcher for Fibery entities with type-specific queries"""

import logging
from typing import Dict, Any, Optional, List
from .client import FiberyClient
from .models import FiberyEntity

logger = logging.getLogger(__name__)


class EntityFetcher:
    """Fetches Fibery entities by public ID with type-specific queries"""
    
    def __init__(self, client: FiberyClient, entity_type_configs: List[Dict[str, Any]]):
        """Initialize entity fetcher
        
        Args:
            client: FiberyClient instance
            entity_type_configs: List of entity type configurations
        """
        self.client = client
        self.entity_type_configs = entity_type_configs
        
        # Build lookup map: storage_type -> config
        self.config_map = {
            config['storage_type']: config
            for config in entity_type_configs
        }
        
        logger.info(f"Entity fetcher initialized with {len(self.config_map)} entity type configs")
    
    def fetch_entity(
        self,
        entity_type: str,
        public_id: str,
        use_cache: bool = False
    ) -> Optional[FiberyEntity]:
        """Fetch entity by public ID
        
        Args:
            entity_type: Entity type in storage format (e.g., "Scrum/Task")
            public_id: Public ID (e.g., "7658")
            use_cache: Whether to use cached data (not implemented here - handled by caller)
            
        Returns:
            FiberyEntity instance or None if not found
        """
        # Get configuration for this entity type
        config = self.config_map.get(entity_type)
        
        if not config:
            logger.warning(f"No configuration found for entity type: {entity_type}")
            return self._fetch_entity_generic(entity_type, public_id)
        
        # Build GraphQL query based on configuration
        query = self._build_query(config)
        
        # Execute query
        result = self.client.graphql_query(
            database=config['database'],
            query=query,
            variables={'searchId': public_id}
        )
        
        if not result:
            logger.error(f"Failed to fetch entity {entity_type} #{public_id}")
            return None
        
        # Check for GraphQL errors
        if 'errors' in result:
            for error in result['errors']:
                logger.error(f"GraphQL error: {error.get('message')}")
            return None
        
        # Extract entity from result
        data = result.get('data', {})
        query_function = config['query_function']
        entities = data.get(query_function, [])
        
        if not entities:
            logger.warning(f"Entity {entity_type} #{public_id} not found")
            return None
        
        entity_data = entities[0]
        entity = FiberyEntity(entity_data, entity_type)
        
        logger.info(f"Fetched entity #{public_id}: {entity.entity_name[:50]}")
        return entity
    
    def _build_query(self, config: Dict[str, Any]) -> str:
        """Build GraphQL query from configuration
        
        Args:
            config: Entity type configuration
            
        Returns:
            GraphQL query string
        """
        query_function = config['query_function']
        fields = config['fields']
        
        # Build field selection
        field_lines = ['id', 'publicId']
        for field_name, field_query in fields.items():
            field_lines.append(field_query)
        
        fields_str = '\n    '.join(field_lines)
        
        query = f"""
query getEntity($searchId: String) {{
  {query_function}(publicId: {{is: $searchId}}) {{
    {fields_str}
  }}
}}
"""
        return query.strip()
    
    def _fetch_entity_generic(
        self,
        entity_type: str,
        public_id: str
    ) -> Optional[FiberyEntity]:
        """Fetch entity using generic approach (fallback for unknown types)
        
        Args:
            entity_type: Entity type (e.g., "Scrum/Task")
            public_id: Public ID
            
        Returns:
            FiberyEntity instance or None
        """
        logger.warning(f"Using generic fetch for unknown type: {entity_type}")
        
        # Try to parse entity type to guess GraphQL query
        parts = entity_type.split('/')
        if len(parts) != 2:
            logger.error(f"Invalid entity type format: {entity_type}")
            return None
        
        database, type_name = parts
        
        # Try common query patterns
        query_function_options = [
            f"find{type_name}s",  # e.g., findTasks
            f"find{type_name.replace('-', '')}s",  # e.g., findQATasks
            f"find{type_name.replace(' ', '')}s",  # e.g., findDesignFeatures
        ]
        
        for query_function in query_function_options:
            query = f"""
query getEntity($searchId: String) {{
  {query_function}(publicId: {{is: $searchId}}) {{
    id
    publicId
    name
    description
    state {{ name }}
  }}
}}
"""
            
            result = self.client.graphql_query(
                database=database,
                query=query,
                variables={'searchId': public_id}
            )
            
            if result and 'data' in result and not result.get('errors'):
                entities = result['data'].get(query_function, [])
                if entities:
                    entity_data = entities[0]
                    entity = FiberyEntity(entity_data, entity_type)
                    logger.info(f"Generic fetch succeeded for #{public_id}")
                    return entity
        
        logger.error(f"Generic fetch failed for {entity_type} #{public_id}")
        return None
    
    def get_configured_types(self) -> List[str]:
        """Get list of configured entity types
        
        Returns:
            List of entity type names
        """
        return list(self.config_map.keys())
    
    def is_type_configured(self, entity_type: str) -> bool:
        """Check if entity type is configured
        
        Args:
            entity_type: Entity type to check
            
        Returns:
            True if configured
        """
        return entity_type in self.config_map

