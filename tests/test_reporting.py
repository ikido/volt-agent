"""Unit tests for report generation"""

import pytest
import tempfile
from pathlib import Path
from src.reporting.generator import ReportGenerator


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_format_entries_for_llm_matched(temp_output_dir):
    """Test formatting matched entries for LLM"""
    gen = ReportGenerator(temp_output_dir)
    
    entries = [
        {
            'entity_id': '1234',
            'entity_database': 'Backend',
            'entity_type': 'Bug',
            'project': 'AuthService',
            'description_clean': 'Fixed authentication bug',
            'total_duration': 7200,  # 2 hours
            'is_matched': True
        }
    ]
    
    result = gen.format_entries_for_llm(entries)
    
    assert '#1234' in result
    assert '[Backend]' in result
    assert '[Bug]' in result
    assert '[AuthService]' in result
    assert 'Fixed authentication bug' in result
    assert '2.0h' in result


def test_format_entries_for_llm_unmatched(temp_output_dir):
    """Test formatting unmatched entries for LLM"""
    gen = ReportGenerator(temp_output_dir)
    
    entries = [
        {
            'description_clean': 'Team standup meeting',
            'total_duration': 1800,  # 0.5 hours
            'is_matched': False
        }
    ]
    
    result = gen.format_entries_for_llm(entries)
    
    assert 'Team standup meeting' in result
    assert '0.5h' in result


def test_generate_individual_report(temp_output_dir):
    """Test generating individual report"""
    gen = ReportGenerator(temp_output_dir)
    
    matched_entries = [
        {
            'entity_id': '1234',
            'entity_database': 'Backend',
            'entity_type': 'Bug',
            'project': 'AuthService',
            'description_clean': 'Fixed bug',
            'total_duration': 7200,
            'is_matched': True
        }
    ]
    
    unmatched_entries = [
        {
            'description_clean': 'Team meeting',
            'total_duration': 1800,
            'is_matched': False
        }
    ]
    
    report = gen.generate_individual_report(
        user_email='john@example.com',
        start_date='2025-09-23',
        end_date='2025-09-29',
        matched_entries=matched_entries,
        unmatched_entries=unmatched_entries,
        matched_summary='Summary of matched work',
        unmatched_summary='Summary of unmatched work',
        timestamp='2025-09-29-14-30'
    )
    
    assert 'john@example.com' in report
    assert '2025-09-23' in report
    assert '2.5 hours' in report  # Total hours
    assert 'Summary of matched work' in report
    assert 'Summary of unmatched work' in report


def test_generate_team_report(temp_output_dir):
    """Test generating team report"""
    gen = ReportGenerator(temp_output_dir)
    
    user_stats = [
        {
            'user_email': 'john@example.com',
            'total_seconds': 28800,  # 8 hours
            'matched_seconds': 25200,  # 7 hours
            'unmatched_seconds': 3600  # 1 hour
        },
        {
            'user_email': 'jane@example.com',
            'total_seconds': 21600,  # 6 hours
            'matched_seconds': 18000,  # 5 hours
            'unmatched_seconds': 3600  # 1 hour
        }
    ]
    
    report = gen.generate_team_report(
        start_date='2025-09-23',
        end_date='2025-09-29',
        user_stats=user_stats,
        team_summary='Team worked on various projects',
        individual_report_paths=['/tmp/report1.md', '/tmp/report2.md'],
        timestamp='2025-09-29-14-30'
    )
    
    assert 'Team Activity Report' in report
    assert 'john@example.com' in report
    assert 'jane@example.com' in report
    assert '14.0 hours' in report  # Total team hours
    assert 'Team worked on various projects' in report

