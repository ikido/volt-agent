"""Toggl API client for fetching time entries"""

import requests
from requests.auth import HTTPBasicAuth
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TogglClient:
    """Client for Toggl Reports API v3"""
    
    def __init__(self, api_token: str, workspace_id: int, 
                 base_url: str = "https://api.track.toggl.com/reports/api/v3",
                 timeout: int = 30, max_retries: int = 3):
        """Initialize Toggl API client
        
        Args:
            api_token: Toggl API token
            workspace_id: Workspace ID
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth = HTTPBasicAuth(api_token, "api_token")
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> requests.Response:
        """Make API request with retry logic
        
        Args:
            endpoint: API endpoint (without base URL)
            payload: Request payload
            
        Returns:
            Response object
            
        Raises:
            Exception: If max retries exceeded or unrecoverable error
        """
        url = f"{self.base_url}/{endpoint}"
        backoff = 60  # Start with 60 seconds
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"API Request to {url}")
                logger.debug(f"Payload: {payload}")
                
                response = requests.post(
                    url,
                    json=payload,
                    auth=self.auth,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code in [402, 429]:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit hit (HTTP {response.status_code}). Waiting {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    # Log the error response body for debugging
                    try:
                        error_body = response.json()
                        logger.error(f"API Error {response.status_code}: {error_body}")
                        logger.error(f"Request payload was: {payload}")
                    except:
                        logger.error(f"API Error {response.status_code}: {response.text}")
                        logger.error(f"Request payload was: {payload}")
                    
                    if attempt < self.max_retries - 1:
                        logger.info(f"Retrying after error (attempt {attempt + 1}/{self.max_retries})...")
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    else:
                        response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise
        
        raise Exception(f"Max retries ({self.max_retries}) exceeded")
    
    def get_time_entries(
        self,
        start_date: str,
        end_date: str,
        user_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch time entries from Toggl API with day-by-day chunking
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            user_ids: Optional list of user IDs to filter by
            
        Returns:
            List of time entry dictionaries
        """
        all_entries = []
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Fetch day-by-day to avoid pagination issues
        current = start
        day_count = 0
        
        logger.info(f"Fetching time entries from {start_date} to {end_date} (day-by-day)")
        
        while current <= end:
            day_count += 1
            day_str = current.strftime("%Y-%m-%d")
            logger.info(f"Fetching day {day_count}: {day_str}")
            
            entries = self._fetch_day(day_str, user_ids)
            all_entries.extend(entries)
            
            logger.info(f"  → Retrieved {len(entries)} entries for {day_str} (total: {len(all_entries)})")
            
            current += timedelta(days=1)
        
        logger.info(f"Successfully fetched {len(all_entries)} total time entries across {day_count} days")
        return all_entries
    
    def _fetch_day(self, date: str, user_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Fetch time entries for a single day with pagination
        
        Args:
            date: Date in YYYY-MM-DD format
            user_ids: Optional list of user IDs to filter by
            
        Returns:
            List of time entry dictionaries for that day
        """
        entries = []
        next_id = None
        first_row_number = None
        page_num = 0
        
        endpoint = f"workspace/{self.workspace_id}/search/time_entries"
        
        while True:
            page_num += 1
            payload = {
                "start_date": date,
                "end_date": date,
                "enrich_response": True,  # Get full data including user info
                "page_size": 50  # Max allowed by Toggl
            }
            
            if user_ids:
                payload["user_ids"] = user_ids
            if next_id:
                payload["first_id"] = next_id
            if first_row_number:
                payload["first_row_number"] = first_row_number
            
            response = self._make_request(endpoint, payload)
            
            # Parse response
            data = response.json()
            grouped_entries = data if isinstance(data, list) else data.get("data", [])
            
            if not grouped_entries:
                break
            
            # Unpack grouped entries - enrich_response groups by user/project/description
            # and nests actual time entries in time_entries array
            for group in grouped_entries:
                user_id = group.get('user_id')
                username = group.get('username')
                email = group.get('email')
                project_id = group.get('project_id')
                description = group.get('description', '')
                billable = group.get('billable')
                tag_ids = group.get('tag_ids', [])
                
                # Unpack each individual time entry
                for time_entry in group.get('time_entries', []):
                    entry = {
                        'id': time_entry.get('id'),
                        'workspace_id': self.workspace_id,
                        'user_id': user_id,
                        'username': username,
                        'user_email': email,
                        'description': description,
                        'start': time_entry.get('start'),
                        'stop': time_entry.get('stop'),
                        'duration': time_entry.get('seconds', 0),
                        'tags': tag_ids,
                        'project_id': project_id,
                        'project_name': None,  # Not in enriched response
                        'billable': billable
                    }
                    entries.append(entry)
            
            # Check for pagination headers
            next_id = response.headers.get("X-Next-ID")
            first_row_number = response.headers.get("X-Next-Row-Number")
            
            if not next_id or not first_row_number:
                break  # No more pages
            
            # Convert to integers (headers are always strings)
            try:
                next_id = int(next_id)
                first_row_number = int(first_row_number)
            except (ValueError, TypeError):
                logger.warning(f"Invalid pagination headers: next_id={next_id}, first_row_number={first_row_number}")
                break
        
        return entries

