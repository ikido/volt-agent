# Pipeline Architecture Setup Guide

This guide walks you through setting up and running the Temporal-based pipeline architecture for Toggl-Fibery analysis.

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Toggl API token
- Fibery API token

---

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

The key new dependency is `temporalio==1.5.0` for Temporal workflow orchestration.

---

## Step 2: Configure Environment

Create or update your `.env` file with required credentials:

```bash
# Toggl Configuration
TOGGL_API_TOKEN=your_toggl_api_token_here
TOGGL_WORKSPACE_ID=your_workspace_id_here

# Fibery Configuration
FIBERY_API_TOKEN=your_fibery_api_token_here
FIBERY_WORKSPACE_NAME=your_workspace_name_here

# Optional: OpenAI for LLM reports
OPENAI_API_KEY=your_openai_key_here
```

---

## Step 3: Start Temporal Infrastructure

The pipeline uses Temporal for workflow orchestration. Start the required services:

```bash
# Start Temporal server, PostgreSQL, and UI
docker-compose up -d

# Verify services are running
docker-compose ps
```

You should see:
- `temporal` - Temporal server (port 7233)
- `temporal-ui` - Web UI (port 8080)
- `postgresql` - Database backend (port 5432)
- `temporal-admin-tools` - Admin utilities

**Temporal UI**: http://localhost:8080

---

## Step 4: Start the Temporal Worker

The worker executes pipeline activities. Open a terminal and run:

```bash
# Start the worker
python -m src.worker
```

You should see:
```
2025-10-11 15:30:45 [INFO] __main__: Connecting to Temporal server...
2025-10-11 15:30:45 [INFO] __main__: Connected to Temporal server
2025-10-11 15:30:45 [INFO] __main__: Worker configured with all activities and workflows
2025-10-11 15:30:45 [INFO] __main__: Task queue: volt-agent-pipeline
2025-10-11 15:30:45 [INFO] __main__: Starting worker...
```

**Keep this terminal open** while running pipelines.

---

## Step 5: Run the Pipeline

### Option A: Full Pipeline (Toggl → Fibery)

Start from scratch, fetching Toggl data and enriching with Fibery:

```bash
python -m src.cli_pipeline run \
  --start-date 2025-10-07 \
  --end-date 2025-10-13
```

**What happens:**
1. ✅ Cleanup Toggl stage
2. 📊 Fetch raw Toggl time entries
3. 📈 Aggregate by user and entity
4. 📝 Generate Toggl summary report
5. ✅ Cleanup Fibery stage
6. 🔍 Extract entities to enrich
7. 🌐 Enrich entities via Fibery API
8. 👤 Generate individual person reports
9. 💾 Save enriched data
10. 👥 Generate team summary report

### Option B: Fibery Re-enrichment Only

Re-run Fibery enrichment on existing Toggl data (useful for testing):

```bash
python -m src.cli_pipeline run \
  --start-from fibery \
  --run-id run_2025-10-10-15-30-45
```

### Option C: Filter by Users

Process only specific users:

```bash
python -m src.cli_pipeline run \
  --start-date 2025-10-07 \
  --end-date 2025-10-13 \
  --users john@example.com,jane@example.com
```

---

## Step 6: View Results

Pipeline outputs are saved to `tmp/runs/{run_id}/`:

```
tmp/runs/run_2025-10-10-15-30-45/
├── run_metadata.json              # Run metadata and status
├── raw_toggl_data.json            # Raw Toggl time entries
├── toggl_aggregated.json          # Aggregated Toggl data
├── enriched_data.json             # Enriched entity data
└── reports/
    ├── toggl_summary.md           # Toggl summary report
    ├── team_summary.md            # Team-level report
    └── individual/
        ├── john_doe.md            # Individual reports
        └── jane_smith.md
```

---

## CLI Commands Reference

### `pipeline run`
Run the pipeline workflow.

```bash
python -m src.cli_pipeline run [OPTIONS]

Options:
  --start-date TEXT         Start date (YYYY-MM-DD) - required if start-from=toggl
  --end-date TEXT           End date (YYYY-MM-DD) - required if start-from=toggl
  --users TEXT              Comma-separated user emails
  --start-from [toggl|fibery]  Stage to start from (default: toggl)
  --run-id TEXT             Existing run ID (required if start-from=fibery)
  --output-dir PATH         Output directory (default: ./tmp/runs)
```

### `pipeline list-runs`
List all pipeline runs.

```bash
python -m src.cli_pipeline list-runs [OPTIONS]

Options:
  --status [completed|failed|in_progress]  Filter by status
  --limit INTEGER                          Max runs to show (default: 10)
```

Example output:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Run ID                     ┃ Status    ┃ Created           ┃ Duration ┃ Stages      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ run_2025-10-10-15-30-45    │ completed │ 2025-10-10T15:30  │ 8m 45s   │ toggl,fibery│
│ run_2025-10-10-14-20-12    │ completed │ 2025-10-10T14:20  │ 7m 32s   │ toggl,fibery│
└────────────────────────────┴───────────┴───────────────────┴──────────┴─────────────┘
```

### `pipeline show-run`
Show details of a specific run.

```bash
python -m src.cli_pipeline show-run RUN_ID
```

### `pipeline cancel-run`
Cancel a running workflow.

```bash
python -m src.cli_pipeline cancel-run RUN_ID
```

### `pipeline temporal-ui`
Open Temporal UI in browser.

```bash
python -m src.cli_pipeline temporal-ui [--run-id RUN_ID]
```

---

## Monitoring and Debugging

### Temporal UI

Access the Temporal Web UI at http://localhost:8080 to:
- View workflow execution history
- Inspect activity inputs/outputs
- Debug failures with full stack traces
- Monitor worker status
- View pending and completed workflows

### Worker Logs

The worker outputs detailed logs for each activity:

```
2025-10-11 15:35:20 [INFO] fetch_toggl_data: Fetching Toggl data from 2025-10-07 to 2025-10-13
2025-10-11 15:36:45 [INFO] fetch_toggl_data: Retrieved 342 time entries
2025-10-11 15:36:50 [INFO] aggregate_toggl_data: Aggregating Toggl data
2025-10-11 15:36:52 [INFO] aggregate_toggl_data: Aggregated 5 users, 87 entities
```

### Run Metadata

Check `tmp/runs/{run_id}/run_metadata.json` for:
- Current status
- Completed stages
- Failed stages (if any)
- Error messages
- Temporal workflow ID

---

## Configuration

### Enrichment Configuration

Edit `config/enrichment_config.yaml` to customize:
- Entity-specific enrichment activities
- Concurrency limits per entity type
- Fields to fetch for each type

Example:
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
```

---

## Troubleshooting

### Issue: "Connection refused" to Temporal

**Solution**: Ensure Temporal is running:
```bash
docker-compose ps temporal
docker-compose logs temporal
```

### Issue: "No worker available"

**Solution**: Start the worker in a separate terminal:
```bash
python -m src.worker
```

### Issue: Activities timing out

**Solution**: Check activity timeout settings in `src/workflows/pipeline_workflow.py` and adjust as needed.

### Issue: Fibery API rate limits

**Solution**: Reduce `max_concurrent` values in `config/enrichment_config.yaml`.

---

## Cleanup

### Stop Temporal Infrastructure

```bash
# Stop services
docker-compose down

# Remove volumes (deletes all workflow history)
docker-compose down -v
```

### Clear Run Data

```bash
# Remove all run outputs
rm -rf tmp/runs/*
```

---

## Architecture Benefits

✅ **Reliability**: Temporal handles failures, retries automatically
✅ **Observability**: Built-in workflow history and progress tracking
✅ **Debuggability**: Inspect execution in Temporal UI
✅ **Flexibility**: Start from any stage, re-run enrichment without re-fetching
✅ **Scalability**: Bounded parallelism prevents API overload
✅ **Extensibility**: Add new entity types via configuration
✅ **Idempotency**: Cleanup activities ensure safe re-runs

---

## Next Steps

1. **Customize Enrichment**: Add entity types specific to your Fibery workspace
2. **LLM Integration**: Enhance reports with OpenAI integration in reporting activities
3. **Monitoring**: Set up alerts for failed workflows
4. **Scheduling**: Use Temporal schedules for automated daily/weekly reports

---

**Need Help?**
Check the [PRD](./PRD_Pipeline_Based_Architecture.md) for architectural details or [Implementation Status](./IMPLEMENTATION_STATUS.md) for component reference.
