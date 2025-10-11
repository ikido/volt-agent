# Pipeline-Based Architecture

**Version:** 2.0
**Status:** ✅ Implemented
**Architecture:** Temporal Workflow-Based with JSON Caching

---

## Overview

This architecture refactors the Toggl-Fibery analysis system from a monolithic SQLite-based approach to a robust, scalable Temporal workflow-based pipeline. The new system provides better reliability, observability, and flexibility.

## Key Features

### 🏗️ Architecture
- **Temporal Workflows**: Durable, fault-tolerant orchestration
- **JSON Storage**: Simple, debuggable file-based caching
- **Activity-Based Design**: Modular, testable components
- **Rolling Window Parallelism**: Bounded concurrency for API calls

### 🔄 Workflow Stages
1. **Toggl Collection** - Fetch and aggregate time entries
2. **Fibery Enrichment** - Enrich entities with Fibery data
3. **Report Generation** - Create individual and team reports

### 🎯 Capabilities
- ✅ Start from any stage (Toggl or Fibery)
- ✅ Re-run enrichment without re-fetching Toggl data
- ✅ Per-entity-type enrichment activities
- ✅ Configurable concurrency limits
- ✅ Real-time progress tracking
- ✅ Automatic cleanup for idempotent runs

---

## Quick Start

### 1. Start Infrastructure
```bash
# Start Temporal server
docker-compose up -d

# Start worker
python -m src.worker
```

### 2. Run Pipeline
```bash
# Full pipeline
python -m src.cli_pipeline run \
  --start-date 2025-10-07 \
  --end-date 2025-10-13

# Re-run enrichment only
python -m src.cli_pipeline run \
  --start-from fibery \
  --run-id run_2025-10-10-15-30-45
```

### 3. View Results
- **Reports**: `tmp/runs/{run_id}/reports/`
- **Data**: `tmp/runs/{run_id}/*.json`
- **Temporal UI**: http://localhost:8080

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](./PRD_Pipeline_Based_Architecture.md) | Complete product requirements and architecture design |
| [Setup Guide](./SETUP_GUIDE.md) | Step-by-step installation and usage instructions |
| [Implementation Status](./IMPLEMENTATION_STATUS.md) | Current implementation progress and component status |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              Temporal Workflow: TogglFiberyPipeline              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐            ┌────────▼────────┐
            │ TOGGL STAGE    │            │ FIBERY STAGE    │
            │ (Activities 0-3)│            │ (Activities 4-9)│
            └───────┬────────┘            └────────┬────────┘
                    │                               │
        ┌───────────┼───────────┐       ┌──────────┼──────────┐
        ▼           ▼           ▼       ▼          ▼          ▼
    Cleanup     Fetch       Aggregate   Extract  Enrich   Generate
                Data        Data        Entities Entities Reports
```

---

## Component Structure

```
src/
├── workflows/              # Temporal workflows
│   └── pipeline_workflow.py    # Main orchestrator
├── activities/             # Temporal activities
│   ├── cleanup_activities.py   # Stage cleanup
│   ├── toggl_activities.py     # Toggl operations
│   ├── fibery_activities.py    # Fibery orchestration
│   ├── reporting_activities.py # Report generation
│   └── enrichment/             # Entity enrichment
│       ├── default.py
│       ├── scrum_task.py
│       ├── scrum_bug.py
│       └── product_feature.py
├── storage/                # JSON storage layer
│   ├── schemas.py
│   └── json_storage.py
├── patterns/               # Reusable patterns
│   └── rolling_window.py
├── worker.py              # Temporal worker
└── cli_pipeline.py        # CLI interface
```

---

## Benefits Over v1.0

| Aspect | v1.0 (SQLite) | v2.0 (Temporal) |
|--------|---------------|-----------------|
| **Reliability** | Manual error handling | Automatic retries & recovery |
| **Observability** | Limited logging | Full workflow history in UI |
| **Flexibility** | All-or-nothing | Start from any stage |
| **Debuggability** | Hard to debug | Temporal UI + detailed logs |
| **Scalability** | Sequential processing | Bounded parallel processing |
| **Idempotency** | Manual cleanup | Automatic stage cleanup |
| **Data Format** | SQLite database | Human-readable JSON |

---

## Configuration

### Enrichment Configuration (`config/enrichment_config.yaml`)

Define entity-specific enrichment behavior:

```yaml
enrichment_activities:
  "Scrum/Task":
    activity: enrich_scrum_task
    max_concurrent: 5
    fields:
      - Story Points
      - Sprint
      - Epic

  "Product/Feature":
    activity: enrich_product_feature
    max_concurrent: 3
    fields:
      - Revenue Impact
      - Launch Date

  default:
    activity: default_enrich_entity
    max_concurrent: 5
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `pipeline run` | Execute the pipeline workflow |
| `pipeline list-runs` | List all runs with status |
| `pipeline show-run` | Show details of a specific run |
| `pipeline cancel-run` | Cancel a running workflow |
| `pipeline temporal-ui` | Open Temporal UI in browser |

---

## Data Flow

```
1. Toggl API
   └─> raw_toggl_data.json
       └─> aggregate_toggl_data
           └─> toggl_aggregated.json
               └─> toggl_summary.md

2. Fibery API
   └─> Extract entities from toggl_aggregated.json
       └─> Enrich via Fibery API (rolling window)
           └─> enriched_data.json
               ├─> individual/{user}.md
               └─> team_summary.md
```

---

## Error Handling

- **Activity Failures**: Logged with full context, workflow fails fast
- **Temporal Retries**: Configurable per activity (default: 1 attempt)
- **Rate Limiting**: Handled by rolling window pattern
- **Cleanup**: Idempotent stage cleanup ensures safe re-runs

---

## Performance

- **Toggl Fetching**: ~2-5 minutes (day-by-day chunking)
- **Entity Enrichment**: ~1-2 minutes per 10 entities (configurable concurrency)
- **Report Generation**: ~30 seconds per user
- **Total Pipeline**: ~5-15 minutes (depends on data volume)

---

## Extension Points

1. **Add Entity Types**: Create new enrichment activities in `src/activities/enrichment/`
2. **Custom Reports**: Modify report generation in `src/activities/reporting_activities.py`
3. **LLM Integration**: Enhance report quality with OpenAI in reporting activities
4. **Monitoring**: Add alerts for failed workflows via Temporal webhooks
5. **Scheduling**: Use Temporal schedules for automated runs

---

## Development

### Running Tests
```bash
pytest tests/
```

### Local Development
```bash
# Start Temporal locally
docker-compose up -d

# Start worker in dev mode
python -m src.worker

# Run test pipeline
python -m src.cli_pipeline run --start-date 2025-10-07 --end-date 2025-10-13
```

---

## Production Considerations

1. **Temporal Cloud**: Consider Temporal Cloud for production deployments
2. **Monitoring**: Set up alerts for workflow failures
3. **Backup**: Backup `tmp/runs/` directory for historical data
4. **Rate Limits**: Tune `max_concurrent` based on API limits
5. **Secrets Management**: Use proper secret management (not .env in production)

---

## Migration from v1.0

If migrating from the SQLite-based v1.0:

1. Data is **not backward compatible** (different storage format)
2. Old reports remain in `tmp/` but won't be accessible via new CLI
3. Can run both systems side-by-side for transition period
4. No database migration needed (fresh start with JSON storage)

---

## Support

- **Issues**: Report bugs or feature requests via GitHub Issues
- **PRD**: See [PRD_Pipeline_Based_Architecture.md](./PRD_Pipeline_Based_Architecture.md) for detailed architecture
- **Setup**: See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for installation instructions

---

**Last Updated**: October 11, 2025
**Implementation**: Complete ✅
