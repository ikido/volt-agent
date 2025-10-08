# PRD: Fibery Entity Context Integration - Configuration

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** 📝 Planning  

> **📚 Part of:** [Fibery Entity Context Integration](./README.md)  
> **Related Docs:** [Core Requirements](./PRD_Core.md) | [Database Schema](./PRD_Database_Schema.md)

---

## Overview

This document defines all configuration files, prompts, and environment variables required for the Fibery Entity Context Integration feature.

---

## 1. Configuration File Structure

### config/config.yaml

```yaml
# config/config.yaml

# ... existing toggl and openai config ...

# Fibery Configuration
fibery:
  api_base_url: "https://{workspace}.fibery.io"
  use_graphql: true  # Use GraphQL API (recommended over REST)
  timeout_seconds: 30
  max_retries: 3
  retry_backoff_factor: 2.0
  
  # Enrichment features
  enrichment:
    enabled: false  # Enable with --enrich-fibery flag
    batch_size: 10  # Fetch entities in batches
    max_concurrent_requests: 5
    
  # Analysis features
  analysis:
    enabled: false  # Enable with --fibery-analysis flag
    check_open_entities: true
    check_discrepancies: true
    
  # Entity type configuration
  # Each entity type has its own field mappings and context logic
  entity_types:
    - storage_type: "Scrum/Task"      # Schema name (REST API)
      graphql_type: "Task"             # GraphQL type name
      query_function: "findTasks"      # GraphQL query function
      database: "Scrum"                # Database/space name
      display_name: "Task"
      fields:
        name: "name"                   # Note: camelCase in GraphQL
        description: "description"
        state: "state { name }"
        completion_date: "completionDate"
        started_date: "startedDate"
        planned_end: "plannedEnd"
        planned_start: "plannedStart"
        feature: "feature { publicId name }"
        assigned_user: "assignedUser { name email }"
      prompt_template: "task"  # Loads from ./config/prompts/task.txt
    
    - storage_type: "Scrum/Bug"
      graphql_type: "Bug"
      query_function: "findBugs"
      database: "Scrum"
      display_name: "Bug"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        completion_date: "completionDate"
        started_date: "startedDate"
        severity: "severity { name }"
        feature: "feature { publicId name }"
        assigned_user: "assignedUser { name email }"
      prompt_template: "bug"  # Loads from ./config/prompts/bug.txt
    
    - storage_type: "Scrum/Sub-bug"
      graphql_type: "SubBug"
      query_function: "findSubBugs"
      database: "Scrum"
      display_name: "Sub-bug"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        # Nested relationships: Sub-bug → Bug → Feature
        # NOTE: Field name is just "bug" (or "Scrum/Bug" in REST API)
        bug: "bug { publicId name feature { publicId name } }"
      prompt_template: "bug"  # Reuses bug.txt
    
    - storage_type: "Scrum/Feature"
      graphql_type: "Feature"
      query_function: "findFeatures"
      database: "Scrum"
      display_name: "Feature"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        actual_release_date: "actualReleaseDate"
        planned_release_date: "plannedReleaseDate"
        tasks: "tasks { publicId name state { name } }"
        bugs: "bugs { publicId name state { name } }"
      prompt_template: "feature"  # Loads from ./config/prompts/feature.txt
    
    - storage_type: "Scrum/Build"
      graphql_type: "Build"
      query_function: "findBuilds"
      database: "Scrum"
      display_name: "Build"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        deployment_date: "deploymentDate"
        features: "features { publicId name }"
        bugs: "bugs { publicId name }"
      prompt_template: "build"  # Loads from ./config/prompts/build.txt
    
    - storage_type: "Scrum/Release"
      graphql_type: "Release"
      query_function: "findReleases"
      database: "Scrum"
      display_name: "Release"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        release_date: "releaseDate"
        features: "features { publicId name state { name } }"
      prompt_template: "build"  # Reuses build.txt
    
    - storage_type: "Scrum/Hotfix"
      graphql_type: "Hotfix"
      query_function: "findHotfixes"
      database: "Scrum"
      display_name: "Hotfix"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        urgency: "urgency { name }"
        deployment_date: "deploymentDate"
        bugs: "bugs { publicId name }"
      prompt_template: "hotfix"  # Loads from ./config/prompts/hotfix.txt
    
    - storage_type: "Scrum/Sub-task"
      graphql_type: "SubTask"
      query_function: "findSubTasks"
      database: "Scrum"
      display_name: "Sub-task"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        completion_date: "completionDate"
        started_date: "startedDate"
        # Nested relationships: Sub-task → Task → Feature
        # NOTE: Field name is just "task" (or "Scrum/Task" in REST API)
        task: "task { publicId name feature { publicId name } }"
      prompt_template: "task"  # Reuses task.txt
    
    - storage_type: "Scrum/Chore"
      graphql_type: "Chore"
      query_function: "findChores"
      database: "Scrum"
      display_name: "Chore"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        completion_date: "completionDate"
        started_date: "startedDate"
        priority: "priority { name }"
      prompt_template: "chore"  # Loads from ./config/prompts/chore.txt
    
    - storage_type: "Scrum/Epic"
      graphql_type: "Epic"
      query_function: "findEpics"
      database: "Scrum"
      display_name: "Epic"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        features: "features { publicId name state { name } }"
        planned_end: "plannedEnd"
      prompt_template: "epic"  # Loads from ./config/prompts/epic.txt
    
    - storage_type: "Scrum/Sprint"
      graphql_type: "Sprint"
      query_function: "findSprints"
      database: "Scrum"
      display_name: "Sprint"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        start_date: "startDate"
        end_date: "endDate"
      prompt_template: "sprint"  # Loads from ./config/prompts/sprint.txt
    
    - storage_type: "Design/Design Feature"
      graphql_type: "DesignFeature"
      query_function: "findDesignFeatures"
      database: "Design"
      display_name: "Design Feature"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        planned_end: "plannedEnd"
        work_versions: "workVersions { publicId name }"
        # NOTE: "Scrum/Features" (plural) in REST API becomes "scrumFeatures"
        scrum_features: "scrumFeatures(limit: 1) { publicId name }"
      prompt_template: "design_feature"  # Loads from ./config/prompts/design_feature.txt
    
    - storage_type: "Design/Work Version"
      graphql_type: "WorkVersion"
      query_function: "findWorkVersions"
      database: "Design"
      display_name: "Design Work Version"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        # Nested relationships: Work Version → Design Feature → Scrum Features (first one)
        # NOTE: Field name is "designFeature" (from "Design/Design Feature" in REST)
        # designFeature.scrumFeatures is a collection, we fetch first with limit
        design_feature: "designFeature { publicId name scrumFeatures(limit: 1) { publicId name } }"
        review_outcome: "reviewOutcome { name }"
      prompt_template: "work_version"  # Loads from ./config/prompts/work_version.txt
  
  # Schema discovery and validation
  schema:
    auto_discover: true
    validate_on_start: true
    warn_on_unknown_types: true
    cache_schema: true
    cache_ttl_hours: 24
    
  # Caching
  cache:
    enabled: true
    schema_ttl_hours: 24
    entity_ttl_hours: 1
    user_ttl_hours: 24
    cache_path: "./data/fibery_cache/"
    force_refresh: false  # Set to true to bypass cache

# Database Configuration (extended)
database:
  path: "./data/toggl_cache.db"
  backup_enabled: true
  backup_path: "./data/backups/"
  # Fibery tables will be added to existing database

# Output Configuration (extended)
output:
  directory: "./tmp"
  log_level: "INFO"
  create_subfolders: true  # Create per-user subfolders
  save_raw_data: true  # Save raw Fibery responses
  save_intermediate_summaries: true
  include_fibery_context: true  # Include in reports when --enrich-fibery used
```

---

## 2. Prompts Configuration

### Directory Structure

Prompts are stored as individual text files in `./config/prompts/` for easy editing:

```
./config/prompts/
├── default.txt                    # Default prompt for unknown entity types
├── task.txt                       # Task-specific prompt
├── bug.txt                        # Bug-specific prompt
├── feature.txt                    # Feature-specific prompt
├── build.txt                      # Build/Release-specific prompt
├── hotfix.txt                     # Hotfix-specific prompt
├── subtask.txt                    # Sub-task-specific prompt
├── chore.txt                      # Chore-specific prompt
├── epic.txt                       # Epic-specific prompt
├── sprint.txt                     # Sprint-specific prompt
├── design_feature.txt             # Design Feature-specific prompt
├── work_version.txt               # Work Version-specific prompt
├── generic.txt                    # Generic fallback prompt
├── enriched_report.txt            # Individual report generation
└── team_summary.txt               # Team summary generation
```

### Prompt File Format

Each prompt file is plain text with `{entity_json}` placeholder for data injection.

**Loading Mechanism:**
- The system reads the prompt template name from `config.yaml` (e.g., `"task"`)
- Appends `.txt` extension and loads from `./config/prompts/task.txt`
- Replaces `{entity_json}` with actual entity data
- Sends complete prompt to OpenAI API

**Benefits of File-Based Prompts:**
- ✅ Easy to edit without YAML escaping issues
- ✅ Can use any text editor
- ✅ Better version control diffs
- ✅ Can reuse prompts across entity types (e.g., `bug.txt` for both Bug and Sub-bug)
- ✅ Simple to add new entity types

**Handling Nested Context in Prompts:**

When entity data includes nested relationships (e.g., Sub-task with parent Task and Feature), the prompt should instruct the LLM to extract and present the full context chain:

```
Your task: Create a summary that:
1. Describes the immediate work (what this sub-task does)
2. Shows the context chain (parent task → feature)
3. Explains why this matters in the bigger picture

Entity Data (includes nested parentTask.feature):
{entity_json}
```

The LLM will receive the complete nested JSON and can extract the full hierarchy to provide meaningful context.

---

## 2.1 Entity Summarization Prompts

### `config/prompts/default.txt`

Default prompt for unknown entity types:

```
You are analyzing a Fibery entity to provide context for a time tracking report.

Below is the raw entity data from Fibery including descriptions, comments, and related entities.

Your task: Create a concise 2-3 paragraph summary that answers:
1. What is this entity about? (main purpose/goal)
2. What work was done? (based on description and comments)
3. What is it connected to? (related features, bugs, user requests)
4. What is the current status?

Format your response in markdown with clear sections:
- **Overview**: 1-2 sentences about what this is
- **Work Details**: What was accomplished
- **Context**: Related entities and connections
- **Status**: Current state and timeline

Keep it CONCISE and FACTUAL. No speculation.

Entity Data:
{entity_json}

Generate the summary now:
```

---

### `config/prompts/task.txt`

Task-specific prompt:

```
You are summarizing a Task entity from Fibery for a time tracking report.

Task data includes: name, description, comments, related features, assigned user, and timeline.

Your task: Create a 2-3 paragraph summary focusing on:
1. What is the task trying to accomplish?
2. What specific work was done? (from description and comments)
3. How does it connect to broader features/initiatives?
4. Current status and completion timeline

Format your response:
**What was worked on:**
[1-2 sentence overview]

**Technical details:**
- Key accomplishment 1
- Key accomplishment 2
- Key accomplishment 3

**Context:**
- Part of Feature #XXX: [Feature name]
- [Other relevant context]

**Status:** [Current state and dates]

Keep it concise and factual. Use bullet points for key details.

Task Data:
{entity_json}

Generate the summary:
```

---

### `config/prompts/bug.txt`

Bug-specific prompt:

```
You are summarizing a Bug entity from Fibery for a time tracking report.

Bug data includes: name, description, reproduction steps, comments, related features, severity.

Your task: Create a concise summary covering:
1. What is the bug? (issue description)
2. What was done to fix it? (from comments and description)
3. What feature/component does it affect?
4. Resolution status and severity

Format your response:
**Issue:**
[1-2 sentence description of the bug]

**Resolution:**
- What was fixed
- How it was fixed

**Impact:**
- Severity: [High/Medium/Low]
- Affects: Feature #XXX

**Status:** [Current state]

Focus on the problem and solution. Keep it brief.

Bug Data:
{entity_json}

Generate the summary:
```

---

### Additional Entity-Specific Prompts

The following prompts follow similar patterns and are stored in their respective files:

- **`feature.txt`** - Focuses on business value, progress tracking, and delivery timeline
- **`build.txt`** - Emphasizes deployment readiness, included features/bugs, and testing status
- **`hotfix.txt`** - Highlights urgency, impact, and rapid deployment needs
- **`chore.txt`** - Describes operational/maintenance value and priority
- **`epic.txt`** - Strategic overview, related features, and overall progress
- **`sprint.txt`** - Sprint goals, duration, and work completed
- **`design_feature.txt`** - Design requirements, work versions, and connection to development
- **`work_version.txt`** - Design iteration details, review outcome, and approval status

### `config/prompts/generic.txt`

Generic fallback for unknown entity types:

```
Summarize this Fibery entity for a time tracking report.

Focus on:
- What is it?
- What work was done?
- Timeline and status
- Related entities

Keep it to 1-2 paragraphs, factual only.

Entity Data:
{entity_json}

Generate the summary:
```

---

## 2.2 Combined Report Prompts

### `config/prompts/enriched_report.txt`

Prompt for generating enriched individual reports:

```
You are creating an enhanced activity report for a team member that now includes rich context from Fibery.

You have:
1. Toggl time entries (what they logged)
2. Fibery entity summaries (detailed context about what they worked on)
3. Work alignment analysis (discrepancies between systems)

Your task: Create a comprehensive report that:
1. Summarizes what the person worked on (using Fibery context)
2. Highlights key accomplishments and deliverables
3. Notes any work alignment issues
4. Provides context about how work connects to larger initiatives

Structure:
- Executive summary (2-3 sentences)
- Key deliverables (bullet points)
- Detailed entity breakdown (use provided summaries)
- Work alignment notes (if issues exist)

Keep the executive summary concise but ensure all major activities are captured.

Data:
{enriched_data}

Generate the report:
```

---

### `config/prompts/team_summary.txt`

Prompt for team summary with Fibery context:

```
You are creating an enhanced team activity report that includes rich context from Fibery.

You have:
1. Individual reports with Fibery context for each team member
2. Work alignment analysis for the team
3. Entity type coverage information
4. Schema change detection results

Your task: Create a comprehensive team report that:
1. Summarizes team-wide activities and accomplishments
2. Identifies major projects and initiatives worked on
3. Highlights work alignment issues that need attention
4. Provides recommendations for configuration improvements

Structure:
- Executive summary
- Team statistics
- Major projects (group related entities)
- Work alignment summary
- Configuration & coverage report
- Recommendations

Focus on actionable insights and team-level patterns.

Data:
{team_data}

Generate the report:
```

---

## 3. Environment Variables

### .env

```bash
# .env file

# ============================================================================
# EXISTING CREDENTIALS
# ============================================================================

# Toggl API
TOGGL_API_TOKEN=your_toggl_token_here
TOGGL_WORKSPACE_ID=your_workspace_id

# OpenAI API
OPENAI_API_KEY=your_openai_key_here

# ============================================================================
# NEW: FIBERY CREDENTIALS
# ============================================================================

# Fibery API Token
# Generate at: https://wearevolt.fibery.io/settings/api-tokens
FIBERY_API_TOKEN=your_fibery_api_token_here

# Fibery Workspace Name
# The subdomain of your Fibery workspace (e.g., "wearevolt" from "wearevolt.fibery.io")
FIBERY_WORKSPACE_NAME=wearevolt
```

### Obtaining Fibery API Token

1. Log in to Fibery: https://wearevolt.fibery.io
2. Go to Settings → API Tokens
3. Create new token with **read-only** permissions
4. Copy token to `.env` file
5. **Never commit `.env` to version control**

---

## 4. Entity Type Configuration Guide

### Adding a New Entity Type

When you encounter a new entity type that needs to be configured:

**Step 1: Discover the entity structure**

Use the Fibery API to fetch a sample entity and understand its fields:

```graphql
query getSample($searchId: String) {
  findQATasks(publicId: {is: $searchId}) {
    id
    publicId
    name
    description
    state { name }
    # Add other fields as discovered
  }
}
```

**Step 2: Add to config.yaml**

```yaml
- storage_type: "Scrum/QA-Task"
  graphql_type: "QATask"
  query_function: "findQATasks"
  database: "Scrum"
  display_name: "QA Task"
  fields:
    name: "name"
    description: "description"
    state: "state { name }"
    # Add relevant fields
  prompt_template: "qa_task"  # Loads from ./config/prompts/qa_task.txt
```

**Step 3: Create specialized prompt (optional)**

If the entity type needs specific handling, create a custom prompt file `./config/prompts/qa_task.txt`:

```
You are summarizing a QA Task entity from Fibery for a time tracking report.

Focus on:
- What is being tested
- Test results and findings
- Related features or bugs
- QA timeline and status

QA Task Data:
{entity_json}

Generate the summary:
```

**Step 4: Test the configuration**

Run a report with the new entity type:

```bash
python generate_report.py \
  --start-date 2025-10-01 \
  --end-date 2025-10-07 \
  --enrich-fibery
```

### Field Mapping Best Practices

**Standard fields to include:**
- `name`: Entity display name
- `description`: Main description (rich text)
- `state`: Current workflow state
- `completion_date`: When completed
- `started_date`: When started

**Entity-specific fields:**
- **Tasks**: `feature`, `assigned_user`, `planned_end`
- **Bugs**: `severity`, `feature`, `parent_bug`
- **Features**: `tasks`, `bugs`, `release_date`
- **Builds**: `deployment_date`, `features`, `bugs`

**Relationship fields:**
Always include relationships to parent/related entities:
```yaml
feature: "feature { publicId name }"
bugs: "bugs { publicId name state { name } }"
```

### Discovering Actual Field Names

**IMPORTANT:** Don't assume field names - verify them in the actual Fibery schema!

**How to find relationship field names:**

1. **Check the workspace structure documentation:**
   - See `/docs/features/2-fibery-reports/workspace-structure/entity_types.json`
   - Find your entity type (e.g., "Scrum/Sub-task")
   - Look at the fields list

2. **Field naming patterns:**
   - REST API: `"Scrum/Task"` (full path with slash)
   - GraphQL: `"task"` (camelCase, short form)
   - Collections: May be plural (e.g., `"scrumFeatures"`)

3. **Example - Scrum/Sub-task:**
   ```json
   {
     "name": "Scrum/Sub-task",
     "fields": [
       "Scrum/Task",      // ← Relationship to parent task
       "Scrum/Bug",       // ← Also can relate to bugs
       "Scrum/name",
       ...
     ]
   }
   ```
   - In GraphQL, `"Scrum/Task"` becomes `"task"`

4. **Verify in GraphQL playground:**
   - Go to: `https://wearevolt.fibery.io/api/graphql/space/Scrum`
   - Run introspection or test queries
   - Check actual field names returned

### Nested Relationships

**Problem:** Some entities only make sense in the context of their parents.

**Example:** A Sub-task by itself doesn't provide enough context. You need:
1. **Sub-task** - The immediate work
2. **Parent Task** - What task this is part of
3. **Feature** - The bigger picture

**Solution:** Fetch nested relationships in GraphQL (using correct field names):

```yaml
# Sub-task configuration with nested context
- storage_type: "Scrum/Sub-task"
  fields:
    name: "name"
    description: "description"
    # Fetch nested: Sub-task → Task → Feature
    # IMPORTANT: Use actual field names from schema
    task: "task {              # Not 'parentTask' - verify in schema!
      publicId 
      name 
      feature { 
        publicId 
        name 
      } 
    }"
```

**Corresponding GraphQL Query:**

```graphql
query getSubTask($searchId: String) {
  findSubTasks(publicId: {is: $searchId}) {
    id
    publicId
    name
    description
    state { name }
    completedDate        # Note: actual field name from schema
    startedDate
    task {               # Not 'parentTask'!
      publicId
      name
      feature {
        publicId
        name
      }
    }
  }
}
```

**Result includes full context:**

```json
{
  "id": "...",
  "publicId": "9234",
  "name": "Update user authentication logic",
  "task": {              // Actual field name
    "publicId": "7658",
    "name": "Implement user management system",
    "feature": {
      "publicId": "1575",
      "name": "User Authentication & Authorization"
    }
  }
}
```

**In the report, this becomes:**

```markdown
### #9234: Update user authentication logic
**Type:** Sub-task | **Status:** Done

**What was worked on:**
Updated user authentication logic as part of the user management system implementation.

**Context:**
- Sub-task of Task #7658: Implement user management system
- Part of Feature #1575: User Authentication & Authorization
- This is a specific component of a larger authentication overhaul
```

**Other nested entity patterns:**

| Entity Type | Nesting Pattern | Why It Matters |
|-------------|----------------|----------------|
| Sub-task | Sub-task → Task → Feature | Understand which feature this small piece supports |
| Sub-bug | Sub-bug → Bug → Feature | See what feature the bug fix affects |
| Work Version | Work Version → Design Feature → Scrum Feature | Connect design iterations to development |
| Task | Task → Feature → Epic | See strategic context (optional, for high-level view) |

**Best Practices:**

1. **Limit nesting depth**: Go 2-3 levels max to avoid query complexity
2. **Fetch minimal fields**: Only get `publicId` and `name` for nested entities
3. **Use consistently**: Apply same pattern to similar entity types
4. **Document intent**: Add comments explaining the nesting in config

---

## 5. Configuration Validation

### Automatic Validation

The system validates configuration on startup:

**Checks performed:**
1. All configured entity types exist in workspace
2. All configured fields exist in entity types
3. GraphQL query functions are correct
4. Prompt templates exist in prompts.yaml

**Validation output:**
```
✓ Configuration validation passed
  - 7 entity types validated
  - All fields exist
  - All prompts found

⚠ Warnings:
  - Entity type "Scrum/QA-Task" exists in workspace but not configured
  - Consider adding to config.yaml
```

### Manual Validation

Check configuration health:

```bash
python generate_report.py --validate-config
```

---

## 6. Cache Configuration

### Cache Behavior

**Schema Cache** (24 hours):
- Stores Fibery workspace schema
- Reduces API calls for schema queries
- Updated automatically when expired

**Entity Cache** (1 hour):
- Stores fetched entity data
- Short TTL because entities change frequently
- Keyed by entity ID and last update time

**User Cache** (24 hours):
- Stores Fibery user list
- Used for user matching
- Infrequently changes

**Summary Cache** (indefinite):
- Stores LLM-generated summaries
- Keyed by entity ID + entity update timestamp
- Reused if entity hasn't changed

### Cache Location

```
./data/fibery_cache/
├── schema_cache.json
├── entities/
│   ├── 7658_20251007.json
│   ├── 7521_20251007.json
│   └── ...
└── users_cache.json
```

### Force Cache Refresh

```yaml
fibery:
  cache:
    force_refresh: true  # Bypass all caches
```

Or via CLI:
```bash
python generate_report.py --force-refresh-fibery
```

---

## 7. Logging Configuration

### Log Levels

```yaml
output:
  log_level: "INFO"  # DEBUG | INFO | WARNING | ERROR
```

**DEBUG**: All API calls, cache hits/misses, detailed processing  
**INFO**: Major steps, entity fetches, summary generation  
**WARNING**: Unknown entity types, missing fields, validation issues  
**ERROR**: API failures, configuration errors, critical issues  

### Log Output

```
./tmp/run_2025-10-07-14-30/
├── run_log.log                    # Main log
├── fibery_api_calls.log          # API call details
└── enrichment_pipeline.log       # Enrichment process
```

---

## 8. Example Configurations

### Minimal Configuration

For basic enrichment without customization:

```yaml
fibery:
  api_base_url: "https://wearevolt.fibery.io"
  use_graphql: true
  entity_types:
    - storage_type: "Scrum/Task"
      graphql_type: "Task"
      query_function: "findTasks"
      database: "Scrum"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
      prompt_template: "fibery_entity_summary_prompt_default"
```

### Full-Featured Configuration

For complete coverage with all features:

See section 1 above for the complete configuration.

---

## Related Documentation

- **[PRD_Core.md](./PRD_Core.md)** - Core requirements and functional specs
- **[PRD_Database_Schema.md](./PRD_Database_Schema.md)** - Database tables
- **[PRD_Schema_Management.md](./PRD_Schema_Management.md)** - Handling unknown types
- **[Fibery API Integration Guide](../Fibery_API_Integration_Guide.md)** - API details

---

**End of Configuration Document**

