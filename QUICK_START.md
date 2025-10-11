# Quick Start: Pipeline Architecture

Get up and running with the Temporal-based pipeline in 5 minutes.

---

## Prerequisites

```bash
# Check you have these installed
docker --version    # Docker 20+
python --version    # Python 3.9+
```

---

## Step 1: Install (30 seconds)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify Temporal is in requirements
grep temporalio requirements.txt
```

---

## Step 2: Configure (1 minute)

Create `.env` file:

```bash
# Toggl
TOGGL_API_TOKEN=your_token_here
TOGGL_WORKSPACE_ID=12345

# Fibery
FIBERY_API_TOKEN=your_token_here
FIBERY_WORKSPACE_NAME=yourworkspace
```

---

## Step 3: Start Temporal (30 seconds)

```bash
# Start Temporal server
docker-compose up -d

# Verify it's running
docker-compose ps
```

**Temporal UI**: http://localhost:8080

---

## Step 4: Start Worker (1 second)

Open a **new terminal** and run:

```bash
python -m src.worker
```

Keep this terminal open!

---

## Step 5: Run Pipeline (5 seconds)

```bash
# Run full pipeline
python -m src.cli_pipeline run \
  --start-date 2025-10-07 \
  --end-date 2025-10-13
```

**Watch progress** in real-time!

---

## View Results

```bash
# List all runs
python -m src.cli_pipeline list-runs

# Show specific run
python -m src.cli_pipeline show-run run_2025-10-10-15-30-45

# View reports
ls -la tmp/runs/run_2025-10-10-15-30-45/reports/
```

---

## Common Commands

```bash
# Run for specific users
python -m src.cli_pipeline run \
  --start-date 2025-10-07 --end-date 2025-10-13 \
  --users john@example.com,jane@example.com

# Re-run enrichment only
python -m src.cli_pipeline run \
  --start-from fibery \
  --run-id run_2025-10-10-15-30-45

# Cancel workflow
python -m src.cli_pipeline cancel-run run_2025-10-10-15-30-45

# Open Temporal UI
python -m src.cli_pipeline temporal-ui
```

---

## Troubleshooting

### "Connection refused"
➜ Start Temporal: `docker-compose up -d`

### "No worker available"
➜ Start worker: `python -m src.worker`

### "Missing credentials"
➜ Check your `.env` file has all tokens

---

## What Gets Created

```
tmp/runs/run_2025-10-10-15-30-45/
├── run_metadata.json              # Run info
├── raw_toggl_data.json            # Raw data
├── toggl_aggregated.json          # Aggregated
├── enriched_data.json             # Enriched
└── reports/
    ├── toggl_summary.md           # Toggl report
    ├── team_summary.md            # Team report
    └── individual/
        ├── user1.md               # Per-user
        └── user2.md
```

---

## Pipeline Stages

```
1. TOGGL STAGE
   ├─ Cleanup
   ├─ Fetch data (5-10 min)
   ├─ Aggregate
   └─ Generate report

2. FIBERY STAGE
   ├─ Cleanup
   ├─ Extract entities
   ├─ Enrich (2-5 min)
   ├─ Generate person reports
   └─ Generate team report
```

---

## Need More Help?

- **Setup Guide**: [docs/features/3-pipeline-architecture/SETUP_GUIDE.md](docs/features/3-pipeline-architecture/SETUP_GUIDE.md)
- **Architecture**: [docs/features/3-pipeline-architecture/README.md](docs/features/3-pipeline-architecture/README.md)
- **PRD**: [docs/features/3-pipeline-architecture/PRD_Pipeline_Based_Architecture.md](docs/features/3-pipeline-architecture/PRD_Pipeline_Based_Architecture.md)

---

**Total Time**: ~5 minutes to first pipeline run! 🚀
