"""Unit tests for FiberyParser"""

import pytest
from src.parser.fibery_parser import FiberyParser


def test_parser_full_metadata():
    """Test parsing with full metadata"""
    parser = FiberyParser()
    description = "Fixed bug #1234 [Backend] [Bug] [AuthService]"
    
    result = parser.parse(description)
    
    assert result['is_matched'] is True
    assert result['entity_id'] == "1234"
    assert result['entity_database'] == "Backend"
    assert result['entity_type'] == "Bug"
    assert result['project'] == "AuthService"
    assert result['description_clean'] == "Fixed bug"


def test_parser_no_metadata():
    """Test parsing without any metadata"""
    parser = FiberyParser()
    description = "Team meeting"
    
    result = parser.parse(description)
    
    assert result['is_matched'] is False
    assert result['entity_id'] is None
    assert result['description_clean'] == "Team meeting"


def test_parser_only_entity_id():
    """Test parsing with only entity ID"""
    parser = FiberyParser()
    description = "Research #5678"
    
    result = parser.parse(description)
    
    assert result['is_matched'] is True
    assert result['entity_id'] == "5678"
    assert result['description_clean'] == "Research"


def test_parser_non_english():
    """Test parsing with non-English characters"""
    parser = FiberyParser()
    description = "? Нет полей Stage, Next action, Owner, Alternate names #1112 [Scrum] [Sub-bug] [Moneyball]"
    
    result = parser.parse(description)
    
    assert result['is_matched'] is True
    assert result['entity_id'] == "1112"
    assert result['entity_database'] == "Scrum"
    assert result['entity_type'] == "Sub-bug"
    assert result['project'] == "Moneyball"
    assert result['description_clean'] == "? Нет полей Stage, Next action, Owner, Alternate names"


def test_parser_empty_description():
    """Test parsing with empty description"""
    parser = FiberyParser()
    
    result = parser.parse("")
    
    assert result['is_matched'] is False
    assert result['description_clean'] == ""


def test_parser_only_tags_no_id():
    """Test parsing with tags but no entity ID"""
    parser = FiberyParser()
    description = "Some work [Backend] [Task]"
    
    result = parser.parse(description)
    
    assert result['is_matched'] is False

