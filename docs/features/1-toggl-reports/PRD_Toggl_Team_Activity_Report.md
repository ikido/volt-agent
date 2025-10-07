# Product Requirements Document (PRD)
# Toggl Team Activity Report Generator

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** ✅ Implemented  
**Implementation Date:** October 3, 2025  

---

## Implementation Notes

### What We Built
- ✅ Python-based pipeline generating team activity reports from Toggl data
- ✅ JSON API with `enrich_response=true` (not CSV) for complete data including user IDs
- ✅ **Daily chunking** to avoid API pagination limits (fetches day-by-day)
- ✅ SQLite caching with upsert operations
- ✅ Fibery.io entity parser using regex
- ✅ OpenAI GPT-4 integration with **concise, structured prompts**
- ✅ **Streaming report generation** - writes each user's report immediately to file
- ✅ Individual and team markdown reports in `./tmp/` directory

### Key Implementation Differences from Original PRD
1. **API Approach**: Uses JSON API with `enrich_response=true` instead of CSV (CSV lacks entry IDs and user IDs)
2. **Pagination Strategy**: Fetches data **day-by-day** to avoid API pagination limits that truncate results
3. **Report Format**: Simplified to concise bullet lists:
   - Project entities: One line per entity with ID, type, database, project, and 1-sentence summary
   - Other activities: Short bullet points for each activity type
4. **Output Location**: Reports go to `./tmp/` (project directory) not `/tmp/` (system directory)
5. **Streaming Writes**: Reports written incrementally as generated, not accumulated in memory
6. **User Filter**: Optional `--users` parameter (defaults to all workspace users)

### Performance
- ~200 entries per week for 11-person team
- 7-15 API calls (one per day + pagination)
- ~2 minutes to generate full reports including LLM summaries
- Properly handles timezones in timestamps

---

## 1. Executive Summary

This document outlines the requirements for developing a Python-based pipeline that generates comprehensive team activity reports by pulling time tracking data from Toggl, caching it locally in SQLite, and using OpenAI's LLM to create intelligent summaries. The system will parse Fibery.io entity metadata from time entry descriptions and provide both individual and team-level insights into work activities.

---

## 2. Objectives

### Primary Goal
Create an automated reporting system that transforms raw Toggl time entries into actionable insights about team activities over a specified period.

### Key Deliverables
1. **Data Extraction Script**: Pull detailed time entries from Toggl API
2. **Local Caching System**: SQLite database to cache and manage time entries
3. **Entity Parser**: Extract Fibery.io metadata from time entry descriptions
4. **LLM Integration**: Generate summaries using OpenAI API
5. **Report Generator**: Create timestamped markdown reports

---

## 3. Functional Requirements

### 3.1 Command-Line Interface

The script shall accept the following command-line arguments:

| Argument | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `--start-date` | String (YYYY-MM-DD) | Yes | Start date for the reporting period | `2025-09-23` |
| `--end-date` | String (YYYY-MM-DD) | Yes | End date for the reporting period | `2025-09-29` |
| `--users` | List of strings | **No** ✅ | Comma-separated list of user emails (optional, defaults to all users) | `user1@example.com,user2@example.com` |
| `--use-cache` | Boolean flag | No | Use cached data instead of fetching from Toggl | `--use-cache` |

**Example Usage:**
```bash
# All users
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29

# Specific users
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --users user1@example.com,user2@example.com
```

**Development Mode Usage:**
```bash
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --use-cache
```

### 3.2 Data Retrieval from Toggl

#### API Endpoint
- **Endpoint**: `POST https://api.track.toggl.com/reports/api/v3/workspace/{workspace_id}/search/time_entries`
- **Documentation**: https://engineering.toggl.com/docs/reports/detailed_reports/

#### Authentication
- **Method**: HTTP Basic Authentication
- **Credentials**: API token (stored in `.env` file)
- **Format**: `{api_token}:api_token` (username:password)

#### Request Parameters
```json
{
  "start_date": "2025-09-23",
  "end_date": "2025-09-29",
  "user_ids": [123, 456, 789]
}
```

#### Response Structure
The API returns time entries with the following key fields:
- `id`: Unique identifier for the time entry
- `workspace_id`: Workspace identifier
- `user_id`: User identifier
- `username`: User's name
- `user_email`: User's email
- `description`: Time entry description (contains Fibery.io metadata)
- `start`: Start timestamp (ISO 8601)
- `stop`: End timestamp (ISO 8601)
- `duration`: Duration in seconds
- `tags`: Array of tags
- `project_id`: Project identifier (if any)
- `project_name`: Project name (if any)

#### Pagination Handling
- **Initial Request**: Returns up to 50 time entries
- **Headers for Pagination**:
  - `X-Next-ID`: ID of the next entry to fetch
  - `X-Next-Row-Number`: Row number for the next page
- **Strategy**: Continue making requests with updated pagination parameters until no more data is returned
- **Implementation**: Implement automatic pagination loop to fetch all entries

#### Rate Limiting
- **Current Subscription**: Starter plan (240 requests per hour)
- **Configuration**: `TOGGL_RPH` (Toggl Requests Per Hour) set to 240 in config file
- **Implementation**: Track request timestamps and ensure we don't exceed rate limit

**Error Handling**:
- HTTP 429 (Too Many Requests): Implement exponential backoff
- HTTP 402 (Payment Required): Indicates rate limit exceeded, implement retry with exponential backoff
- **Backoff Strategy**: Start with 60 seconds, double on each retry, max 5 retries

### 3.3 Data Processing

#### Time Entry Grouping
- Group time entries by identical `description` field
- Sum `duration` values for grouped entries
- Preserve all metadata (user, dates, tags) for grouped entries

#### Entity Metadata Parsing

Parse Fibery.io metadata from descriptions using the following format:

**Example Description:**
```
? Нет полей Stage, Next action, Owner, Alternate names #1112 [Scrum] [Sub-bug] [Moneyball]
```

**Extracted Fields:**
- **Description Text**: `? Нет полей Stage, Next action, Owner, Alternate names`
- **Entity ID**: `#1112` (extract using regex: `#(\d+)`)
- **Entity Database**: `[Scrum]` (first bracketed tag)
- **Entity Type**: `[Sub-bug]` (second bracketed tag)
- **Project**: `[Moneyball]` (last bracketed tag)

**Parsing Rules:**
1. **IMPORTANT**: Parse from the END of the description - tags and entity ID are at the end
2. Extract entity ID using pattern: `#(\d+)` searching from the end of the string
3. Extract all bracketed tags: `\[([^\]]+)\]` from the end portion of the description
4. Everything before the entity metadata is the description text (may contain any special characters)
5. Classify tags in order: Database, Type, Project (handle variable number of tags)
6. If no entity ID found, mark as "unmatched"

**Edge Cases to Handle:**
- Descriptions without any Fibery.io metadata
- Descriptions with partial metadata (e.g., only entity ID, no tags)
- Multiple entity IDs in one description
- Non-English characters in descriptions

### 3.4 Local Data Storage (SQLite)

#### Database Schema

**Table: `runs`**
```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    user_emails TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'in_progress', 'completed', 'failed'
    total_entries INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Table: `toggl_time_entries`**
Raw cached data from Toggl API
```sql
CREATE TABLE toggl_time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    toggl_id INTEGER NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    workspace_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    user_email TEXT NOT NULL,
    description TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    stop_time DATETIME NOT NULL,
    duration INTEGER NOT NULL,  -- in seconds
    tags TEXT,  -- JSON array
    project_id INTEGER,
    project_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
```

**Table: `processed_time_entries`**
Processed data with parsed metadata and aggregations
```sql
CREATE TABLE processed_time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    description_clean TEXT NOT NULL,  -- Description without metadata
    entity_id TEXT,  -- e.g., "1112"
    entity_database TEXT,  -- e.g., "Scrum"
    entity_type TEXT,  -- e.g., "Sub-bug"
    project TEXT,  -- e.g., "Moneyball"
    is_matched BOOLEAN NOT NULL,  -- TRUE if entity ID was found
    total_duration INTEGER NOT NULL,  -- summed duration in seconds
    entry_count INTEGER NOT NULL,  -- number of raw entries aggregated
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id),
    UNIQUE(user_email, description_clean, entity_id, entity_database, entity_type, project)
);
```

**Table: `reports`**
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    report_type TEXT NOT NULL,  -- 'individual', 'team'
    user_email TEXT,  -- NULL for team reports
    content TEXT NOT NULL,  -- Markdown content
    file_path TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
```

#### Data Synchronization Strategy

**Run ID Generation:**
- Format: `run_{YYYY-MM-DD-HH-MM}_{UUID4_short}`
- Example: `run_2025-09-29-14-30_a7b3c4d5`

**Update Strategy (Upsert Pattern):**

**Step 1: Upsert Raw Toggl Data**
1. Create new run entry with unique `run_id`
2. Fetch all time entries from Toggl for the specified period
3. For each time entry:
   - **UPSERT** into `toggl_time_entries` based on `toggl_id`:
     - If `toggl_id` exists: Update all fields including `run_id` and `updated_at`
     - If not exists: Insert new record with current `run_id`

**Step 2: Process and Upsert Processed Entries**
4. Parse metadata from all `toggl_time_entries` for the current run
5. Group by `user_email` + `description_clean` + `entity_id` + `entity_database` + `entity_type` + `project`
6. Sum durations and count entries for each group
7. For each processed group:
   - **UPSERT** into `processed_time_entries` based on unique combination:
     - Unique key: `(user_email, description_clean, entity_id, entity_database, entity_type, project)`
     - If combination exists: Update `run_id`, `total_duration`, `entry_count`, and `updated_at`
     - If not exists: Insert new record with current `run_id`

**Benefits:**
- Always have latest data from Toggl cached locally
- Processed entries stay up-to-date with latest aggregations
- Historical tracking by run_id for both raw and processed data
- Efficient upsert operations
- Simple filtering by run_id for reports

### 3.5 Analysis and Reporting

#### Per-User Analysis

For each user in the specified email list:

**1. Time Tracking Metrics:**
- Total time tracked (sum of all durations)
- Total time on matched entities (entries with entity ID)
- Total time on unmatched entities (entries without entity ID)
- Percentage breakdown

**2. LLM Summarization - Matched Entities:**

**Prompt Template:**
```
You are analyzing time tracking data for a team member. Below is a list of time entries 
that were matched to entities in our project management system (Fibery.io).

Each entry includes:
- Entity ID (e.g., #1112)
- Entity Type (e.g., Sub-bug, Task, Feature)
- Entity Database (e.g., Scrum, Kanban)
- Project (e.g., Moneyball)
- Description of work done
- Time spent (in hours)

Your task is to create a comprehensive summary of what this person worked on. 
IMPORTANT: Do not omit any entities or activities. Group related work together when 
appropriate, but ensure every entity mentioned in the data appears in your summary.

Format your response as:
1. Overview (2-3 sentences about overall focus areas)
2. Detailed breakdown by project or entity type
3. Notable patterns or focus areas

Time entries:
{matched_entries}

Generate the summary now:
```

**3. LLM Summarization - Unmatched Entities:**

**Prompt Template:**
```
You are analyzing time tracking data for a team member. Below is a list of time entries 
that could NOT be matched to specific entities in our project management system.

These entries may include:
- Administrative tasks
- Meetings
- Research or exploration
- Tasks not yet tracked in the project management system
- Miscellaneous activities

Your task is to create a comprehensive summary of these activities.
IMPORTANT: Do not omit any entries. Group similar activities together when appropriate.

Format your response as:
1. Overview (2-3 sentences)
2. Categorized breakdown (e.g., meetings, admin, research)
3. Time distribution across categories

Time entries:
{unmatched_entries}

Generate the summary now:
```

**4. Individual Report Structure:**

```markdown
# Individual Activity Report: {User Name}
**Period:** {start_date} to {end_date}  
**Generated:** {timestamp}

---

## Summary Statistics

- **Total Time Tracked:** {total_hours} hours
- **Time on Project Entities:** {matched_hours} hours ({matched_percentage}%)
- **Time on Other Activities:** {unmatched_hours} hours ({unmatched_percentage}%)

---

## Work on Project Entities

{LLM_summary_matched}

---

## Other Activities

{LLM_summary_unmatched}

---
```

#### Team-Level Analysis

**Team Summary LLM Prompt:**

```
You are creating a comprehensive team activity report based on individual team member reports.

Below are the individual activity summaries for each team member for the period 
{start_date} to {end_date}.

Your task is to synthesize this information into a cohesive team report that:
1. Provides an executive summary of team activities
2. Identifies major focus areas and projects worked on
3. Highlights patterns in how time was distributed
4. Notes any areas that received significant team attention
5. Identifies any gaps or unusual patterns

IMPORTANT: Ensure the report is comprehensive and captures all major activities across 
the team. Do not omit significant projects or focus areas.

Individual Reports:
{individual_reports}

Generate the team summary now:
```

**Team Report Structure:**

```markdown
# Team Activity Report
**Period:** {start_date} to {end_date}  
**Generated:** {timestamp}  
**Team Members:** {user_count}

---

## Executive Summary

{LLM_executive_summary}

---

## Team Statistics

- **Total Team Time Tracked:** {total_hours} hours
- **Time on Project Entities:** {matched_hours} hours ({matched_percentage}%)
- **Time on Other Activities:** {unmatched_hours} hours ({unmatched_percentage}%)

### Time Distribution by Team Member

| Team Member | Total Hours | Project Work | Other Work |
|-------------|-------------|--------------|------------|
{per_user_table}

---

## Detailed Analysis

{LLM_detailed_analysis}

---

## Appendix: Individual Reports

{links_to_individual_reports}

---
```

### 3.6 Output Files

All output files shall be written to `./tmp` directory with timestamps:

**Timestamp Format:** `YYYY-MM-DD-HH-MM`

**File 1: Process Log**
- **Filename:** `toggl_report_log_{timestamp}.log`
- **Example:** `toggl_report_log_2025-09-29-14-30.log`
- **Content:** Detailed execution log including:
  - Script start time
  - API requests made (with response codes)
  - Number of entries fetched per page
  - Parsing results (matched vs unmatched)
  - Database operations (inserts, updates)
  - LLM API calls (tokens used)
  - Any errors or warnings
  - Script completion time

**File 2: Individual Reports**
- **Filename:** `toggl_individual_reports_{timestamp}.md`
- **Example:** `toggl_individual_reports_2025-09-29-14-30.md`
- **Content:** Concatenated individual reports for all users

**File 3: Team Summary**
- **Filename:** `toggl_team_summary_{timestamp}.md`
- **Example:** `toggl_team_summary_2025-09-29-14-30.md`
- **Content:** Comprehensive team activity report

---

## 4. Non-Functional Requirements

### 4.1 Performance

- **API Request Efficiency**: Minimize API calls through effective caching
- **Pagination Performance**: Handle up to 10,000 time entries efficiently
- **Database Performance**: Index key fields (`toggl_id`, `run_id`, `user_email`)
- **LLM Call Optimization**: Batch entries when possible to reduce API calls
- **Execution Time Target**: Complete full report for 5 users, 1 week period in < 2 minutes

### 4.2 Security

**Environment Variables (.env):**
```
TOGGL_API_TOKEN=your_api_token_here
TOGGL_WORKSPACE_ID=123456
OPENAI_API_KEY=your_openai_api_key_here
```

**Security Measures:**
- Never commit `.env` file to version control
- Use `.gitignore` to exclude `.env`
- Validate all environment variables on script startup
- Sanitize user inputs to prevent SQL injection
- Use parameterized SQL queries

### 4.3 Reliability

**Error Handling:**
- Graceful degradation if LLM API is unavailable
- Retry logic for transient API failures
- Comprehensive logging for debugging
- Validation of API responses before processing
- Database transaction rollback on errors

**Data Integrity:**
- Validate date formats
- Verify user email existence in Toggl before filtering
- Ensure workspace ID is valid
- Check for data consistency after database updates

### 4.4 Maintainability

**Code Organization:**
```
volt-agent/
├── .env                          # Environment variables (git-ignored)
├── .gitignore
├── README.md
├── requirements.txt              # Python dependencies
├── config/
│   ├── config.yaml              # Rate limits, API settings
│   └── prompts.yaml             # LLM prompt templates
├── src/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── cli.py                   # CLI argument parsing
│   ├── toggl/
│   │   ├── __init__.py
│   │   ├── client.py           # Toggl API client
│   │   └── models.py           # Data models
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py               # SQLite operations
│   │   └── schema.sql          # Database schema
│   ├── parser/
│   │   ├── __init__.py
│   │   └── fibery_parser.py    # Entity metadata parser
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py           # OpenAI API client
│   │   └── prompts.py          # Prompt management
│   └── reporting/
│       ├── __init__.py
│       ├── generator.py        # Report generation
│       └── templates.py        # Report templates
└── tests/
    ├── __init__.py
    ├── test_toggl_client.py
    ├── test_parser.py
    ├── test_database.py
    └── test_reporting.py
```

**Logging Configuration:**
```python
# Multiple log levels for different components
- DEBUG: Detailed debugging information
- INFO: General informational messages
- WARNING: Warning messages for unusual but handled situations
- ERROR: Error messages for failures
- CRITICAL: Critical errors that may cause script to fail
```

### 4.5 Scalability Considerations
- Database indexing for performance with large datasets
- Efficient upsert operations to minimize database writes
- Pagination handling for unlimited time entries
- Request rate limiting to respect API quotas

---

## 5. Configuration Management

### 5.1 Configuration File (config.yaml)

```yaml
# Toggl API Configuration
toggl:
  api_base_url: "https://api.track.toggl.com/reports/api/v3"
  workspace_id: 123456  # Can be overridden by TOGGL_WORKSPACE_ID env var
  timeout_seconds: 30
  max_retries: 3
  retry_backoff_factor: 2.0
  toggl_rph: 240  # Requests per hour (Starter plan)
  
  # Pagination settings
  page_size: 50  # Maximum allowed by Toggl

# OpenAI Configuration
openai:
  model: "gpt-4-turbo-preview"
  max_tokens: 4000
  temperature: 0.3  # Lower for more factual summaries
  timeout_seconds: 60
  max_retries: 3

# Database Configuration
database:
  path: "./data/toggl_cache.db"
  backup_enabled: true
  backup_path: "./data/backups/"

# Output Configuration
output:
  directory: "./tmp"
  log_level: "INFO"
  
# Parsing Configuration
parsing:
  entity_id_pattern: "#(\\d+)"
  tag_pattern: "\\[([^\\]]+)\\]"
  
# Report Configuration
reports:
  include_metadata: true
```

### 5.2 Environment Variables (.env)

```bash
# Toggl API Credentials
TOGGL_API_TOKEN=your_toggl_api_token_here
TOGGL_WORKSPACE_ID=123456

# OpenAI API Credentials
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Override config settings
# LOG_LEVEL=DEBUG
```

### 5.3 Dependencies (requirements.txt)

```
# API clients
requests==2.31.0
openai==1.3.0

# Data processing
python-dotenv==1.0.0
pydantic==2.4.2
pyyaml==6.0.1

# CLI
click==8.1.7
rich==13.6.0  # For beautiful CLI output

# Date/time handling
python-dateutil==2.8.2

# Logging
structlog==23.2.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
responses==0.24.1  # For mocking API calls
```

---

## 6. API Integration Specifications

### 6.1 Toggl API Details

**Base URL:** `https://api.track.toggl.com/reports/api/v3`

**Authentication:**
```python
import requests
from requests.auth import HTTPBasicAuth

api_token = "your_api_token"
auth = HTTPBasicAuth(api_token, "api_token")
```

**Example Request:**
```python
url = f"https://api.track.toggl.com/reports/api/v3/workspace/{workspace_id}/search/time_entries"

payload = {
    "start_date": "2025-09-23",
    "end_date": "2025-09-29",
    "user_ids": [123, 456]
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, auth=auth)
```

**Pagination Example:**
```python
all_entries = []
next_id = None
next_row_number = None

while True:
    payload = {
        "start_date": "2025-09-23",
        "end_date": "2025-09-29",
        "user_ids": [123, 456]
    }
    
    if next_id:
        payload["next_id"] = next_id
    if next_row_number:
        payload["next_row_number"] = next_row_number
    
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    data = response.json()
    
    all_entries.extend(data.get("data", []))
    
    # Check pagination headers
    next_id = response.headers.get("X-Next-ID")
    next_row_number = response.headers.get("X-Next-Row-Number")
    
    if not next_id or not next_row_number:
        break  # No more pages
```

**Rate Limit Handling:**
```python
import time

def make_request_with_retry(url, payload, auth, max_retries=5):
    backoff = 60  # Start with 60 seconds
    
    for attempt in range(max_retries):
        response = requests.post(url, json=payload, auth=auth)
        
        if response.status_code == 200:
            return response
        elif response.status_code in [402, 429]:
            # Rate limit exceeded
            print(f"Rate limit hit. Waiting {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff
        else:
            response.raise_for_status()
    
    raise Exception("Max retries exceeded")
```

### 6.2 OpenAI API Details

**Client Initialization:**
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**Example LLM Call:**
```python
def generate_summary(entries, prompt_template):
    prompt = prompt_template.format(entries=entries)
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are an expert at analyzing time tracking data."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000,
        temperature=0.3
    )
    
    return response.choices[0].message.content
```

**Token Management:**
- Monitor token usage per request
- Estimate costs based on OpenAI pricing
- Implement token budget limits if needed
- Log token usage for cost tracking

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Components to Test:**
- Toggl API client (with mocked responses)
- Entity parser (various description formats)
- Database operations (CRUD operations)
- LLM client (with mocked responses)
- Report generator (output formatting)

### 7.2 Integration Tests

**Scenarios to Test:**
- End-to-end flow with test data
- Pagination with large datasets
- Rate limit handling
- Database synchronization across multiple runs
- Cache usage mode

### 7.3 Test Data

**Sample Time Entries:**
```json
[
  {
    "id": 1001,
    "user_id": 123,
    "username": "John Doe",
    "user_email": "john@example.com",
    "description": "Fixed authentication bug #2034 [Backend] [Bug] [AuthService]",
    "start": "2025-09-23T09:00:00Z",
    "stop": "2025-09-23T11:30:00Z",
    "duration": 9000
  },
  {
    "id": 1002,
    "user_id": 123,
    "username": "John Doe",
    "user_email": "john@example.com",
    "description": "Team standup meeting",
    "start": "2025-09-23T10:00:00Z",
    "stop": "2025-09-23T10:15:00Z",
    "duration": 900
  }
]
```

---

## 8. Glossary

| Term | Definition |
|------|------------|
| **Toggl** | Time tracking software used by the team |
| **Fibery.io** | Project management and knowledge base platform |
| **Entity** | A work item in Fibery.io (e.g., task, bug, feature) |
| **Time Entry** | A record of time spent on an activity in Toggl |
| **Run** | A single execution of the report generation script |
| **Matched Entry** | Time entry successfully parsed to extract Fibery.io entity |
| **Unmatched Entry** | Time entry without recognizable Fibery.io metadata |
| **LLM** | Large Language Model (e.g., GPT-4) |
| **API Token** | Authentication credential for API access |
| **Workspace** | Toggl organizational container for time entries |

---

## 9. References

### Documentation
1. **Toggl API Documentation**
   - Detailed Reports: https://engineering.toggl.com/docs/reports/detailed_reports/
   - Authentication: https://engineering.toggl.com/docs/authentication/
   - Rate Limits: https://support.toggl.com/en/articles/11484112-api-webhook-limits

2. **OpenAI API Documentation**
   - Chat Completions: https://platform.openai.com/docs/api-reference/chat
   - Best Practices: https://platform.openai.com/docs/guides/prompt-engineering
   - Pricing: https://openai.com/pricing

3. **Python Libraries**
   - Requests: https://docs.python-requests.org/
   - Click: https://click.palletsprojects.com/
   - python-dotenv: https://pypi.org/project/python-dotenv/
   - sqlite3: https://docs.python.org/3/library/sqlite3.html

### Related Resources
- Fibery.io API: https://api.fibery.io/
- UV Package Manager: https://github.com/astral-sh/uv
- SQLite Documentation: https://www.sqlite.org/docs.html

---

## 10. Appendices

### Appendix A: Sample Entity Parsing Test Cases

```python
test_cases = [
    {
        "input": "Fixed bug #1234 [Backend] [Bug] [AuthService]",
        "expected": {
            "description": "Fixed bug",
            "entity_id": "1234",
            "database": "Backend",
            "type": "Bug",
            "project": "AuthService",
            "is_matched": True
        }
    },
    {
        "input": "Team meeting",
        "expected": {
            "description": "Team meeting",
            "entity_id": None,
            "database": None,
            "type": None,
            "project": None,
            "is_matched": False
        }
    },
    {
        "input": "Research #5678",
        "expected": {
            "description": "Research",
            "entity_id": "5678",
            "database": None,
            "type": None,
            "project": None,
            "is_matched": True
        }
    },
    {
        "input": "? Нет полей Stage, Next action, Owner, Alternate names #1112 [Scrum] [Sub-bug] [Moneyball]",
        "expected": {
            "description": "? Нет полей Stage, Next action, Owner, Alternate names",
            "entity_id": "1112",
            "database": "Scrum",
            "type": "Sub-bug",
            "project": "Moneyball",
            "is_matched": True
        }
    }
]
```

### Appendix B: Sample LLM Prompts

See sections 3.5 for detailed prompt templates.

### Appendix C: Database Indexes

```sql
-- Indexes for performance optimization
CREATE INDEX idx_toggl_time_entries_run_id ON toggl_time_entries(run_id);
CREATE INDEX idx_toggl_time_entries_toggl_id ON toggl_time_entries(toggl_id);
CREATE INDEX idx_toggl_time_entries_user_email ON toggl_time_entries(user_email);
CREATE INDEX idx_toggl_time_entries_start_time ON toggl_time_entries(start_time);
CREATE INDEX idx_processed_time_entries_run_id ON processed_time_entries(run_id);
CREATE INDEX idx_processed_time_entries_user_email ON processed_time_entries(user_email);
CREATE INDEX idx_processed_time_entries_entity_id ON processed_time_entries(entity_id);
CREATE INDEX idx_processed_time_entries_project ON processed_time_entries(project);
CREATE INDEX idx_processed_time_entries_is_matched ON processed_time_entries(is_matched);
```

### Appendix D: Example CLI Help Output

```
Usage: generate_report.py [OPTIONS]

  Generate team activity reports from Toggl time tracking data.

Options:
  --start-date TEXT       Start date (YYYY-MM-DD)  [required]
  --end-date TEXT         End date (YYYY-MM-DD)  [required]
  --users TEXT            Comma-separated user emails (optional, defaults to all)
  --use-cache             Use cached data instead of fetching from Toggl
  --config PATH           Path to config file  [default: config/config.yaml]
  --output-dir PATH       Output directory  [default: ./tmp]
  --log-level TEXT        Logging level  [default: INFO]
  --help                  Show this message and exit.

Examples:
  # Generate weekly report for all users
  python generate_report.py \
    --start-date 2025-09-23 \
    --end-date 2025-09-29

  # Generate report for specific users
  python generate_report.py \
    --start-date 2025-09-23 \
    --end-date 2025-09-29 \
    --users john@example.com,jane@example.com

  # Use cached data for development
  python generate_report.py \
    --start-date 2025-09-23 \
    --end-date 2025-09-29 \
    --use-cache
```

---

**End of Document**

