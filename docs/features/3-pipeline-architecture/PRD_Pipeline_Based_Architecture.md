# Product Requirements Document (PRD)
# Pipeline-Based Architecture for Toggl and Fibery Analysis

**Version:** 2.0
**Date:** October 10, 2025
**Status:** 📋 Planning
**Previous Version:** 1.0 (SQLite-based monolithic architecture)

---

## Executive Summary

This document outlines the requirements for refactoring the Toggl-Fibery analysis system from a monolithic SQLite-based architecture to a **Temporal workflow-based pipeline architecture** using JSON files for caching. The new system uses Temporal for workflow orchestration, providing robust error handling, retry logic, and progress tracking.

### Key Changes from v1.0

1. **Replace SQLite with JSON files** for all caching and data persistence
2. **Temporal-orchestrated workflow** with activities for each processing step
3. **Run-based caching** with structured JSON outputs at each activity
4. **Configurable stage execution** - start from Toggl or Fibery enrichment stage
5. **Rolling window parallelism** for bounded concurrent entity processing
6. **Per-entity-type enrichment** with configurable activity mapping
7. **LLM-generated reports** for all reporting activities
8. **Docker Compose integration** for local Temporal server deployment

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Temporal Workflow Design](#2-temporal-workflow-design)
3. [Workflow Activities](#3-workflow-activities)
4. [Parallelism Pattern](#4-parallelism-pattern)
5. [Data Structures](#5-data-structures)
6. [Command-Line Interface](#6-command-line-interface)
7. [File Structure](#7-file-structure)
8. [Infrastructure](#8-infrastructure)

---

## 1. Architecture Overview

### 1.1 Temporal Workflow Pattern

The new architecture uses **Temporal** for workflow orchestration:

1. **Single Workflow** orchestrates the entire pipeline execution
2. **Activities** represent atomic units of work (data fetching, processing, reporting)
3. **Local Activities** for fast, deterministic operations (file I/O, data transformation)
4. **Regular Activities** for external API calls with retry logic
5. **Cleanup Activities** at the start of each stage to ensure idempotency
6. **Rolling Window Parallelism** for bounded concurrent processing
7. **Temporal Queries** provide real-time progress updates and ETA calculation
8. **JSON-based persistence** for all intermediate data and outputs

### 1.2 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Temporal Workflow: TogglFiberyPipeline              │
└─────────────────────────────────────────────────────────────────┘

Input Parameters:
  - start_date, end_date, users
  - start_from: "toggl" | "fibery" (default: "toggl")
  - run_id: optional (required if start_from="fibery")

Workflow Execution:

[STAGE 1: TOGGL COLLECTION] (if start_from == "toggl")
  ├─ Activity 0: cleanup_toggl_stage() [LOCAL]
  │   → Removes previous Toggl stage outputs for this run
  │
  ├─ Activity 1: fetch_toggl_data()
  │   → Fetches raw Toggl time entries for date range
  │   → Saves to: tmp/runs/{run_id}/raw_toggl_data.json
  │
  ├─ Activity 2: aggregate_toggl_data() [LOCAL]
  │   → Parses entity metadata, groups by user/entity
  │   → Saves to: tmp/runs/{run_id}/toggl_aggregated.json
  │
  └─ Activity 3: generate_toggl_report() [LOCAL, LLM]
      → Uses LLM to generate markdown summary report
      → Saves to: tmp/runs/{run_id}/reports/toggl_summary.md

[STAGE 2: FIBERY ENRICHMENT] (if start_from == "fibery" OR after Stage 1)
  ├─ Activity 4: cleanup_fibery_stage() [LOCAL]
  │   → Removes previous Fibery stage outputs for this run
  │
  ├─ Activity 5: extract_fibery_entities() [LOCAL]
  │   → Reads toggl_aggregated.json
  │   → Returns: List[EntityToEnrich] grouped by (db, type)
  │
  ├─ Activity 6: enrich_entities_by_type() [ROLLING WINDOW]
  │   → For each (db, type) pair:
  │   →   - Select enrichment activity from config
  │   →   - Process entities using rolling window (max_concurrent=5)
  │   → Returns: List[EnrichedEntity]
  │
  ├─ Activity 7: generate_person_reports() [ROLLING WINDOW, LLM]
  │   → For each user:
  │   →   - Aggregate enriched data
  │   →   - Generate LLM summary
  │   → Returns: List[PersonReport]
  │
  ├─ Activity 8: save_enriched_data() [LOCAL]
  │   → Saves enriched entities and person reports
  │   → Saves to: tmp/runs/{run_id}/enriched_data.json
  │   → Saves to: tmp/runs/{run_id}/reports/individual/*.md
  │
  └─ Activity 9: generate_team_report() [LOCAL, LLM]
      → Uses LLM to create aggregated team report
      → Saves to: tmp/runs/{run_id}/reports/team_summary.md

Temporal Query: get_progress()
  → Returns: {current_stage, current_activity, percentage, eta_seconds}
```

### 1.3 Benefits

✅ **Reliability**: Temporal handles failures, retries, and timeouts automatically
✅ **Observability**: Built-in workflow history and progress tracking
✅ **Debuggability**: Inspect Temporal UI for execution history and failures
✅ **Flexibility**: Start from any stage, re-run enrichment without re-fetching Toggl
✅ **Scalability**: Bounded parallelism via rolling window pattern
✅ **Extensibility**: Per-entity-type enrichment activities via configuration
✅ **Idempotency**: Cleanup activities ensure stages can be re-run
✅ **Durability**: Workflow state persisted automatically

---

## 2. Temporal Workflow Design

### 2.1 Workflow: TogglFiberyPipeline

**Workflow ID Format:** `toggl-fibery-{run_id}`
**Task Queue:** `volt-agent-pipeline`
**Execution Timeout:** 2 hours
**Run Timeout:** 2 hours

**Input Parameters:**
```python
@dataclass
class PipelineInput:
    # Date range for Toggl data
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD

    # User filtering
    users: Optional[List[str]] = None  # User emails, None = all users

    # Stage control
    start_from: Literal["toggl", "fibery"] = "toggl"
    run_id: Optional[str] = None  # Required if start_from="fibery"

    # Processing configuration
    config: Optional[Dict[str, Any]] = None  # Override config values
```

**Workflow Logic:**
1. If `start_from == "toggl"`:
   - Generate `run_id` if not provided (format: `run_YYYY-MM-DD-HH-MM-SS`)
   - Execute Toggl cleanup activity
   - Execute Toggl collection activities (1-3)
2. If `start_from == "fibery"`:
   - Validate `run_id` is provided and Toggl data exists
   - Execute Fibery cleanup activity
3. Execute Fibery enrichment activities (5-9) using rolling window for parallelism
4. Update run metadata on success/failure
5. Return final run summary

**Error Handling:**
- If any activity fails, entire workflow fails (no partial success)
- Workflow state is preserved in Temporal for debugging
- Run metadata is marked as "failed" with error details
- Cleanup activities ensure failed runs can be retried cleanly

**Progress Tracking:**
- Workflow implements `get_progress()` query handler
- Returns current stage, activity, completion percentage, and ETA
- Tracks sub-progress for rolling window activities
- Used by CLI for real-time progress display

### 2.2 Retry and Timeout Policies

**Default Activity Retry Policy:**
```python
RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_attempts=1,  # No retries - fail fast
    non_retryable_error_types=["ValueError", "ValidationError"]
)
```

**Activity Timeouts:**
- `fetch_toggl_data`: 30 minutes (handles large datasets, rate limiting)
- `enrich_*_entity`: 2 minutes per entity
- `generate_*_report`: 5 minutes per report (LLM calls)
- Cleanup activities: 5 minutes
- Local activities: 10 minutes (file I/O operations)

**Rationale:**
- Single retry attempt prevents infinite loops and wasted resources
- High timeouts accommodate API rate limiting and large datasets
- Failures are explicit and require manual intervention

---

## 3. Workflow Activities

### Activity 0: cleanup_toggl_stage
**Type:** Local Activity
**Purpose:** Clean up previous Toggl stage outputs to ensure idempotency

**Inputs:**
- `run_id`

**Processing:**
- Remove `raw_toggl_data.json` if exists
- Remove `toggl_aggregated.json` if exists
- Remove `reports/toggl_summary.md` if exists
- Preserve enriched data and fibery reports

**Timeout:** 5 minutes
**Retry:** 1 attempt

---

### Activity 1: fetch_toggl_data
**Type:** Regular Activity
**Purpose:** Fetch raw Toggl time entries from API

**Inputs:**
- `start_date`, `end_date`, `user_emails`, `run_id`

**Processing:**
- Uses existing day-by-day chunking logic
- Respects Toggl API rate limits (240 req/hour)
- Fetches all time entries for specified period

**Output File:** `tmp/runs/{run_id}/raw_toggl_data.json`

**Timeout:** 30 minutes
**Retry:** 1 attempt

---

### Activity 2: aggregate_toggl_data
**Type:** Local Activity
**Purpose:** Parse and aggregate Toggl data by user and entity

**Inputs:**
- `run_id` (reads `raw_toggl_data.json`)

**Processing:**
- Parse Fibery entity metadata using regex
- Group entries by user → matched/unmatched → entity/activity
- Calculate time aggregations
- Generate statistics

**Output File:** `tmp/runs/{run_id}/toggl_aggregated.json`

**Timeout:** 10 minutes
**Retry:** 1 attempt

---

### Activity 3: generate_toggl_report
**Type:** Local Activity
**Purpose:** Use LLM to generate markdown summary report for Toggl data

**Inputs:**
- `run_id` (reads `toggl_aggregated.json`)

**Processing:**
- Read aggregated Toggl data
- Call LLM with prompt to generate:
  - Executive summary
  - Per-user summaries
  - Matched entities overview
  - Unmatched activities summary
  - Time distribution analysis
- Format LLM output as markdown

**Output File:** `tmp/runs/{run_id}/reports/toggl_summary.md`

**Timeout:** 10 minutes (includes LLM call)
**Retry:** 1 attempt

---

### Activity 4: cleanup_fibery_stage
**Type:** Local Activity
**Purpose:** Clean up previous Fibery stage outputs to ensure idempotency

**Inputs:**
- `run_id`

**Processing:**
- Remove `enriched_data.json` if exists
- Remove `reports/individual/*.md` files if exist
- Remove `reports/team_summary.md` if exists
- Preserve Toggl data

**Timeout:** 5 minutes
**Retry:** 1 attempt

---

### Activity 5: extract_fibery_entities
**Type:** Local Activity
**Purpose:** Build list of Fibery entities to enrich, grouped by type

**Inputs:**
- `run_id` (reads `toggl_aggregated.json`)

**Processing:**
- Extract all unique matched entities
- Group by (database, entity_type)
- Return dict: `{(db, type): [entity_ids]}`

**Output:** Returns `Dict[Tuple[str, str], List[str]]` (in-memory)

**Timeout:** 5 minutes
**Retry:** 1 attempt

---

### Activity 6: enrich_entities_by_type
**Type:** Orchestrator Activity (calls entity-specific activities)
**Purpose:** Enrich entities using type-specific activities with rolling window parallelism

**Inputs:**
- `entities_by_type: Dict[Tuple[str, str], List[str]]`
- `run_id`
- `config: EnrichmentConfig`

**Processing:**
1. For each (database, entity_type) pair:
   - Look up enrichment activity from config
   - If no specific activity found, use `default_enrich_entity`
   - Use rolling window pattern (max_concurrent=5) to process entities
   - Each entity processed by its type-specific activity

**Configuration Example:**
```yaml
enrichment_activities:
  "Scrum/Task":
    activity: enrich_scrum_task
    max_concurrent: 5
  "Scrum/Bug":
    activity: enrich_scrum_bug
    max_concurrent: 5
  "Product/Feature":
    activity: enrich_product_feature
    max_concurrent: 3
  default:
    activity: default_enrich_entity
    max_concurrent: 5
```

**Output:** Returns `List[EnrichedEntity]`

**Timeout:** 60 minutes (2 min/entity * 30 entities max per batch)
**Retry:** 1 attempt

**Type-Specific Enrichment Activities:**

Each entity type can have a dedicated enrichment activity that knows how to query specific fields:

```python
async def enrich_scrum_task(entity_id: str, run_id: str) -> EnrichedEntity:
    """Enrich Scrum Task with task-specific fields"""
    # Query Fibery API for Scrum Task fields:
    # - Story Points, Sprint, Epic
    # - Acceptance Criteria
    # - Test Cases linked
    # - etc.
    pass

async def enrich_product_feature(entity_id: str, run_id: str) -> EnrichedEntity:
    """Enrich Product Feature with feature-specific fields"""
    # Query Fibery API for Product Feature fields:
    # - Product Area, Customer Requests
    # - Revenue Impact
    # - Launch Date
    # - etc.
    pass

async def default_enrich_entity(entity_id: str, entity_type: str, run_id: str) -> EnrichedEntity:
    """Default enrichment for entities without specific activity"""
    # Query common fields:
    # - State, dates, description, comments
    # - Assignees, priority, labels
    pass
```

---

### Activity 7: generate_person_reports
**Type:** Orchestrator Activity (calls per-person LLM activity)
**Purpose:** Generate LLM summaries for each user using rolling window

**Inputs:**
- `users: List[str]`  # User emails
- `enriched_entities: List[EnrichedEntity]`
- `run_id`

**Processing:**
- Use rolling window pattern (max_concurrent=3) to process users
- For each user, call `generate_person_report_llm(user, entities)`
- Each person report generated in parallel via LLM

**Output:** Returns `List[PersonReport]`

**Timeout:** 30 minutes (5 min/user * 6 users max per batch)
**Retry:** 1 attempt

**Per-Person Activity:**
```python
async def generate_person_report_llm(user_email: str, enriched_entities: List[EnrichedEntity]) -> PersonReport:
    """Generate LLM summary for one person's work"""
    # Filter entities for this user
    # Call LLM with prompt to generate:
    # - Overall summary
    # - Matched entities summary
    # - Unmatched activities summary
    # - Work patterns and insights
    pass
```

---

### Activity 8: save_enriched_data
**Type:** Local Activity
**Purpose:** Save all enriched entities and person reports to files

**Inputs:**
- `run_id`
- `enriched_entities: List[EnrichedEntity]`
- `person_reports: List[PersonReport]`

**Processing:**
- Merge enriched entities with toggl_aggregated data
- Save to enriched_data.json
- Create individual markdown files per person from PersonReport
- Update run metadata with statistics

**Output Files:**
- `tmp/runs/{run_id}/enriched_data.json`
- `tmp/runs/{run_id}/reports/individual/{user_slug}.md`

**Timeout:** 10 minutes
**Retry:** 1 attempt

---

### Activity 9: generate_team_report
**Type:** Local Activity
**Purpose:** Use LLM to create aggregated team markdown report

**Inputs:**
- `run_id` (reads `enriched_data.json`)

**Processing:**
- Read all enriched data
- Call LLM with prompt to generate:
  - Team-level executive summary
  - Key accomplishments
  - Cross-team patterns
  - Resource allocation insights
  - Recommendations
- Format LLM output as markdown

**Output File:** `tmp/runs/{run_id}/reports/team_summary.md`

**Timeout:** 10 minutes (includes LLM call)
**Retry:** 1 attempt

---

## 4. Parallelism Pattern

### 4.1 Rolling Window Parallel Processing

**Overview:** A pattern for processing large lists of entities with bounded concurrency using a sliding window approach. This ensures controlled parallelism without overwhelming external services or system resources.

**Problem**: Need to process a large list of entities in parallel, but want to limit concurrent operations to avoid overwhelming external APIs, rate limits, or system resources.

**Solution**: Use a rolling window pattern where a fixed number of tasks run concurrently, and new tasks are started immediately as previous ones complete.

### 4.2 Implementation Structure

1. **Data Structures**:
   - **Queue**: A deque (double-ended queue) holding unprocessed entities
   - **Running Tasks**: A dictionary mapping active asyncio tasks to their entities
   - **Results**: A list accumulating outcomes from completed tasks

2. **Algorithm**:
   1. Initialize:
      - Load all entities into a deque
      - Set max_concurrent limit (e.g., 5)
      - Create empty tracking structures
   2. Start Initial Batch:
      - Launch up to max_concurrent tasks
      - Add each task to running tasks dictionary
   3. Process Until Complete:
      - While running tasks exist:
        a. Wait for ANY task to complete (FIRST_COMPLETED)
        b. Collect result from completed task
        c. Remove from running tasks
        d. If entities remain in queue:
           - Pop next entity
           - Start new task
           - Add to running tasks
   4. Return aggregated results

3. **Key Parameters**:
   - `max_concurrent`: Maximum number of parallel operations (typically 3-10)
   - `timeout`: Per-entity processing timeout
   - `retry_policy`: Retry behavior for failed operations

### 4.3 Code Template

```python
from collections import deque
import asyncio
from typing import List, Any, Callable

async def process_with_rolling_window(
    entities: List[Any],
    process_fn: Callable,
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process entities in parallel using rolling window pattern.

    Args:
        entities: List of entities to process
        process_fn: Async function to process each entity
        max_concurrent: Max parallel operations

    Returns:
        List of results from processing each entity
    """
    remaining = deque(entities)
    running = {}  # task -> entity
    results = []

    # Start initial batch
    while len(running) < max_concurrent and remaining:
        entity = remaining.popleft()
        task = asyncio.create_task(process_fn(entity))
        running[task] = entity

    # Process as they complete
    while running:
        done, pending = await asyncio.wait(
            running.keys(),
            return_when=asyncio.FIRST_COMPLETED
        )

        for completed_task in done:
            entity = running.pop(completed_task)
            result = completed_task.result()  # May raise exception
            results.append(result)

            # Start next if available
            if remaining:
                next_entity = remaining.popleft()
                next_task = asyncio.create_task(process_fn(next_entity))
                running[next_task] = next_entity

    return results
```

### 4.4 Usage in Workflow

```python
# In Activity 6: enrich_entities_by_type
async def enrich_entities_by_type(entities_by_type, run_id, config):
    all_enriched = []

    for (db, entity_type), entity_ids in entities_by_type.items():
        # Get activity function for this type
        activity_fn = get_enrichment_activity(db, entity_type, config)

        # Process with rolling window
        enriched = await process_with_rolling_window(
            entities=entity_ids,
            process_fn=lambda eid: activity_fn(eid, run_id),
            max_concurrent=config.get_max_concurrent(db, entity_type)
        )

        all_enriched.extend(enriched)

    return all_enriched
```

### 4.5 Advantages

✅ **Bounded Concurrency**: Never exceeds the specified limit, preventing resource exhaustion
✅ **Continuous Processing**: No idle time between batches - starts new work immediately
✅ **Early Results**: Results available as soon as individual tasks complete
✅ **Efficient Resource Usage**: Maintains steady load on system and external services
✅ **Fail-Fast**: Exceptions propagate immediately, allowing quick failure detection

### 4.6 When to Use

✅ **Good fit when**:
- Processing requires external API calls with rate limits
- Individual operations have variable completion times
- Need to balance throughput with resource constraints
- Want continuous processing without batch delays

❌ **Not ideal when**:
- Operations are extremely fast (< 10ms)
- No external dependencies or rate limits
- Simple sequential processing is sufficient
- Need strict ordering guarantees

---

## 5. Data Structures

### 5.1 Run Metadata (`run_metadata.json`)

```json
{
  "run_id": "run_2025-10-10-15-30-45",
  "workflow_id": "toggl-fibery-run_2025-10-10-15-30-45",
  "created_at": "2025-10-10T15:30:45Z",
  "status": "in_progress",
  "pipeline_version": "2.0",
  "parameters": {
    "start_date": "2025-10-07",
    "end_date": "2025-10-13",
    "users_filter": ["user1@example.com"],
    "start_from": "toggl"
  },
  "temporal_metadata": {
    "workflow_id": "toggl-fibery-run_2025-10-10-15-30-45",
    "run_id": "temporal-run-uuid",
    "task_queue": "volt-agent-pipeline"
  },
  "stages_completed": ["toggl", "fibery"],
  "stages_failed": []
}
```

### 5.2 Enrichment Configuration

**File:** `config/enrichment_config.yaml`

```yaml
enrichment_activities:
  # Scrum entities
  "Scrum/Task":
    activity: enrich_scrum_task
    max_concurrent: 5
    fields:
      - Story Points
      - Sprint
      - Epic
      - Acceptance Criteria

  "Scrum/Bug":
    activity: enrich_scrum_bug
    max_concurrent: 5
    fields:
      - Severity
      - Steps to Reproduce
      - Root Cause

  # Product entities
  "Product/Feature":
    activity: enrich_product_feature
    max_concurrent: 3
    fields:
      - Product Area
      - Customer Requests
      - Revenue Impact
      - Launch Date

  # Default for all other types
  default:
    activity: default_enrich_entity
    max_concurrent: 5
    fields:
      - State
      - Dates
      - Description
      - Comments
      - Assignees
```

---

## 6. Command-Line Interface

### 6.1 Main Pipeline Command

```bash
# Start from beginning (Toggl collection)
volt-agent run \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD \
  [--users email1@example.com,email2@example.com] \
  [--output-dir ./tmp/runs]

# Start from Fibery enrichment (re-run enrichment only)
volt-agent run \
  --start-from fibery \
  --run-id run_2025-10-10-15-30-45
```

**Options:**
- `--start-date` (required if start-from=toggl): Start date of reporting period
- `--end-date` (required if start-from=toggl): End date of reporting period
- `--users` (optional): Comma-separated user emails (default: all users)
- `--start-from` (optional): Stage to start from (default: toggl)
  - `toggl`: Start from Toggl collection (full pipeline)
  - `fibery`: Start from Fibery enrichment (requires --run-id)
- `--run-id` (required if start-from=fibery): Existing run ID to enrich
- `--output-dir` (optional): Base directory for runs (default: `./tmp/runs`)

**Examples:**
```bash
# Initial run: collect Toggl data and enrich
volt-agent run --start-date 2025-10-07 --end-date 2025-10-13

# Re-run Fibery enrichment only (e.g., after config changes)
volt-agent run --start-from fibery --run-id run_2025-10-10-15-30-45

# Run for specific users only
volt-agent run --start-date 2025-10-07 --end-date 2025-10-13 \
  --users john@example.com,jane@example.com
```

### 6.2 Progress Display

```
╭──────────────────────────────────────────────────────────────╮
│ Toggl-Fibery Pipeline                                        │
│ Run ID: run_2025-10-10-15-30-45                             │
│ Stage: Fibery Enrichment                                     │
╰──────────────────────────────────────────────────────────────╯

[Activity 6/9] Enriching entities by type
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 68% | ETA: 2m 15s

Details:
  ├─ Current: Scrum/Task (15/20 entities)
  ├─ Completed: Scrum/Bug (8/8 entities)
  ├─ Remaining: Product/Feature (12 entities)
  ├─ Elapsed: 3m 42s
  └─ Rate: 0.45 entities/sec

Press 'q' to quit monitoring (workflow continues in background)
Press 'd' for detailed view in Temporal UI
```

### 6.3 Utility Commands

```bash
# List all runs
volt-agent list-runs [--limit 10] [--status completed|failed|in_progress]

# Show run details
volt-agent show-run --run-id RUN_ID

# Cancel running workflow
volt-agent cancel-run --run-id RUN_ID

# Open Temporal UI for run
volt-agent temporal-ui --run-id RUN_ID
```

---

## 7. File Structure

### 7.1 Directory Layout

```
volt-agent/
├── tmp/
│   └── runs/
│       └── run_2025-10-10-15-30-45/
│           ├── run_metadata.json
│           ├── raw_toggl_data.json
│           ├── toggl_aggregated.json
│           ├── enriched_data.json
│           └── reports/
│               ├── toggl_summary.md
│               ├── team_summary.md
│               └── individual/
│                   ├── john_doe.md
│                   └── jane_smith.md
├── src/
│   ├── cli.py
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── pipeline_workflow.py         # Temporal workflow
│   ├── activities/
│   │   ├── __init__.py
│   │   ├── cleanup_activities.py        # Cleanup activities
│   │   ├── toggl_activities.py          # Activities 1-3
│   │   ├── fibery_activities.py         # Activity 5
│   │   ├── enrichment/
│   │   │   ├── __init__.py
│   │   │   ├── scrum_task.py            # enrich_scrum_task
│   │   │   ├── scrum_bug.py             # enrich_scrum_bug
│   │   │   ├── product_feature.py       # enrich_product_feature
│   │   │   └── default.py               # default_enrich_entity
│   │   └── reporting_activities.py      # Activities 7-9
│   ├── patterns/
│   │   ├── __init__.py
│   │   └── rolling_window.py            # Rolling window implementation
│   ├── worker.py                        # Temporal worker
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── json_storage.py
│   │   └── schemas.py
│   ├── toggl/                           # Existing clients
│   ├── fibery/
│   └── llm/
├── docker-compose.yml                   # Temporal + dependencies
└── config/
    ├── config.yaml
    └── enrichment_config.yaml           # Per-entity-type config
```

### 7.2 Temporal Worker Structure

```python
# src/worker.py
from temporalio.client import Client
from temporalio.worker import Worker
from activities.cleanup_activities import cleanup_toggl_stage, cleanup_fibery_stage
from activities.toggl_activities import fetch_toggl_data, aggregate_toggl_data, generate_toggl_report
from activities.fibery_activities import extract_fibery_entities, enrich_entities_by_type
from activities.reporting_activities import generate_person_reports, save_enriched_data, generate_team_report
from activities.enrichment import (
    enrich_scrum_task,
    enrich_scrum_bug,
    enrich_product_feature,
    default_enrich_entity
)

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="volt-agent-pipeline",
        workflows=[TogglFiberyPipeline],
        activities=[
            # Cleanup
            cleanup_toggl_stage,
            cleanup_fibery_stage,
            # Toggl
            fetch_toggl_data,
            aggregate_toggl_data,
            generate_toggl_report,
            # Fibery
            extract_fibery_entities,
            enrich_entities_by_type,
            # Enrichment (type-specific)
            enrich_scrum_task,
            enrich_scrum_bug,
            enrich_product_feature,
            default_enrich_entity,
            # Reporting
            generate_person_reports,
            save_enriched_data,
            generate_team_report,
        ],
    )

    await worker.run()
```

---

## 8. Infrastructure

### 8.1 Docker Compose Setup

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    depends_on:
      - postgresql

  temporal-ui:
    image: temporalio/ui:latest
    ports:
      - "8080:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=http://localhost:3000
    depends_on:
      - temporal

  postgresql:
    image: postgres:13
    environment:
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
      POSTGRES_DB: temporal
    ports:
      - "5432:5432"
    volumes:
      - temporal-postgres:/var/lib/postgresql/data

  temporal-admin-tools:
    image: temporalio/admin-tools:latest
    environment:
      - TEMPORAL_CLI_ADDRESS=temporal:7233
    depends_on:
      - temporal
    stdin_open: true
    tty: true

volumes:
  temporal-postgres:
```

### 8.2 Starting the Infrastructure

```bash
# Start Temporal and dependencies
docker-compose up -d

# Verify services are running
docker-compose ps

# View Temporal UI
open http://localhost:8080

# Start Temporal worker
python -m src.worker

# Run pipeline (from Toggl)
volt-agent run --start-date 2025-10-07 --end-date 2025-10-13

# Run pipeline (from Fibery only)
volt-agent run --start-from fibery --run-id run_2025-10-10-15-30-45
```

### 8.3 Temporal Configuration

**Connection Settings:**
- **Temporal Server:** `localhost:7233`
- **Temporal UI:** `http://localhost:8080`
- **Task Queue:** `volt-agent-pipeline`
- **Namespace:** `default`

**Worker Configuration:**
```python
worker_config = {
    "max_concurrent_activities": 10,
    "max_concurrent_workflow_tasks": 1,
    "max_concurrent_local_activities": 10,
}
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Workflow** | Temporal workflow orchestrating the entire pipeline |
| **Activity** | Individual unit of work executed by Temporal worker |
| **Local Activity** | Fast, deterministic activity (file I/O, data transformation) |
| **Regular Activity** | Activity with external dependencies (API calls) |
| **Cleanup Activity** | Activity that removes previous stage outputs for idempotency |
| **Rolling Window** | Parallelism pattern with bounded concurrency |
| **Task Queue** | Temporal queue where workflow and activity tasks are dispatched |
| **Worker** | Process that polls task queue and executes activities |
| **Run** | Single execution of the pipeline workflow |
| **Run ID** | Unique identifier for a pipeline run |
| **Stage** | Major phase of pipeline (Toggl or Fibery) |

---

## References

### Internal Documents
- [PRD v1.0: Toggl Team Activity Report Generator](../1-toggl-reports/PRD_Toggl_Team_Activity_Report.md)
- [PRD: Fibery Reports](../2-fibery-reports/PRD_Core.md)

### External Documentation
- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [Toggl API Documentation](https://engineering.toggl.com/docs/reports/detailed_reports/)
- [Fibery API Documentation](https://api.fibery.io/)
- [Rich Library](https://rich.readthedocs.io/)

---

**End of Document**
