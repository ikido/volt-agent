# Fibery Entity Context Integration

**Status:** ✅ Implementation Complete  
**Version:** 1.0  
**Date:** October 8, 2025

---

## Overview

This document describes the Fibery Entity Context Integration feature that enriches Toggl time tracking reports with detailed contextual information from Fibery.io entities.

### What's New

- **🔗 Entity Enrichment**: Fetch detailed information from Fibery for each entity logged in Toggl
- **🤖 AI Summarization**: Generate entity-type-specific summaries using OpenAI
- **📊 Enhanced Reports**: Person-by-person reports with full entity context
- **💾 Smart Caching**: Database caching for Fibery entities and summaries
- **🎯 Type-Aware**: Different context extraction for Tasks, Bugs, Features, Builds, etc.

---

## Quick Start

### 1. Setup Environment Variables

Add Fibery credentials to your `.env` file:

```bash
# Existing credentials
TOGGL_API_TOKEN=your_toggl_token
TOGGL_WORKSPACE_ID=your_workspace_id
OPENAI_API_KEY=your_openai_key

# NEW: Fibery credentials
FIBERY_API_TOKEN=your_fibery_api_token_here
FIBERY_WORKSPACE_NAME=wearevolt
```

### 2. Generate Report with Enrichment

```bash
# Basic report with Fibery enrichment
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery

# Skip summarization (faster, no OpenAI costs)
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery \
  --skip-summarization

# Use cached data (development mode)
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery \
  --use-cache
```

---

## Architecture

### Components

```
src/
├── fibery/
│   ├── client.py           # Fibery API client (GraphQL + REST)
│   ├── models.py           # Data models for entities and users
│   └── entity_fetcher.py   # Entity fetching with type-specific queries
├── llm/
│   └── summarizer.py       # LLM-based entity summarization
├── enrichment/
│   └── pipeline.py         # Main enrichment orchestrator
└── reporting/
    └── generator.py        # Enhanced report generation (extended)
```

### Database Schema

Two new tables added to `toggl_cache.db`:

```sql
-- Cache for Fibery entities
CREATE TABLE fibery_entities (
    id INTEGER PRIMARY KEY,
    fibery_id TEXT UNIQUE,      -- UUID from Fibery
    public_id TEXT,             -- Public ID like "7658"
    entity_type TEXT,           -- e.g., "Scrum/Task"
    entity_name TEXT,
    description_md TEXT,
    comments TEXT,              -- JSONB nested tree
    metadata TEXT,              -- JSONB flexible storage
    summary_md TEXT,            -- AI-generated summary (cached)
    fetched_at DATETIME,
    updated_at DATETIME
);

-- Cache for Fibery users
CREATE TABLE fibery_users (
    id INTEGER PRIMARY KEY,
    fibery_id TEXT UNIQUE,
    email TEXT UNIQUE,
    name TEXT,
    role TEXT,
    is_active BOOLEAN,
    fetched_at DATETIME,
    updated_at DATETIME
);
```

---

## Configuration

### Entity Type Configuration

Entity types are configured in `config/config.yaml`:

```yaml
fibery:
  api_base_url: "https://wearevolt.fibery.io"
  use_graphql: true
  
  entity_types:
    - storage_type: "Scrum/Task"
      graphql_type: "Task"
      query_function: "findTasks"
      database: "Scrum"
      display_name: "Task"
      fields:
        name: "name"
        description: "description"
        state: "state { name }"
        feature: "feature { publicId name }"
      prompt_template: "task"
```

**Currently Configured Types:**
- Scrum/Task
- Scrum/Bug
- Scrum/Sub-bug
- Scrum/Feature
- Scrum/Build
- Scrum/Sub-task
- Scrum/Chore

### Prompt Templates

Entity-type-specific prompts stored in `config/prompts/`:

- `task.txt` - Task-specific summarization
- `bug.txt` - Bug-specific summarization
- `feature.txt` - Feature-specific summarization
- `build.txt` - Build/Release-specific summarization
- `chore.txt` - Chore-specific summarization
- `generic.txt` - Fallback for unknown types

**Prompt Format:**
```
You are summarizing a Task entity from Fibery for a time tracking report.

Your task: Create a 2-3 paragraph summary focusing on:
1. What is the task trying to accomplish?
2. What specific work was done?
3. How does it connect to broader features?
4. Current status and timeline

Task Data:
{entity_json}

Generate the summary:
```

---

## CLI Flags

### `--enrich-fibery`

Enable Fibery entity enrichment. Fetches entity details and generates summaries.

```bash
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery
```

### `--skip-summarization`

Skip LLM summarization (development mode). Faster and no OpenAI costs.

```bash
python generate_report.py \
  --start-date 2025-09-23 \
  --end-date 2025-09-29 \
  --enrich-fibery \
  --skip-summarization
```

### `--fibery-analysis`

Enable work alignment analysis (planned for future implementation).

---

## Report Format

### Standard Report (Without Enrichment)

```markdown
# Individual Activity Report: user@example.com

## Work on Project Entities

- **#7658 [Scrum] [Task] [Volt - Internal]**: One short sentence. (17.7 hours)
```

### Enriched Report (With Fibery Enrichment)

```markdown
# Individual Activity Report: user@example.com
**Report Type:** Enriched with Fibery Context

## Work on Project Entities

### #7658: Provision AWS Infrastructure in Huber AWS Org ID
**Time:** 17.7 hours | **Type:** Scrum/Task

**What was worked on:**
Provisioned complete AWS infrastructure in Huber AWS Organization including VPC setup, 
subnet configuration, security groups, and IAM roles for production environment.

**Technical details:**
- Designed VPC architecture with multi-AZ support
- Configured security groups and network ACLs
- Set up IAM roles and policies

**Context:**
- Part of Feature #1575: Create AWS Infrastructure for Huber

**Status:** Done (Completed: 2025-10-05)

---
```

---

## Workflow

### 1. Initialize Components

```python
# Initialize Fibery client
fibery_client = FiberyClient(
    api_token=os.getenv('FIBERY_API_TOKEN'),
    workspace_name=os.getenv('FIBERY_WORKSPACE_NAME')
)

# Initialize entity fetcher
entity_fetcher = EntityFetcher(
    client=fibery_client,
    entity_type_configs=config['fibery']['entity_types']
)

# Initialize summarizer
summarizer = EntitySummarizer(
    llm_client=llm,
    entity_type_configs=config['fibery']['entity_types']
)

# Initialize pipeline
enrichment_pipeline = EnrichmentPipeline(
    db=db,
    fibery_client=fibery_client,
    entity_fetcher=entity_fetcher,
    summarizer=summarizer
)
```

### 2. Fetch and Cache Users

```python
user_count = enrichment_pipeline.fetch_and_cache_users()
```

### 3. Enrich Entities

```python
entities_to_enrich = [
    {'entity_id': '7658', 'entity_type': 'Scrum/Task'},
    {'entity_id': '7521', 'entity_type': 'Scrum/Bug'}
]

enriched = enrichment_pipeline.enrich_entities_batch(
    entities_to_enrich,
    use_cache=True
)
```

### 4. Generate Reports

```python
report = report_gen.generate_individual_report(
    user_email=user_email,
    matched_entries=matched,
    enriched_entities=enriched
)
```

---

## Caching Strategy

### Entity Cache

- **TTL**: 1 hour (entities may update frequently)
- **Key**: `public_id` (e.g., "7658")
- **Use `--use-cache` flag**: Skip API calls and use cached data

### Summary Cache

- **TTL**: Indefinite (keyed by entity + updated_at)
- **Regeneration**: Only when entity data changes
- **Storage**: Directly in `fibery_entities.summary_md` column

### User Cache

- **TTL**: 24 hours
- **Refresh**: Automatic on each run (unless using `--use-cache`)

---

## Performance

### Metrics (Typical Report)

- **Entity Fetch**: ~2 seconds per entity (cached: instant)
- **LLM Summary**: ~5 seconds per entity
- **Total Overhead**: ~3 minutes for 50 entities (first run)
- **Cached Run**: ~10 seconds (using `--use-cache`)

### Optimization Tips

1. **Development**: Use `--use-cache` and `--skip-summarization`
2. **First Run**: Expect longer time for initial data fetch
3. **Subsequent Runs**: Much faster with cached entities
4. **Large Teams**: Consider processing in batches

---

## Troubleshooting

### Missing Fibery Credentials

**Error:**
```
ValueError: Fibery enrichment enabled but FIBERY_API_TOKEN not set
```

**Solution:**
Add `FIBERY_API_TOKEN` and `FIBERY_WORKSPACE_NAME` to `.env` file.

### Entity Not Found

**Symptom:** Entity in Toggl but not enriched in report

**Possible Causes:**
1. Entity deleted in Fibery
2. Incorrect entity ID
3. Entity type not configured

**Solution:**
Check logs for specific error. Entity will appear in report with basic info.

### Unknown Entity Type

**Symptom:** Warning about unknown entity type

**Example:**
```
⚠️  Unknown Types: Scrum/QA-Task
```

**Solution:**
Add configuration for the entity type in `config/config.yaml` and create a prompt template.

---

## Future Enhancements (Not Yet Implemented)

The following features are documented in PRDs but not yet implemented:

- [ ] **Work Alignment Analysis** (`--fibery-analysis` flag)
- [ ] **Unknown Entity Detection Reports**
- [ ] **Schema Validation Reports**
- [ ] **Configuration Recommendations**
- [ ] **Nested Relationships** (Sub-task → Task → Feature)

See `docs/features/2-fibery-reports/` for detailed PRDs.

---

## Adding New Entity Types

### Step 1: Discover Entity Structure

Use Fibery GraphQL playground:
```
https://wearevolt.fibery.io/api/graphql/space/Scrum
```

### Step 2: Add to config.yaml

```yaml
- storage_type: "Scrum/NewType"
  graphql_type: "NewType"
  query_function: "findNewTypes"
  database: "Scrum"
  display_name: "New Type"
  fields:
    name: "name"
    description: "description"
    state: "state { name }"
  prompt_template: "new_type"
```

### Step 3: Create Prompt Template

Create `config/prompts/new_type.txt`:
```
You are summarizing a NewType entity from Fibery.

Focus on: [what matters for this type]

Entity Data:
{entity_json}

Generate the summary:
```

### Step 4: Test

```bash
python generate_report.py \
  --start-date 2025-10-01 \
  --end-date 2025-10-07 \
  --enrich-fibery
```

---

## API Documentation

See `docs/features/2-fibery-reports/Fibery_API_Integration_Guide.md` for complete API documentation.

---

## Related Documentation

- **[PRD_Core.md](docs/features/2-fibery-reports/PRD_Core.md)** - Core requirements
- **[PRD_Configuration.md](docs/features/2-fibery-reports/PRD_Configuration.md)** - Configuration guide
- **[PRD_Database_Schema.md](docs/features/2-fibery-reports/PRD_Database_Schema.md)** - Database design
- **[PRD_Report_Formats.md](docs/features/2-fibery-reports/PRD_Report_Formats.md)** - Report templates
- **[Fibery_API_Integration_Guide.md](docs/features/2-fibery-reports/Fibery_API_Integration_Guide.md)** - API docs

---

## Support

For issues or questions:
1. Check logs in `./tmp/toggl_report_log_*.log`
2. Review PRD documentation
3. Check database for cached data: `sqlite3 ./data/toggl_cache.db`

---

**Last Updated:** October 8, 2025

