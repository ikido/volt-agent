"""Unit tests for TogglClient"""

import pytest
import responses
from src.toggl.client import TogglClient


@responses.activate
def test_fetch_time_entries_single_page():
    """Test fetching time entries with single page"""
    # Mock API response
    responses.add(
        responses.POST,
        "https://api.track.toggl.com/reports/api/v3/workspace/123/search/time_entries",
        json=[
            {
                'user_id': 456,
                'username': 'John Doe',
                'email': 'john@example.com',
                'project_id': 789,
                'description': 'Test task #1234 [Backend] [Bug] [Project]',
                'billable': False,
                'tag_ids': [],
                'time_entries': [
                    {
                        'id': 1001,
                        'start': '2025-09-23T09:00:00Z',
                        'stop': '2025-09-23T10:00:00Z',
                        'seconds': 3600
                    }
                ]
            }
        ],
        status=200,
        headers={}  # No pagination headers
    )
    
    client = TogglClient(api_token='test_token', workspace_id=123)
    entries = client.get_time_entries('2025-09-23', '2025-09-23')
    
    assert len(entries) == 1
    assert entries[0]['id'] == 1001
    assert entries[0]['user_email'] == 'john@example.com'
    assert entries[0]['duration'] == 3600


@responses.activate
def test_fetch_time_entries_multiple_days():
    """Test fetching entries across multiple days"""
    # Mock API responses for two days
    for day in ['2025-09-23', '2025-09-24']:
        responses.add(
            responses.POST,
            "https://api.track.toggl.com/reports/api/v3/workspace/123/search/time_entries",
            json=[
                {
                    'user_id': 456,
                    'username': 'John Doe',
                    'email': 'john@example.com',
                    'project_id': 789,
                    'description': f'Work on {day}',
                    'billable': False,
                    'tag_ids': [],
                    'time_entries': [
                        {
                            'id': 1000 + int(day[-2:]),
                            'start': f'{day}T09:00:00Z',
                            'stop': f'{day}T10:00:00Z',
                            'seconds': 3600
                        }
                    ]
                }
            ],
            status=200,
            headers={}
        )
    
    client = TogglClient(api_token='test_token', workspace_id=123)
    entries = client.get_time_entries('2025-09-23', '2025-09-24')
    
    assert len(entries) == 2


@responses.activate
def test_rate_limit_retry():
    """Test retry logic on rate limit"""
    # First request returns 429, second succeeds
    responses.add(
        responses.POST,
        "https://api.track.toggl.com/reports/api/v3/workspace/123/search/time_entries",
        json={'error': 'Too many requests'},
        status=429
    )
    
    responses.add(
        responses.POST,
        "https://api.track.toggl.com/reports/api/v3/workspace/123/search/time_entries",
        json=[],
        status=200,
        headers={}
    )
    
    client = TogglClient(api_token='test_token', workspace_id=123, max_retries=2)
    entries = client.get_time_entries('2025-09-23', '2025-09-23')
    
    # Should succeed after retry
    assert entries == []

