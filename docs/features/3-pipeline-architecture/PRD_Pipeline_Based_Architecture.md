# Product Requirements Document (PRD)
# Pipeline-Based Architecture for Toggl and Fibery Analysis

**Version:** 2.0  
**Date:** October 10, 2025  
**Status:** 📋 Planning  
**Previous Version:** 1.0 (SQLite-based monolithic architecture)

---

## Executive Summary

This document outlines the requirements for refactoring the Toggl-Fibery analysis system from a monolithic SQLite-based architecture to a **pipeline-based architecture** using JSON files for caching. The new system will support both **sequential step-by-step execution** and **full pipeline execution** with a single command.

### Key Changes from v1.0

1. **Replace SQLite with JSON files** for all caching and data persistence
2. **Multi-step pipeline** with independently executable steps
3. **Run-based caching** with structured JSON outputs at each step
4. **Step isolation** allowing re-execution of individual steps without re-running previous steps
5. **Future-ready architecture** for console UI and additional pipeline steps

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Pipeline Steps](#2-pipeline-steps)
3. [Data Structures](#3-data-structures)
4. [Command-Line Interface](#4-command-line-interface)
5. [File Structure](#5-file-structure)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Migration Strategy](#8-migration-strategy)
9. [Future Enhancements](#9-future-enhancements)

---

## 1. Architecture Overview

### 1.1 Pipeline Philosophy

The new architecture follows a **data pipeline pattern** where:

1. Each step has **clear inputs and outputs**
2. Each step produces **both JSON (machine-readable) and Markdown (human-readable)** outputs
3. Steps are **idempotent** - can be re-run with same inputs to get same outputs
4. Steps can be executed **independently** or **sequentially** via a single command
5. All intermediate data is **cached as JSON** for inspection, debugging, and re-processing

### 1.2 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Pipeline Flow                            │
└─────────────────────────────────────────────────────────────────┘

Step 1: TOGGL COLLECTION
  Input:  --start-date, --end-date, [--users]
  Output: run_metadata.json, toggl_data.json, toggl_report.md
  
          ↓ (pass run_id)
          
Step 2: FIBERY ENRICHMENT
  Input:  --run-id
  Reads:  toggl_data.json (from step 1)
  Output: fibery_enriched.json, fibery_report.md
  
          ↓ (pass run_id for future steps)
          
Step N: FUTURE STEPS
  Input:  --run-id
  Reads:  Previous step outputs
  Output: New JSON + Markdown outputs

┌─────────────────────────────────────────────────────────────────┐
│                      OR: Full Pipeline                           │
└─────────────────────────────────────────────────────────────────┘

Full Command: Executes all steps sequentially
  Input:  --start-date, --end-date, [--users]
  Runs:   Step 1 → Step 2 → Step N
  Output: All JSON + Markdown files for each step
```

### 1.3 Benefits

✅ **Modularity**: Each step is independent and testable  
✅ **Debuggability**: Inspect JSON outputs at each step  
✅ **Flexibility**: Re-run only the steps you need  
✅ **Extensibility**: Easy to add new pipeline steps  
✅ **Transparency**: Human-readable reports at each step  
✅ **No Database**: Simpler deployment, easier backup, version control friendly  

---

## 2. Pipeline Steps

### Step 1: Toggl Data Collection

**Command:** `volt-agent toggl-collect`

**Purpose:** Fetch raw Toggl time tracking data, parse entity metadata, aggregate by person and activity.

**Inputs:**
- `--start-date` (YYYY-MM-DD): Start of reporting period
- `--end-date` (YYYY-MM-DD): End of reporting period
- `--users` (optional): Comma-separated list of user emails (default: all workspace users)

**Processing:**
1. Generate unique `run_id` (format: `run_YYYY-MM-DD-HH-MM-SS`)
2. Create run directory: `tmp/runs/{run_id}/`
3. Fetch Toggl time entries for the date range (using existing day-by-day chunking)
4. Parse Fibery entity metadata from descriptions (existing regex parser)
5. Group entries by:
   - User email
   - Matched vs unmatched entities
   - For matched: by Fibery entity ID
   - For unmatched: by description/activity type
6. Aggregate time spent per group

**Outputs:**
- `tmp/runs/{run_id}/run_metadata.json` - Metadata about this run (root level)
- `tmp/runs/{run_id}/step_1_toggl_collection/toggl_data.json` - Complete structured Toggl data
- `tmp/runs/{run_id}/step_1_toggl_collection/reports/toggl_summary.md` - Human-readable summary report
- `tmp/runs/{run_id}/step_1_toggl_collection/logs/toggl_collection.log` - Detailed execution log

**Success Criteria:**
- All Toggl data fetched and parsed successfully
- JSON output is valid and complete
- Markdown report is generated
- No data loss compared to v1.0 SQLite approach

---

### Step 2: Fibery Enrichment

**Command:** `volt-agent fibery-enrich`

**Purpose:** Enrich matched Fibery entities with additional metadata from Fibery API.

**Inputs:**
- `--run-id` (required): Run ID from Step 1

**Processing:**
1. Read `toggl_data.json` from the specified run
2. Extract all matched Fibery entities (those with entity IDs)
3. For each entity, fetch from Fibery API:
   - Start date, end date
   - Total time logged (if available in Fibery)
   - Description presence and content
   - Comments count and recent comments
   - Feature/project metadata
   - State/status information
   - Priority, assignees, etc.
4. Merge Fibery data with Toggl time tracking data
5. Use LLM to generate summaries for enriched entities

**Outputs:**
- `tmp/runs/{run_id}/step_2_fibery_enrichment/fibery_enriched.json` - Toggl data enriched with Fibery metadata
- `tmp/runs/{run_id}/step_2_fibery_enrichment/reports/fibery_summary.md` - Human-readable enriched report
- `tmp/runs/{run_id}/step_2_fibery_enrichment/logs/fibery_enrichment.log` - Detailed execution log

**Success Criteria:**
- All matched entities successfully enriched (or gracefully handled if entity not found)
- JSON output maintains all Toggl data + adds Fibery metadata
- Markdown report shows enriched information
- No degradation in report quality compared to v1.0

---

### Step 3: Full Pipeline Execution

**Command:** `volt-agent run-full`

**Purpose:** Execute all pipeline steps sequentially in a single command.

**Inputs:**
- Same as Step 1: `--start-date`, `--end-date`, `--users`

**Processing:**
1. Execute Step 1 (Toggl Collection) → get `run_id`
2. Execute Step 2 (Fibery Enrichment) with `run_id`
3. Execute any future steps with `run_id`

**Outputs:**
- All outputs from all steps in the run directory

**Success Criteria:**
- All steps execute successfully
- Same results as running steps individually
- Graceful error handling with rollback/cleanup on failure

---

## 3. Data Structures

### 3.1 Run Metadata (`run_metadata.json`)

**Purpose:** Store metadata about the pipeline run for reference and provenance.

```json
{
  "run_id": "run_2025-10-10-15-30-45",
  "created_at": "2025-10-10T15:30:45Z",
  "status": "in_progress",  // "in_progress", "completed", "failed"
  "pipeline_version": "2.0",
  "steps_completed": ["toggl-collect"],
  "steps_failed": [],
  "parameters": {
    "start_date": "2025-10-07",
    "end_date": "2025-10-13",
    "users_filter": ["user1@example.com", "user2@example.com"],
    "users_count": 2
  },
  "statistics": {
    "total_time_entries": 245,
    "total_users": 2,
    "total_duration_seconds": 144000,
    "matched_entries": 180,
    "unmatched_entries": 65
  },
  "step_metadata": {
    "toggl-collect": {
      "started_at": "2025-10-10T15:30:45Z",
      "completed_at": "2025-10-10T15:31:20Z",
      "duration_seconds": 35,
      "status": "completed",
      "api_calls": 7,
      "entries_fetched": 245
    },
    "fibery-enrich": {
      "started_at": null,
      "completed_at": null,
      "duration_seconds": null,
      "status": "pending"
    }
  }
}
```

### 3.2 Toggl Data (`toggl_data.json`)

**Purpose:** Complete structured output from Toggl collection step.

```json
{
  "run_id": "run_2025-10-10-15-30-45",
  "generated_at": "2025-10-10T15:31:20Z",
  "date_range": {
    "start_date": "2025-10-07",
    "end_date": "2025-10-13"
  },
  "summary": {
    "total_users": 2,
    "total_entries": 245,
    "period_duration_seconds": 144000,
    "period_duration_hours": 40.0,
    "matched_entries_count": 180,
    "unmatched_entries_count": 65
  },
  "users": [
    {
      "user_metadata": {
        "email": "user1@example.com",
        "name": "John Doe",
        "toggl_user_id": 123456
      },
      "statistics": {
        "period_duration_seconds": 72000,
        "period_duration_hours": 20.0,
        "matched_duration_seconds": 54000,
        "unmatched_duration_seconds": 18000,
        "matched_percentage": 75.0,
        "unmatched_percentage": 25.0,
        "total_entries": 120,
        "matched_entities_count": 15,
        "unmatched_activities_count": 8
      },
      "matched_entities": [
        {
          "fibery_metadata": {
            "entity_id": "1234",
            "public_id": "#1234",
            "entity_database": "Scrum",
            "entity_type": "Task",
            "entity_name": "Fix authentication bug",
            "project": "AuthService"
          },
          "time_tracking": {
            "time_spent_seconds": 7200,
            "time_spent_hours": 2.0,
            "entry_count": 3,
            "first_logged": "2025-10-07T09:00:00Z",
            "last_logged": "2025-10-09T16:30:00Z"
          }
        }
      ],
      "unmatched_activities": [
        {
          "description": "Team standup meeting",
          "time_tracking": {
            "total_duration_seconds": 900,
            "total_duration_hours": 0.25,
            "entry_count": 5,
            "first_logged": "2025-10-07T10:00:00Z",
            "last_logged": "2025-10-11T10:00:00Z"
          }
        }
      ]
    }
  ]
}
```

### 3.3 Fibery Enriched Data (`fibery_enriched.json`)

**Purpose:** Toggl data enriched with Fibery metadata and LLM summaries.

```json
{
  "run_id": "run_2025-10-10-15-30-45",
  "generated_at": "2025-10-10T15:35:45Z",
  "based_on": {
    "toggl_data_file": "toggl_data.json",
    "toggl_generated_at": "2025-10-10T15:31:20Z"
  },
  "enrichment_summary": {
    "total_entities_to_enrich": 25,
    "successfully_enriched": 23,
    "not_found_in_fibery": 2,
    "api_calls_made": 25
  },
  "users": [
    {
      "user_metadata": {
        "email": "user1@example.com",
        "name": "John Doe",
        "toggl_user_id": 123456
      },
      "statistics": {
        // Same as toggl_data.json
        "period_duration_seconds": 72000,
        "period_duration_hours": 20.0,
        "matched_duration_seconds": 54000,
        "unmatched_duration_seconds": 18000,
        "matched_percentage": 75.0,
        "unmatched_percentage": 25.0,
        "total_entries": 120,
        "matched_entities_count": 15,
        "unmatched_activities_count": 8
      },
      "matched_entities": [
        {
          "fibery_metadata": {
            "entity_id": "1234",
            "public_id": "#1234",
            "entity_database": "Scrum",
            "entity_type": "Task",
            "entity_name": "Fix authentication bug",
            "project": "AuthService"
          },
          "time_tracking": {
            // From toggl_data.json
            "time_spent_seconds": 7200,
            "time_spent_hours": 2.0,
            "entry_count": 3,
            "first_logged": "2025-10-07T09:00:00Z",
            "last_logged": "2025-10-09T16:30:00Z"
          },
          "fibery_enrichment": {
            "enrichment_status": "success",  // "success", "not_found", "api_error"
            "enriched_at": "2025-10-10T15:32:10Z",
            "fibery_data": {
              "state": {
                "current": "In Progress",
                "history": [
                  {"state": "Backlog", "date": "2025-10-01"},
                  {"state": "In Progress", "date": "2025-10-07"}
                ]
              },
              "dates": {
                "created_at": "2025-10-01T12:00:00Z",
                "started_at": "2025-10-07T09:00:00Z",
                "completed_at": null,
                "due_date": "2025-10-15T00:00:00Z"
              },
              "content": {
                "has_description": true,
                "description_length": 350,
                "description_preview": "Authentication system is failing when...",
                "has_comments": true,
                "comments_count": 3,
                "recent_comments": [
                  {
                    "author": "Jane Smith",
                    "created_at": "2025-10-08T14:30:00Z",
                    "text_preview": "Found the root cause in..."
                  }
                ]
              },
              "relationships": {
                "parent_feature": {
                  "id": "5678",
                  "name": "Authentication Overhaul",
                  "type": "Feature"
                },
                "assignees": ["John Doe", "Jane Smith"],
                "priority": "High",
                "labels": ["backend", "security", "urgent"]
              },
              "time_data": {
                "fibery_time_spent_seconds": 8100,  // If Fibery tracks time separately
                "estimated_seconds": 14400
              }
            }
          }
        }
      ],
      "unmatched_activities": [
        {
          "description": "Team standup meeting",
          "time_tracking": {
            "time_spent_seconds": 900,
            "time_spent_hours": 0.25,
            "entry_count": 5,
            "first_logged": "2025-10-07T10:00:00Z",
            "last_logged": "2025-10-11T10:00:00Z"
          }
        }
      ]
    }
  ]
}
```

---

## 4. Command-Line Interface

### 4.1 Command Structure

**Base Command:**
```bash
volt-agent [COMMAND] [OPTIONS]
```

### 4.2 Step 1: Toggl Collection

```bash
volt-agent toggl-collect \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD \
  [--users email1@example.com,email2@example.com] \
  [--output-dir ./tmp/runs] \
  [--config ./config/config.yaml]
```

**Options:**
- `--start-date` (required): Start date of reporting period
- `--end-date` (required): End date of reporting period
- `--users` (optional): Comma-separated user emails (default: all users in workspace)
- `--output-dir` (optional): Base directory for runs (default: `./tmp/runs`)
- `--config` (optional): Path to config file (default: `./config/config.yaml`)

**Example:**
```bash
# Collect data for current week, all users
volt-agent toggl-collect \
  --start-date 2025-10-07 \
  --end-date 2025-10-13

# Output:
# ✓ Run created: run_2025-10-10-15-30-45
# ✓ Fetching Toggl data...
#   ├─ Day 1/7: 35 entries
#   ├─ Day 2/7: 40 entries
#   └─ ... 
# ✓ Parsing entity metadata...
# ✓ Aggregating data by user...
# ✓ Writing JSON output...
# ✓ Generating markdown report...
# 
# ✅ Step 1 complete!
#    Run ID: run_2025-10-10-15-30-45
#    Location: ./tmp/runs/run_2025-10-10-15-30-45/step_1_toggl_collection/
#    Total entries: 245
#    Total users: 12
#    Duration: 35 seconds
#
# Next step:
#    volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45
```

### 4.3 Step 2: Fibery Enrichment

```bash
volt-agent fibery-enrich \
  --run-id RUN_ID \
  [--config ./config/config.yaml]
```

**Options:**
- `--run-id` (required): Run ID from Step 1
- `--config` (optional): Path to config file

**Example:**
```bash
volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45

# Output:
# ✓ Loading run: run_2025-10-10-15-30-45
# ✓ Reading step_1_toggl_collection/toggl_data.json...
# ✓ Found 25 entities to enrich
# ✓ Fetching Fibery data...
#   ├─ Entity #1234: ✓ Success
#   ├─ Entity #1235: ✓ Success
#   ├─ Entity #1236: ⚠ Not found
#   └─ ... 
# ✓ Generating LLM summaries...
#   ├─ User: john@example.com ✓
#   └─ ...
# ✓ Writing enriched JSON...
# ✓ Generating markdown report...
# 
# ✅ Step 2 complete!
#    Run ID: run_2025-10-10-15-30-45
#    Successfully enriched: 23/25 entities
#    Duration: 45 seconds
```

### 4.4 Full Pipeline Execution

```bash
volt-agent run-full \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD \
  [--users email1@example.com,email2@example.com] \
  [--output-dir ./tmp/runs] \
  [--config ./config/config.yaml]
```

**Options:**
- Same as `toggl-collect` (since it starts the pipeline)

**Example:**
```bash
volt-agent run-full \
  --start-date 2025-10-07 \
  --end-date 2025-10-13

# Output:
# ══════════════════════════════════════════
# FULL PIPELINE EXECUTION
# ══════════════════════════════════════════
#
# [Step 1/2] Toggl Collection
# ✓ Run created: run_2025-10-10-15-30-45
# ✓ Fetching Toggl data... (35 seconds)
# ✓ Step 1 complete
#
# [Step 2/2] Fibery Enrichment
# ✓ Loading run data...
# ✓ Enriching entities... (45 seconds)
# ✓ Step 2 complete
#
# ══════════════════════════════════════════
# ✅ PIPELINE COMPLETE
# ══════════════════════════════════════════
#    Run ID: run_2025-10-10-15-30-45
#    Location: ./tmp/runs/run_2025-10-10-15-30-45/
#    Total duration: 80 seconds
#
# Reports generated:
#    - toggl_summary.md
#    - fibery_summary.md
```

### 4.5 Utility Commands

```bash
# List all runs
volt-agent list-runs [--limit 10] [--status completed|failed|in_progress]

# Show run details
volt-agent show-run --run-id RUN_ID

# Clean up old runs
volt-agent cleanup-runs --older-than 30d [--dry-run]

# Validate a run's data integrity
volt-agent validate-run --run-id RUN_ID
```

---

## 5. File Structure

### 5.1 Directory Layout

```
volt-agent/
├── tmp/
│   └── runs/
│       └── run_2025-10-10-15-30-45/           # Run directory
│           ├── run_metadata.json              # Run metadata (root level)
│           │
│           ├── step_1_toggl_collection/       # Step 1 outputs
│           │   ├── toggl_data.json            # Step 1 data
│           │   ├── reports/                   # Step 1 reports
│           │   │   ├── toggl_summary.md
│           │   │   └── individual/            # Per-user reports
│           │   │       ├── john_doe.md
│           │   │       └── jane_smith.md
│           │   └── logs/
│           │       └── toggl_collection.log
│           │
│           └── step_2_fibery_enrichment/      # Step 2 outputs
│               ├── fibery_enriched.json       # Step 2 data
│               ├── reports/                   # Step 2 reports
│               │   ├── fibery_summary.md
│               │   └── individual/            # Per-user enriched reports
│               │       ├── john_doe.md
│               │       └── jane_smith.md
│               └── logs/
│                   └── fibery_enrichment.log
├── src/
│   ├── cli.py                                 # CLI entry point
│   ├── commands/                              # Command implementations
│   │   ├── __init__.py
│   │   ├── toggl_collect.py                   # Step 1
│   │   ├── fibery_enrich.py                   # Step 2
│   │   ├── run_full.py                        # Full pipeline
│   │   └── utils.py                           # Utility commands
│   ├── pipeline/                              # Pipeline framework
│   │   ├── __init__.py
│   │   ├── step.py                            # Base step class
│   │   ├── runner.py                          # Pipeline runner
│   │   └── run_manager.py                     # Run lifecycle management
│   ├── storage/                               # JSON storage layer
│   │   ├── __init__.py
│   │   ├── json_storage.py                    # JSON read/write utilities
│   │   └── schemas.py                         # Pydantic models for validation
│   ├── toggl/                                 # Existing Toggl client
│   ├── fibery/                                # Existing Fibery client
│   ├── parser/                                # Existing parser
│   └── llm/                                   # Existing LLM client
└── config/
    └── config.yaml                            # Configuration
```

### 5.2 File Naming Conventions

**Run ID Format:**
```
run_YYYY-MM-DD-HH-MM-SS
```

**Run Directory:**
```
tmp/runs/{run_id}/
```

**Directory Structure:**
```
{run_id}/
├── run_metadata.json                                    # Always present (root level)
├── step_1_toggl_collection/                             # Step 1 directory
│   ├── toggl_data.json                                  # Step 1 output
│   ├── reports/toggl_summary.md
│   └── logs/toggl_collection.log
├── step_2_fibery_enrichment/                            # Step 2 directory
│   ├── fibery_enriched.json                             # Step 2 output
│   ├── reports/fibery_summary.md
│   └── logs/fibery_enrichment.log
└── step_N_*/                                            # Future steps
    ├── *.json
    ├── reports/
    └── logs/
```

---

## 6. Functional Requirements

### 6.1 Step 1: Toggl Collection

#### FR-TC-1: Data Fetching
- **Requirement:** Fetch all Toggl time entries for the specified date range
- **Implementation:** Reuse existing day-by-day chunking logic from v1.0
- **Acceptance Criteria:**
  - All time entries fetched without data loss
  - Handles pagination correctly
  - Respects rate limits (240 requests/hour)
  - Graceful error handling for API failures

#### FR-TC-2: Entity Parsing
- **Requirement:** Parse Fibery entity metadata from time entry descriptions
- **Implementation:** Reuse existing regex parser from v1.0
- **Acceptance Criteria:**
  - Correctly extracts entity ID (#1234)
  - Correctly extracts database, type, project from brackets
  - Handles missing or partial metadata
  - Handles non-English characters

#### FR-TC-3: Data Aggregation
- **Requirement:** Group time entries by user, then by matched/unmatched, then by entity/activity
- **Acceptance Criteria:**
  - Correct grouping logic
  - Accurate time summations
  - No duplicate entries
  - Preserves raw entry data for reference

#### FR-TC-4: JSON Output
- **Requirement:** Write structured JSON output conforming to `toggl_data.json` schema
- **Acceptance Criteria:**
  - Valid JSON syntax
  - Conforms to Pydantic schema
  - Complete data (no missing fields)
  - Human-readable formatting (indented)

#### FR-TC-5: Markdown Report
- **Requirement:** Generate human-readable Markdown summary
- **Acceptance Criteria:**
  - Shows summary statistics per user
  - Lists matched entities with time spent
  - Lists unmatched activities with time spent
  - Matches or exceeds quality of v1.0 reports

#### FR-TC-6: Run Metadata
- **Requirement:** Create and maintain run metadata file
- **Acceptance Criteria:**
  - Unique run_id generated
  - Metadata includes all required fields
  - Status tracking (in_progress, completed, failed)
  - Step completion tracking

### 6.2 Step 2: Fibery Enrichment

#### FR-FE-1: Data Loading
- **Requirement:** Load toggl_data.json from step 1 directory of specified run
- **Acceptance Criteria:**
  - Validates run exists
  - Validates step_1_toggl_collection directory exists
  - Validates toggl_data.json exists and is valid
  - Handles corrupted JSON gracefully

#### FR-FE-2: Entity Enrichment
- **Requirement:** Fetch additional metadata from Fibery for each matched entity
- **Acceptance Criteria:**
  - Fetches all specified fields (state, dates, description, comments, relationships)
  - Handles entities not found in Fibery gracefully
  - Handles API errors with retry logic
  - Respects Fibery API rate limits

#### FR-FE-3: LLM Summarization
- **Requirement:** Generate intelligent summaries per user using LLM
- **Implementation:** Reuse existing LLM integration from v1.0
- **Acceptance Criteria:**
  - Generates overall summary per user
  - Generates matched entities summary
  - Generates unmatched activities summary
  - Summaries are comprehensive and accurate

#### FR-FE-4: JSON Output
- **Requirement:** Write enriched JSON output conforming to `fibery_enriched.json` schema
- **Acceptance Criteria:**
  - Valid JSON syntax
  - Conforms to Pydantic schema
  - Includes all toggl_data + Fibery enrichment
  - Handles missing enrichment data gracefully

#### FR-FE-5: Markdown Report
- **Requirement:** Generate human-readable enriched report
- **Acceptance Criteria:**
  - Shows all toggl_data information
  - Shows enriched Fibery metadata per entity
  - Includes LLM summaries
  - Matches or exceeds quality of v1.0 reports

#### FR-FE-6: Run Metadata Update
- **Requirement:** Update run_metadata.json with step 2 completion status
- **Acceptance Criteria:**
  - Updates step_metadata for fibery-enrich
  - Updates steps_completed list
  - Updates overall status if pipeline complete

### 6.3 Full Pipeline Execution

#### FR-FP-1: Sequential Execution
- **Requirement:** Execute all pipeline steps sequentially
- **Acceptance Criteria:**
  - Step 1 executes first
  - Step 2 receives run_id from step 1
  - Steps execute in correct order
  - Each step completes before next starts

#### FR-FP-2: Error Handling
- **Requirement:** Handle errors gracefully and provide clear failure points
- **Acceptance Criteria:**
  - If step 1 fails, pipeline stops and reports error
  - If step 2 fails, step 1 data is preserved
  - run_metadata.json reflects failed step
  - Clear error messages to user

#### FR-FP-3: Progress Reporting
- **Requirement:** Provide clear progress indication to user
- **Acceptance Criteria:**
  - Shows which step is currently executing
  - Shows progress within each step
  - Shows estimated time remaining (if possible)
  - Clean, formatted console output

### 6.4 Utility Commands

#### FR-UC-1: List Runs
- **Requirement:** List all runs with filtering options
- **Acceptance Criteria:**
  - Shows run_id, date, status, user count
  - Supports filtering by status
  - Supports limiting number of results
  - Sorted by date (newest first)

#### FR-UC-2: Show Run
- **Requirement:** Display detailed information about a specific run
- **Acceptance Criteria:**
  - Shows all run metadata
  - Shows file sizes
  - Shows step completion status
  - Shows statistics

#### FR-UC-3: Cleanup Runs
- **Requirement:** Delete old runs to free up space
- **Acceptance Criteria:**
  - Supports --older-than parameter (days)
  - Supports --dry-run flag
  - Asks for confirmation unless --force flag
  - Reports what was deleted

#### FR-UC-4: Validate Run
- **Requirement:** Check integrity of a run's data
- **Acceptance Criteria:**
  - Validates all JSON files against schemas
  - Checks for missing files
  - Validates data consistency
  - Reports any issues found

---

## 7. Non-Functional Requirements

### 7.1 Performance

**NFR-P-1: Execution Speed**
- Step 1 (Toggl Collection): ≤ 2 minutes for 12 users, 7-day period
- Step 2 (Fibery Enrichment): ≤ 3 minutes for 150 entities
- Full Pipeline: ≤ 5 minutes total

**NFR-P-2: File Size**
- JSON files should be human-readable (indented) but compressed if >10MB
- Individual report markdown files: ≤ 100KB each
- Summary reports: ≤ 500KB each

**NFR-P-3: Memory Usage**
- Peak memory usage: ≤ 512MB for typical workloads
- Streaming where possible (don't load entire datasets into memory)

### 7.2 Reliability

**NFR-R-1: Data Integrity**
- All JSON outputs must be valid and schema-compliant
- No data loss during migration from v1.0 to v2.0
- Atomic writes (use temp files + rename)
- Checksums for data validation

**NFR-R-2: Error Recovery**
- Graceful degradation if APIs unavailable
- Retry logic with exponential backoff
- Clear error messages
- Preserve partial progress on failure

**NFR-R-3: Idempotency**
- Re-running same step with same inputs produces identical outputs
- Steps can be re-run without side effects
- Timestamps may differ but data content identical

### 7.3 Maintainability

**NFR-M-1: Code Organization**
- Clear separation of concerns
- Reuse existing v1.0 code where appropriate
- Well-documented pipeline framework
- Consistent naming conventions

**NFR-M-2: Testing**
- Unit tests for all new pipeline code
- Integration tests for full pipeline
- Test coverage ≥ 80%
- Mock external APIs in tests

**NFR-M-3: Logging**
- Structured logging with log levels
- Per-step log files
- Debug mode for verbose output
- Log rotation for long-running processes

### 7.4 Extensibility

**NFR-E-1: New Steps**
- Easy to add new pipeline steps
- Base `Step` class with clear interface
- Automatic run metadata updates
- Automatic CLI command generation

**NFR-E-2: Configuration**
- All configurable values in config.yaml
- Environment variable overrides
- Schema validation for config

### 7.5 Usability

**NFR-U-1: CLI Experience**
- Clear, helpful error messages
- Colorized output (using `rich` library)
- Progress bars for long operations
- Helpful examples in `--help` output

**NFR-U-2: Documentation**
- README with quick start guide
- Detailed docs for each command
- Migration guide from v1.0
- Examples for common use cases

---

## 8. Migration Strategy

### 8.1 Migration Goals

1. **Preserve existing functionality** - No features lost
2. **Backward compatibility** - Option to run v1.0 mode during transition
3. **Data migration** - Convert existing SQLite data to JSON (optional)
4. **Smooth transition** - Users can gradually adopt new commands

### 8.2 Migration Phases

#### Phase 1: Foundation (Week 1)
- ✅ Create pipeline framework (`Step` class, `Runner`, `RunManager`)
- ✅ Create JSON storage layer with Pydantic schemas
- ✅ Create new CLI structure with new commands
- ✅ Keep existing v1.0 code working

#### Phase 2: Step 1 Implementation (Week 2)
- ✅ Implement `toggl-collect` command
- ✅ Reuse existing Toggl client, parser
- ✅ Write JSON output with new schema
- ✅ Generate markdown reports
- ✅ Test against v1.0 for parity

#### Phase 3: Step 2 Implementation (Week 3)
- ✅ Implement `fibery-enrich` command
- ✅ Reuse existing Fibery client, LLM client
- ✅ Write enriched JSON output
- ✅ Generate enriched markdown reports
- ✅ Test against v1.0 for parity

#### Phase 4: Full Pipeline (Week 4)
- ✅ Implement `run-full` command
- ✅ Implement utility commands (`list-runs`, `show-run`, etc.)
- ✅ End-to-end testing
- ✅ Performance testing

#### Phase 5: Documentation & Cleanup (Week 5)
- ✅ Update README and docs
- ✅ Write migration guide
- ✅ Deprecate v1.0 commands (with warnings)
- ✅ Optional: Data migration tool for existing SQLite data

### 8.3 Backward Compatibility

**Option 1: Dual Mode**
```bash
# Old way (still works, shows deprecation warning)
python generate_report.py --start-date 2025-10-07 --end-date 2025-10-13

# New way
volt-agent run-full --start-date 2025-10-07 --end-date 2025-10-13
```

**Option 2: Adapter Layer**
- Keep old CLI interface
- Internally call new pipeline
- Output both SQLite and JSON for transition period

### 8.4 Data Migration Tool

**Optional Command:**
```bash
volt-agent migrate-from-sqlite \
  --sqlite-db ./data/toggl_cache.db \
  --run-id run_2025-10-10-15-30-45 \
  [--output-dir ./tmp/runs]
```

**Purpose:** Convert existing SQLite run data to new JSON format

---

## 9. Future Enhancements

### 9.1 Additional Pipeline Steps (Post-v2.0)

#### Step 3: Analytics & Insights
- Statistical analysis of work patterns
- Trend detection over multiple weeks
- Team productivity metrics
- Anomaly detection

#### Step 4: Report Generation
- Customizable report templates
- Multi-format output (PDF, HTML, JSON)
- Client-facing reports
- Executive summaries

#### Step 5: Integration Steps
- Push to Slack/Teams
- Update Fibery with time tracking data
- Sync to data warehouse
- Trigger automation workflows

### 9.2 Interactive Console UI

**Future Command:**
```bash
volt-agent ui
```

**Features:**
- TUI (Terminal UI) using `textual` or `rich`
- Interactive step selection
- Live progress visualization
- Browse past runs
- View reports in terminal

**Mock UI:**
```
╔══════════════════════════════════════════════════════════════╗
║                    VOLT-AGENT PIPELINE                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Select Pipeline Step:                                       ║
║                                                              ║
║  ▶ Run Full Pipeline                                         ║
║    Step 1: Toggl Collection                                  ║
║    Step 2: Fibery Enrichment                                 ║
║    ---------------------------------                         ║
║    View Past Runs                                            ║
║    Settings                                                  ║
║    Exit                                                      ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Recent Runs:                                                ║
║  • run_2025-10-10-15-30-45 [COMPLETED] (2 hours ago)        ║
║  • run_2025-10-09-10-15-30 [COMPLETED] (1 day ago)          ║
║  • run_2025-10-08-14-20-15 [FAILED]    (2 days ago)         ║
╚══════════════════════════════════════════════════════════════╝

Use ↑↓ arrows to navigate, Enter to select, Esc to go back
```

### 9.3 Configuration Profiles

**Feature:** Support multiple configuration profiles

```bash
# Run with production config
volt-agent run-full --profile production --start-date 2025-10-07 --end-date 2025-10-13

# Run with development config (uses test Fibery workspace, verbose logging)
volt-agent run-full --profile dev --start-date 2025-10-07 --end-date 2025-10-13
```

**Config Structure:**
```yaml
profiles:
  production:
    toggl:
      workspace_id: 123456
    fibery:
      workspace_url: "https://company.fibery.io"
    output:
      directory: "./reports/production"
  
  dev:
    toggl:
      workspace_id: 789012
    fibery:
      workspace_url: "https://company-dev.fibery.io"
    output:
      directory: "./tmp/dev"
    logging:
      level: DEBUG
```

### 9.4 Scheduling & Automation

**Feature:** Schedule automatic pipeline runs

```bash
# Schedule weekly reports every Monday at 9am
volt-agent schedule add \
  --name "weekly-team-report" \
  --command "run-full --start-date {last_monday} --end-date {last_sunday}" \
  --cron "0 9 * * 1"

# List scheduled jobs
volt-agent schedule list

# Remove scheduled job
volt-agent schedule remove --name "weekly-team-report"
```

### 9.5 Comparison & Diff Tools

**Feature:** Compare runs across different time periods

```bash
# Compare this week vs last week
volt-agent compare \
  --run-id-1 run_2025-10-10-15-30-45 \
  --run-id-2 run_2025-10-03-15-30-45 \
  --output comparison_report.md
```

**Output:**
- Time spent changes per user
- New entities worked on
- Dropped entities
- Focus area shifts
- Productivity trends

### 9.6 Export & Integration

```bash
# Export to CSV for Excel analysis
volt-agent export --run-id RUN_ID --format csv --output report.csv

# Export to data warehouse
volt-agent export --run-id RUN_ID --format bigquery --table team_activity

# Send to Slack
volt-agent notify --run-id RUN_ID --channel "#team-reports" --format slack
```

### 9.7 Web Dashboard

**Future Feature:** Web-based dashboard for browsing reports

- Browse all runs
- View reports in browser
- Interactive charts
- Drill-down into individual user data
- Search and filter
- Export capabilities

---

## 10. Appendices

### Appendix A: Schema Definitions (Pydantic Models)

**File:** `src/storage/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class UserMetadata(BaseModel):
    email: str
    name: str
    toggl_user_id: int

class FiberyMetadata(BaseModel):
    entity_id: str
    public_id: str
    entity_database: str
    entity_type: str
    entity_name: str
    project: str

class TimeTracking(BaseModel):
    time_spent_seconds: int
    time_spent_hours: float
    entry_count: int
    first_logged: datetime
    last_logged: datetime

class MatchedEntity(BaseModel):
    fibery_metadata: FiberyMetadata
    time_tracking: TimeTracking

class UnmatchedActivity(BaseModel):
    description: str
    time_tracking: TimeTracking

class UserStatistics(BaseModel):
    period_duration_seconds: int
    period_duration_hours: float
    matched_duration_seconds: int
    unmatched_duration_seconds: int
    matched_percentage: float
    unmatched_percentage: float
    total_entries: int
    matched_entities_count: int
    unmatched_activities_count: int

class UserData(BaseModel):
    user_metadata: UserMetadata
    statistics: UserStatistics
    matched_entities: List[MatchedEntity]
    unmatched_activities: List[UnmatchedActivity]

class DateRange(BaseModel):
    start_date: str
    end_date: str

class TogglDataSummary(BaseModel):
    total_users: int
    total_entries: int
    period_duration_seconds: int
    period_duration_hours: float
    matched_entries_count: int
    unmatched_entries_count: int

class TogglData(BaseModel):
    run_id: str
    generated_at: datetime
    date_range: DateRange
    summary: TogglDataSummary
    users: List[UserData]

class RunParameters(BaseModel):
    start_date: str
    end_date: str
    users_filter: Optional[List[str]]
    users_count: int

class RunStatistics(BaseModel):
    total_time_entries: int
    total_users: int
    period_duration_seconds: int
    matched_entries: int
    unmatched_entries: int

class StepMetadata(BaseModel):
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    status: Literal["pending", "in_progress", "completed", "failed"]

class RunMetadata(BaseModel):
    run_id: str
    created_at: datetime
    status: Literal["in_progress", "completed", "failed"]
    pipeline_version: str
    steps_completed: List[str]
    steps_failed: List[str]
    parameters: RunParameters
    statistics: RunStatistics
    step_metadata: dict[str, StepMetadata]

# Additional models for fibery_enriched.json
# (Similar pattern, extending MatchedEntity with enrichment data)
```

### Appendix B: Base Step Class

**File:** `src/pipeline/step.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
import logging

class PipelineStep(ABC):
    """Base class for all pipeline steps"""
    
    def __init__(self, run_id: str, run_dir: Path, config: Dict[str, Any]):
        self.run_id = run_id
        self.run_dir = run_dir
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def step_name(self) -> str:
        """Unique name for this step (e.g., 'toggl-collect')"""
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Execute this pipeline step.
        
        Returns:
            True if step succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_inputs(self) -> bool:
        """
        Validate that all required inputs are available.
        
        Returns:
            True if inputs are valid, False otherwise
        """
        pass
    
    def update_run_metadata(self, status: str, **kwargs):
        """Update run metadata with this step's status"""
        # Implementation in base class
        pass
    
    def write_json_output(self, filename: str, data: Any):
        """Write JSON output with atomic write"""
        # Implementation in base class
        pass
    
    def write_markdown_output(self, filename: str, content: str):
        """Write markdown output"""
        # Implementation in base class
        pass
```

### Appendix C: Example Usage Scenarios

**Scenario 1: Weekly Team Report**
```bash
# Run every Monday morning for previous week
volt-agent run-full \
  --start-date $(date -d "last monday -7 days" +%Y-%m-%d) \
  --end-date $(date -d "last sunday" +%Y-%m-%d)
```

**Scenario 2: Re-enrich Existing Data**
```bash
# Step 1: Collect Toggl data
volt-agent toggl-collect --start-date 2025-10-07 --end-date 2025-10-13
# Output: run_2025-10-10-15-30-45

# Step 2: First enrichment attempt (maybe had API issues)
volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45
# Some entities failed to enrich

# Step 2 again: Re-run enrichment after fixing API issues
volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45 --force
# All entities enriched successfully
```

**Scenario 3: Development Testing**
```bash
# Collect data once
volt-agent toggl-collect --start-date 2025-10-07 --end-date 2025-10-13

# Test enrichment step multiple times with different LLM prompts
volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45 --force
# Tweak prompt config
volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45 --force
# Compare outputs
```

**Scenario 4: Specific Users Only**
```bash
# Weekly report for leadership team only
volt-agent run-full \
  --start-date 2025-10-07 \
  --end-date 2025-10-13 \
  --users ceo@company.com,cto@company.com,cpo@company.com
```

### Appendix D: Error Handling Examples

**Scenario: Toggl API Failure**
```bash
$ volt-agent toggl-collect --start-date 2025-10-07 --end-date 2025-10-13

✗ Run created: run_2025-10-10-15-30-45
✗ Fetching Toggl data...
  ├─ Day 1/7: ✓ 35 entries
  ├─ Day 2/7: ✗ API Error: 429 Too Many Requests
  ├─ Retrying in 60 seconds...
  ├─ Day 2/7: ✗ API Error: 429 Too Many Requests
  ├─ Retrying in 120 seconds...
  ├─ Day 2/7: ✓ 40 entries
  └─ ...
✓ Step 1 complete!
```

**Scenario: Invalid Run ID**
```bash
$ volt-agent fibery-enrich --run-id invalid_run

✗ Error: Run 'invalid_run' not found
  
  Available runs:
  • run_2025-10-10-15-30-45 (2 hours ago)
  • run_2025-10-09-10-15-30 (1 day ago)
  
  Use 'volt-agent list-runs' to see all runs
```

**Scenario: Corrupted JSON**
```bash
$ volt-agent fibery-enrich --run-id run_2025-10-10-15-30-45

✗ Error: Failed to load toggl_data.json
  File: ./tmp/runs/run_2025-10-10-15-30-45/toggl_data.json
  Reason: Invalid JSON syntax at line 245
  
  Suggested actions:
  1. Re-run step 1: volt-agent toggl-collect --start-date ... --end-date ...
  2. Restore from backup (if available)
  3. Manually fix JSON file
```

---

## 11. Success Criteria

### 11.1 Feature Completeness

- ✅ All v1.0 functionality preserved
- ✅ Step 1 (Toggl Collection) working independently
- ✅ Step 2 (Fibery Enrichment) working independently  
- ✅ Full pipeline working end-to-end
- ✅ Utility commands (list, show, cleanup, validate) working
- ✅ Comprehensive error handling

### 11.2 Quality Metrics

- ✅ Test coverage ≥ 80%
- ✅ No critical bugs
- ✅ Performance targets met
- ✅ All JSON schemas validated
- ✅ Documentation complete

### 11.3 User Acceptance

- ✅ Users can run full pipeline with single command
- ✅ Users can run steps independently
- ✅ Reports match or exceed v1.0 quality
- ✅ CLI is intuitive and helpful
- ✅ Migration from v1.0 is smooth

---

## 12. Glossary

| Term | Definition |
|------|------------|
| **Pipeline** | Series of data processing steps executed sequentially |
| **Step** | Individual unit of work in the pipeline |
| **Run** | Single execution of one or more pipeline steps |
| **Run ID** | Unique identifier for a pipeline run |
| **Run Directory** | File system directory containing all outputs for a run |
| **JSON Cache** | Structured JSON files storing intermediate pipeline data |
| **Matched Entity** | Toggl entry with successfully parsed Fibery metadata |
| **Unmatched Activity** | Toggl entry without Fibery entity reference |
| **Enrichment** | Process of adding Fibery metadata to Toggl data |
| **Idempotent** | Operation that produces same result when repeated |

---

## 13. References

### Internal Documents
- [PRD v1.0: Toggl Team Activity Report Generator](../1-toggl-reports/PRD_Toggl_Team_Activity_Report.md)
- [PRD: Fibery Reports](../2-fibery-reports/PRD_Core.md)

### External Documentation
- [Toggl API Documentation](https://engineering.toggl.com/docs/reports/detailed_reports/)
- [Fibery API Documentation](https://api.fibery.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Click CLI Framework](https://click.palletsprojects.com/)
- [Rich Library](https://rich.readthedocs.io/)

---

**End of Document**

