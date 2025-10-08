# PRD: Fibery Entity Context Integration - Core Requirements

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** 📝 Planning  

> **📚 Part of:** [Fibery Entity Context Integration](./README.md)  
> **Related Docs:** [API Guide](../Fibery_API_Integration_Guide.md) | [Database Schema](./PRD_Database_Schema.md) | [Configuration](./PRD_Configuration.md)

---

## 1. Executive Summary

This document outlines the core requirements for enhancing the existing Toggl Team Activity Report Generator by integrating rich contextual information from Fibery.io entities. The system will match time entries to Fibery entities, fetch detailed entity information (descriptions, comments, related entities), generate AI summaries, and provide comprehensive activity analysis including work alignment and discrepancy detection.

---

## 2. Objectives

### Primary Goal
Transform the existing Toggl reports by adding deep contextual information from Fibery, enabling better understanding of what team members actually worked on and identifying misalignments between time tracking and project management systems.

### Key Deliverables
1. **Fibery API Client**: Fetch entities, users, and workspace schema from Fibery
2. **Entity Enrichment Pipeline**: Match Toggl entries to Fibery entities and fetch detailed context
3. **AI Summarization**: Generate concise, entity-type-specific summaries using OpenAI
4. **Work Alignment Analysis**: Identify discrepancies between Toggl and Fibery records
5. **Enhanced Report Structure**: Person-by-person reports with full entity context
6. **Self-Maintaining System**: Detect unknown entity types and schema changes
7. **Configuration Monitoring**: Automated validation and improvement recommendations

---

## 3. Background & Context

### 3.1 Current State
- ✅ Toggl reports extract entity IDs from time entry descriptions (e.g., `#7658`)
- ✅ Entity metadata parsed: ID, Database, Type, Project
- ✅ Reports show **what entity ID** was worked on but not **what the entity actually is**
- ❌ No contextual information about the entity's purpose, description, or status
- ❌ No validation that entities are properly tracked in Fibery
- ❌ No detection of work done but not logged properly

### 3.2 Problem Statement
**Current limitation**: Team members see that someone spent 17.7 hours on "#7658 [Scrum] [Task]" but have no context about what that actually means.

**This applies to ALL entity types logged in Toggl:**

**Known entity types we support** (configured with specific context logic):

**Scrum Database:**
- Scrum/Task - Development tasks
- Scrum/Sub-task - Subtasks under main tasks
- Scrum/Bug - Bug fixes
- Scrum/Sub-bug - Sub-items for bugs
- Scrum/Feature - High-level features
- Scrum/Epic - Large initiatives spanning multiple features
- Scrum/Build - Build deployments
- Scrum/Release - Release management
- Scrum/Hotfix - Urgent fixes
- Scrum/Chore - Maintenance and operational work
- Scrum/Sprint - Sprint planning and tracking

**Design Database:**
- Design/Design Feature - Design feature requirements and specs
- Design/Work Version - Design work versions and iterations

*(Add more as discovered)*

**Unknown entity types:**
- The system should gracefully handle entity types not yet configured
- Flag them in reports for investigation
- Use generic context extraction as fallback
- Track them for future configuration updates

**Entity-level Context (What was worked on?):**
- What is this entity about?
- What problem does it solve?
- When did work on this start? What's the ETA?
- What's the current state/status?
- Are there comments or discussions providing context?
- Is the work properly reflected in Fibery's state?

**Parent/Feature Context (The Bigger Picture):**
- Is this entity part of a larger feature or initiative?
- When did work on the parent feature start?
- What has been completed so far on the feature?
- What work is still remaining?
- What's the ETA for the entire feature?
- How does this entity fit into the overall delivery timeline?

**Entity-Type-Specific Context:**
Different entity types need different context:

**Development Work:**
- **Tasks/Sub-tasks:** Focus on parent feature, related issues, blocking items, completion status
- **Bugs/Sub-bugs:** Focus on parent feature, severity, related issues, resolution details
- **Chores:** Focus on operational/maintenance value, priority, completion status

**Strategic Planning:**
- **Features:** Focus on overall progress, related tasks/bugs, user requests, release timeline
- **Epics:** Focus on strategic value, included features, overall progress across features
- **Sprints:** Focus on sprint goals, completed work, timeline

**Deployment:**
- **Builds/Releases:** Focus on included features/bugs, deployment timeline, testing status
- **Hotfixes:** Focus on urgency, impact, related bugs, deployment priority

**Design Work:**
- **Design Features:** Focus on design requirements, work versions, connection to Scrum features
- **Work Versions:** Focus on design iteration, review outcome, approval status

**Why this matters:**
Understanding both the individual entity and the larger context helps answer critical questions:
- *"Is this entity part of strategic work or a one-off?"*
- *"Are we on track to deliver the feature this is part of?"*
- *"Should we be concerned about the time spent here?"*
- *"What's the impact if this work is delayed?"*
- *"Does the context justify the time investment?"*

### 3.3 Proposed Solution
Fetch complete entity information from Fibery and enrich reports with **entity-type-aware context**:

**Entity-level Information (for ALL entity types):**
1. Entity name and description (what it's about)
2. Current state and status
3. Timeline: When started, when completed, planned dates
4. Comments and discussions (important context)
5. Entity-type-specific fields (e.g., severity for bugs, release date for builds)

**Parent/Related Entity Information:**
6. Parent feature details and timeline (if applicable)
7. Feature progress: what's done, what's left
8. Feature ETA and delivery status
9. Related entities: user requests, bugs, tasks, etc.
10. Business context and priority

**Entity-Type-Specific Logic:**

**Development Work:**
- **Tasks/Sub-tasks:** Fetch parent feature, parent task (for sub-tasks with nested feature context), related issues, assignees
- **Bugs/Sub-bugs:** Fetch parent feature, parent bug (for sub-bugs with nested feature context), severity, related issues
- **Chores:** Fetch priority, completion status, operational context

**Strategic Planning:**
- **Features:** Fetch child tasks/bugs, user requests, release plan, progress metrics
- **Epics:** Fetch related features, overall progress, strategic objectives
- **Sprints:** Fetch sprint work items, goals, timeline

**Deployment:**
- **Builds/Releases:** Fetch included features/bugs, deployment status, testing state
- **Hotfixes:** Fetch related bugs, urgency info, deployment timeline

**Design Work:**
- **Design Features:** Fetch work versions, related Scrum features, design timeline
- **Work Versions:** Fetch parent design feature (with nested Scrum feature), review outcome, iteration status

**Nested Relationship Handling:**
For entities like Sub-tasks and Work Versions that only make sense in context, fetch multi-level relationships:
- Sub-task → Parent Task → Feature (3 levels)
- Sub-bug → Parent Bug → Feature (3 levels)
- Work Version → Design Feature → Scrum Feature (3 levels)

This ensures reports show the full context chain, not just the immediate parent.

**Alignment & Validation:**
11. Discrepancy analysis (work logged in Toggl but not in Fibery, or vice versa)
12. Timeline validation (are dates aligned between systems?)
13. State consistency checking

**Flexible Summarization:**
14. Entity-type-specific LLM prompts for optimal summaries
15. Different templates for different entity types

**Maintainability & Evolution:**
16. **Unknown Entity Detection:** Detect and report entity types not in configuration (markdown output)
17. **Work Alignment Analysis:** Flag discrepancies between Toggl and Fibery (markdown output)
18. **Configuration Validation:** Validate config against live schema (markdown output)
19. **Self-Improving:** Reports suggest configuration improvements (markdown output)

**Note:** All analysis outputs to dedicated markdown reports, not stored in database (database is just a cache).

**Result:** Reports that answer not just *"what was worked on"* but *"why it matters, where it's going, and when it will be done"* - **regardless of entity type**

---

## 4. Functional Requirements

> **📚 Related Documentation:**
> - **API Details:** [Fibery API Integration Guide](../Fibery_API_Integration_Guide.md)
> - **Workspace Structure:** [workspace-structure/README.md](../workspace-structure/README.md)
> - **Database Schema:** [PRD_Database_Schema.md](./PRD_Database_Schema.md)
> - **Configuration:** [PRD_Configuration.md](./PRD_Configuration.md)

### 4.1 Enhanced Command-Line Interface

Extend existing CLI with Fibery-specific options:

| Argument | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `--enrich-fibery` | Boolean flag | No | Enable Fibery entity enrichment | `--enrich-fibery` |
| `--fibery-analysis` | Boolean flag | No | Enable work alignment analysis | `--fibery-analysis` |
| `--skip-summarization` | Boolean flag | No | Skip LLM summarization (dev mode) | `--skip-summarization` |

**Example Usage:**
```bash
# Generate report with Fibery enrichment
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery

# Full analysis including discrepancy detection
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery \
  --fibery-analysis
```

### 4.2 Fibery API Integration

**📚 Full API documentation:** [Fibery_API_Integration_Guide.md](../Fibery_API_Integration_Guide.md)

#### 4.2.1 Authentication
- **Method**: Token-based authentication
- **Header**: `Authorization: Token {api_token}`
- **Credentials**: Stored in `.env` file
- **Workspace:** wearevolt.fibery.io

```bash
# .env file
FIBERY_API_TOKEN=your_fibery_api_token_here
FIBERY_WORKSPACE_NAME=wearevolt
```

#### 4.2.2 API Approach: GraphQL (Recommended)

**Why GraphQL:**
- ✅ Clean, intuitive syntax
- ✅ Easy filtering by public ID
- ✅ Type-safe queries
- ✅ Simpler to maintain

**Base Endpoint:**
```
https://wearevolt.fibery.io/api/graphql/space/{database}
```

**Quick Example - Fetch Task by ID:**
```graphql
query getTask($searchId: String) {
  findTasks(publicId: {is: $searchId}) {
    id
    publicId
    name
    state { name }
    completionDate
    startedDate
    feature {
      publicId
      name
    }
  }
}
```

**Variables:**
```json
{"searchId": "7658"}
```

**Sample Response:**
```json
{
  "data": {
    "findTasks": [{
      "id": "9b19265e-beaa-4a72-8c0f-3334a3a6d50b",
      "publicId": "7658",
      "name": "Provision AWS Infrastructure in Huber AWS Org ID",
      "state": {"name": "In progress"},
      "completionDate": null,
      "startedDate": "2025-09-22T12:01:32.155Z",
      "feature": {
        "publicId": "1575",
        "name": "Create AWS Infrastructure for Huber"
      }
    }]
  }
}
```

**📚 Complete API documentation:** [Fibery API Integration Guide](../Fibery_API_Integration_Guide.md)

#### 4.2.3 Entity Type Configuration

**Actual workspace entity types** (from wearevolt.fibery.io):

**Key principle:** Each entity type can have its own:
- Field mappings (what fields to fetch)
- Summarization prompt (how to summarize)
- Related entity logic (what to fetch as context)
- Timeline fields (which dates matter)

**Example configuration** (see [PRD_Configuration.md](./PRD_Configuration.md) for complete config):

```yaml
# config/config.yaml - Fibery section
fibery:
  api_base_url: "https://wearevolt.fibery.io"
  use_graphql: true  # Use GraphQL API (recommended)
  
  entity_types:
    - storage_type: "Scrum/Task"
      graphql_type: "Task"
      query_function: "findTasks"
      database: "Scrum"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        completion_date: "completionDate"
        feature: "feature { publicId name }"
```

### 4.3 Entity Enrichment Pipeline

#### 4.3.1 Directory Structure

```
./tmp/run_{timestamp}/
├── toggl_data/
│   ├── user1@example.com/
│   │   ├── 01_raw_toggl_report.md
│   │   ├── 02_entity_7658_raw.json
│   │   ├── 03_entity_7658_summary.md
│   │   ├── 04_entity_7521_raw.json
│   │   ├── 05_entity_7521_summary.md
│   │   └── 06_enriched_report.md
│   └── user2@example.com/
│       └── ...
├── fibery_analysis/
│   ├── user1@example.com/
│   │   ├── entities_in_fibery.json
│   │   ├── discrepancies.md
│   │   └── work_alignment.md
│   └── user2@example.com/
│       └── ...
├── combined_individual_reports.md
└── team_summary.md
```

#### 4.3.2 Step-by-Step Process

**Step 1: Create User Subfolder**
```
./tmp/run_2025-10-07-10-41/toggl_data/alex.akilin@wearevolt.com/
```

**Step 2: Generate Base Toggl Report**

File: `01_raw_toggl_report.md`
```markdown
# Toggl Time Entries: alex.akilin@wearevolt.com
**Period:** 2025-09-29 to 2025-10-05

## Matched Entities (53.2 hours)

### #7658 [Scrum] [Task] [Volt - Internal]
- **Time Spent:** 17.7 hours
- **Description:** Provisioned AWS Infrastructure in Huber AWS Org ID
- **Fibery Context:** [Loading...]
```

**Step 3: Fetch Fibery Entity Data**

For each entity ID (e.g., 7658):
1. Determine entity type from parsed metadata (`[Scrum] [Task]`)
2. Fetch entity using appropriate Fibery query
3. Save raw response: `02_entity_7658_raw.json`

**Step 4: Generate Entity Summary**

Use OpenAI to summarize entity data:

Input: Raw JSON from Fibery  
Output: `03_entity_7658_summary.md`

```markdown
## Entity #7658: Deploy AWS Infrastructure

**Type:** Task | **Status:** Done | **Database:** Scrum

**Description:**
Provision complete AWS infrastructure in Huber AWS Organization including VPC, subnets, security groups, and IAM roles for production environment.

**Related Entities:**
- Feature #1234: Infrastructure Setup
- User Request #456: AWS Environment for Huber

**Timeline:**
- Started: 2025-09-29
- Completed: 2025-10-05
```

**Step 5: Update Report with Enriched Context**

File: `06_enriched_report.md`
```markdown
# Enriched Activity Report: alex.akilin@wearevolt.com
**Period:** 2025-09-29 to 2025-10-05

## Matched Entities (53.2 hours)

### #7658: Deploy AWS Infrastructure
- **Time Spent:** 17.7 hours
- **Type:** Task | **Status:** Done | **Database:** Scrum

**What was worked on:**
Provision complete AWS infrastructure in Huber AWS Organization...

**Context:**
- Part of Feature #1234: Infrastructure Setup
- Status: Successfully completed on 2025-10-05
```

**Step 6: Work Alignment Analysis** (if `--fibery-analysis` enabled)

File: `fibery_analysis/alex.akilin@wearevolt.com/work_alignment.md`

```markdown
# Work Alignment Analysis: alex.akilin@wearevolt.com
**Period:** 2025-09-29 to 2025-10-05

## ✅ Properly Tracked (6 entities)
Entities that appear in both Toggl and Fibery with correct state

## ⚠️ Fibery Not Updated (2 entities)
Logged time in Toggl but Fibery status doesn't reflect completion

## ❓ Missing in Toggl (1 entity)
Entities assigned in Fibery but no time logged in Toggl

## 📋 Open Entities (3 entities)
Entities assigned to user that are still open
```

### 4.4 OpenAI Summarization

**Configuration:** Entity-type-specific prompts in `config/prompts.yaml`

See [PRD_Configuration.md](./PRD_Configuration.md) for complete prompt templates.

**Key Features:**
- Different prompts for different entity types (Task, Bug, Feature, Build, Hotfix)
- Generic fallback for unknown entity types
- Focused on relevant context for each type
- Concise, factual summaries

### 4.5 Work Alignment Analysis

**When enabled with `--fibery-analysis`:**

1. **Fetch user's assigned entities** from Fibery for the date range
2. **Compare with Toggl entries** to identify:
   - ✅ **Properly tracked:** In both systems with correct state
   - ⚠️ **Fibery not updated:** Time logged but state not updated
   - ❓ **Missing in Toggl:** Assigned but no time logged
   - 📋 **Open entities:** Assigned but not started

3. **Generate alignment report** for each user
4. **Include in enhanced reports** with actionable insights

### 4.6 Rate Limiting and Caching

**API Rate Limits:**
- Fibery: No explicit rate limit, implement conservative limits
- OpenAI: Existing rate limit handling

**Caching Strategy:**
1. **Schema Cache**: 24 hours
2. **Entity Cache**: 1 hour (entities may update frequently)
3. **User Cache**: 24 hours
4. **Summary Cache**: Indefinite (keyed by entity_id + updated_at)

See [PRD_Configuration.md](./PRD_Configuration.md) for cache configuration.

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **Entity fetch time**: < 2 seconds per entity
- **LLM summarization**: < 5 seconds per entity
- **Total enrichment overhead**: < 3 minutes for 50 entities
- **Caching effectiveness**: > 70% cache hit rate for repeated runs

### 5.2 Reliability

**Error Handling:**
- Graceful degradation if Fibery API unavailable
- Retry logic for transient failures (3 retries, exponential backoff)
- Continue processing if one entity fails
- Log all errors for debugging

**Data Validation:**
- Validate API responses before processing
- Handle missing fields gracefully
- Verify entity types match expected schema
- Validate user email matching

### 5.3 Security

**API Credentials:**
```bash
# .env file
FIBERY_API_TOKEN=your_fibery_token_here
FIBERY_WORKSPACE_NAME=your_workspace
```

**Security Measures:**
- Read-only Fibery API access (no writes)
- Sanitize all user inputs
- Use parameterized SQL queries
- Never log API tokens
- Encrypt sensitive data in local cache

### 5.4 Maintainability

**Code Organization:**
```
volt-agent/
├── src/
│   ├── fibery/
│   │   ├── client.py              # Fibery API client
│   │   ├── models.py              # Data models
│   │   ├── schema.py              # Schema discovery
│   │   ├── entity_fetcher.py     # Entity fetching
│   │   └── user_matcher.py       # User matching
│   ├── enrichment/
│   │   ├── pipeline.py           # Orchestration
│   │   ├── summarizer.py         # LLM summarization
│   │   └── alignment_analyzer.py # Work alignment
│   └── reporting/
│       └── enriched_generator.py  # Enhanced reports
└── tests/
    ├── test_fibery_client.py
    ├── test_entity_fetcher.py
    ├── test_enrichment_pipeline.py
    └── test_alignment_analyzer.py
```

---

## 6. Related Documentation

- **[PRD_Database_Schema.md](./PRD_Database_Schema.md)** - All database tables and schema
- **[PRD_Configuration.md](./PRD_Configuration.md)** - Configuration files and prompts
- **[PRD_Report_Formats.md](./PRD_Report_Formats.md)** - Enhanced report templates
- **[PRD_Schema_Management.md](./PRD_Schema_Management.md)** - Self-maintaining system features
- **[PRD_Implementation.md](./PRD_Implementation.md)** - Implementation plan and testing
- **[Fibery API Integration Guide](../Fibery_API_Integration_Guide.md)** - Complete API documentation
- **[Workspace Structure](../workspace-structure/README.md)** - Fibery workspace analysis

---

**End of Core Requirements Document**

