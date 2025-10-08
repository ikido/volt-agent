"""Fibery API client for GraphQL and REST API access"""

import requests
import logging
import time
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class FiberyClient:
    """Client for interacting with Fibery.io API"""
    
    def __init__(
        self,
        api_token: str,
        workspace_name: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        max_requests_per_minute: int = 60
    ):
        """Initialize Fibery API client
        
        Args:
            api_token: Fibery API token
            workspace_name: Workspace name (subdomain)
            base_url: Base URL (defaults to https://{workspace_name}.fibery.io)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            max_requests_per_minute: Rate limit
        """
        self.api_token = api_token
        self.workspace_name = workspace_name
        self.base_url = base_url or f"https://{workspace_name}.fibery.io"
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_rpm = max_requests_per_minute
        self.request_times = deque()
        
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Initialized Fibery client for workspace: {workspace_name}")
    
    def _wait_if_rate_limited(self):
        """Wait if rate limit is reached"""
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        
        # If at limit, wait
        if len(self.request_times) >= self.max_rpm:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    def graphql_query(
        self,
        database: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute GraphQL query
        
        Args:
            database: Database/space name (e.g., "Scrum")
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Response data or None on error
        """
        url = f"{self.base_url}/api/graphql/space/{database}"
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        return self._make_request('POST', url, json=payload)
    
    def rest_query(self, command: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute REST API command
        
        Args:
            command: Command name (e.g., "fibery.entity/query")
            args: Command arguments
            
        Returns:
            Response data or None on error
        """
        url = f"{self.base_url}/api/commands"
        payload = {
            'command': command,
            'args': args
        }
        
        return self._make_request('POST', url, json=payload)
    
    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments
            
        Returns:
            Response JSON or None on error
        """
        self._wait_if_rate_limited()
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response.json()
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = min(2 ** attempt, 60)
                    logger.warning(f"Rate limited (429), waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code >= 500:
                    # Server error - retry
                    wait_time = min(2 ** attempt, 60)
                    logger.warning(f"Server error ({response.status_code}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                else:
                    # Client error - don't retry
                    logger.error(f"HTTP {response.status_code}: {response.text}")
                    return None
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        logger.error(f"Failed after {self.max_retries} attempts")
        return None
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all workspace users
        
        Returns:
            List of user dictionaries
        """
        logger.info("Fetching Fibery users...")
        
        result = self.rest_query(
            command='fibery.entity/query',
            args={
                'query': {
                    'q/from': 'fibery/user',
                    'q/select': [
                        'fibery/id',
                        'user/name',
                        'user/email',
                        'user/role'
                    ],
                    'q/limit': 'q/no-limit'
                }
            }
        )
        
        if result and result.get('success'):
            users = result.get('result', [])
            logger.info(f"Fetched {len(users)} users")
            return users
        
        logger.error("Failed to fetch users")
        return []
    
    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get workspace schema
        
        Returns:
            Schema dictionary or None on error
        """
        logger.info("Fetching Fibery schema...")
        
        result = self.rest_query(
            command='fibery.schema/query',
            args={}
        )
        
        if result:
            logger.info("Schema fetched successfully")
            return result
        
        logger.error("Failed to fetch schema")
        return None

