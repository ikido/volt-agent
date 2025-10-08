# PRD: Fibery Entity Context Integration - Implementation Plan

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** 📝 Planning  

> **📚 Part of:** [Fibery Entity Context Integration](./README.md)  
> **Related Docs:** [Core Requirements](./PRD_Core.md) | [Database Schema](./PRD_Database_Schema.md) | [Configuration](./PRD_Configuration.md)

---

## Overview

This document outlines the implementation plan, success metrics, risks, and future enhancements for the Fibery Entity Context Integration feature.

---

## 1. Implementation Phases

### Phase 1: Foundation

**Goal:** Set up core infrastructure for Fibery API integration

**Tasks:**
- Set up Fibery API client with authentication
- Implement user fetching and email matching
- Create database schema extensions (2 cache tables)

**Deliverables:**
- `src/fibery/client.py` - Fibery API client (GraphQL + REST)
- `src/fibery/user_matcher.py` - User matching logic
- Database migration script with new tables

**Success Criteria:**
- Can authenticate with Fibery API
- Can fetch and cache Fibery users
- Database tables created successfully

---

### Phase 2: Entity Fetching

**Goal:** Implement entity fetching for all configured entity types

**Tasks:**
- Implement entity fetching by public ID
- Support multiple entity types (Task, Bug, Feature, etc.)
- Implement entity caching with upsert logic
- Handle API errors gracefully
- Fetch and cache comments (nested structure)

**Deliverables:**
- `src/fibery/entity_fetcher.py` - Entity fetching logic
- `src/fibery/models.py` - Data models for entities
- GraphQL query templates for each entity type
- Entity caching mechanism (upsert to database)

**Success Criteria:**
- Can fetch entities by public ID
- Supports all 14 configured entity types
- Caching reduces API calls significantly
- Graceful error handling for missing entities
- Comments stored as nested JSON structure

---

### Phase 3: LLM Summarization

**Goal:** Generate AI summaries for entities using OpenAI

**Tasks:**
- Implement prompt loading from text files
- Implement entity-type-specific prompt selection
- Generate summaries via OpenAI API
- Cache summaries directly on entity rows
- Handle generic/unknown entity types with fallback prompts

**Deliverables:**
- `src/llm/summarizer.py` - LLM summarization logic
- Prompt template loading mechanism
- Entity summary generation and caching
- Token usage tracking

**Success Criteria:**
- Can generate summaries for all entity types
- Summaries cached in `fibery_entities.summary_md`
- Generic fallback for unknown types works
- Summaries are factual and concise

---

### Phase 4: Work Alignment Analysis

**Goal:** Detect discrepancies between Toggl and Fibery

**Tasks:**
- Compare Toggl entries with Fibery entity states
- Identify "Fibery not updated" issues
- Identify "Missing in Toggl" issues
- Generate markdown alignment report

**Deliverables:**
- `src/analysis/alignment_analyzer.py` - Alignment logic
- Discrepancy detection algorithms
- `work_alignment_YYYY-MM-DD.md` report generation

**Success Criteria:**
- Identifies entities logged but not updated in Fibery
- Identifies entities assigned but not logged in Toggl
- Generates actionable markdown report with recommendations
- Report includes priority-based action items

---

### Phase 5: Enhanced Reporting

**Goal:** Create comprehensive reports with Fibery context

**Tasks:**
- Create enriched individual report template
- Create enhanced team summary template
- Integrate entity summaries into reports
- Add references to analysis markdown files
- Polish formatting and presentation

**Deliverables:**
- `src/reporting/enriched_generator.py` - Enhanced report generator
- Individual report with entity context
- Team summary with project grouping
- Cross-references to analysis files

**Success Criteria:**
- Individual reports show full entity context with summaries
- Team reports group related work by project
- Reports link to analysis markdown files
- All sections properly formatted

---

### Phase 6: Analysis & Validation

**Goal:** Implement analysis and validation features (output as markdown reports)

**Tasks:**
- Unknown entity type detection and reporting
- Configuration validation against live schema
- Self-improvement recommendations
- CLI commands for analysis

**Deliverables:**
- `src/analysis/unknown_types.py` - Unknown type detection
- `src/analysis/config_validator.py` - Configuration validation
- `unknown_entities_YYYY-MM-DD.md` generation
- `config_validation_YYYY-MM-DD.md` generation
- CLI commands: `--validate-config-only`, `--analysis-only`

**Success Criteria:**
- Detects and reports unknown entity types in markdown
- Validates configuration against workspace in markdown
- Provides clear, actionable recommendations
- All analysis output as dedicated markdown files

---

## 2. Success Metrics

### 2.1 Functional Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Entity fetch success rate | >95% | Successful API calls / Total attempts |
| User matching accuracy | >90% | Correct matches / Total users |
| Summary generation coverage | 100% | Entities with summaries / Total entities |
| Discrepancy detection accuracy | >95% | Correct detections / Manual review |


---

## 3. Glossary

| Term | Definition |
|------|------------|
| **Entity** | A work item in Fibery (Task, Bug, Feature, etc.) |
| **Public ID** | Human-readable entity ID in Fibery (e.g., "7658") |
| **Fibery ID** | Internal UUID used by Fibery API |
| **Enrichment** | Adding Fibery context to Toggl reports |
| **Work Alignment** | Consistency between Toggl logs and Fibery state |
| **Discrepancy** | Mismatch between Toggl and Fibery records |
| **Entity Type** | Category of entity (Task, Bug, Sub-bug, etc.) |
| **Database** | Fibery workspace database (e.g., "Scrum", "Kanban") |
| **Relation** | Connection between entities in Fibery |
| **Schema** | Structure of Fibery workspace (types and fields) |
| **Cache Hit Rate** | Percentage of requests served from cache |

---

## 4. References

### Documentation
1. **Fibery API Documentation**
   - Overview: https://the.fibery.io/@public/User_Guide/Guide/Fibery-API-Overview-279
   - Commands: https://api.fibery.io/
   
2. **Existing System**
   - Toggl Reports PRD: `/docs/features/1-toggl-reports/PRD_Toggl_Team_Activity_Report.md`
   - Fibery Parser: `/src/parser/fibery_parser.py`

3. **OpenAI API**
   - Chat Completions: https://platform.openai.com/docs/api-reference/chat

### Related PRDs
- **[PRD_Core.md](./PRD_Core.md)** - Core requirements and functional specs
- **[PRD_Database_Schema.md](./PRD_Database_Schema.md)** - Database design
- **[PRD_Configuration.md](./PRD_Configuration.md)** - Configuration and prompts
- **[PRD_Report_Formats.md](./PRD_Report_Formats.md)** - Report templates
- **[PRD_Schema_Management.md](./PRD_Schema_Management.md)** - Analysis & validation (markdown reports)

---

**End of Implementation Document**

