# Volt Agent - Toggl Team Activity Report Generator

A Python-based automated reporting system that generates AI-powered team activity reports from Toggl time tracking data.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API credentials:

```bash
# Toggl API Credentials
TOGGL_API_TOKEN=your_toggl_api_token_here
TOGGL_WORKSPACE_ID=123456

# OpenAI API Credentials
OPENAI_API_KEY=your_openai_api_key_here
```

**Where to get credentials:**
- **Toggl API Token**: https://track.toggl.com/profile → API Token
- **Workspace ID**: Found in Toggl URL when viewing your workspace (e.g., `https://track.toggl.com/1637944/...`)
- **OpenAI API Key**: https://platform.openai.com/api-keys

### 3. Run Your First Report

Generate a report for the current week (Monday-Sunday):

```bash
python generate_report.py --start-date 2025-09-29 --end-date 2025-10-05
```

This will:
- Fetch all time entries from Toggl for all users
- Parse Fibery.io entity metadata (#ID [Database] [Type] [Project])
- Generate AI summaries using GPT-4
- Write reports to `./tmp/` directory

## Usage Examples

### Full Week Report (All Users)
```bash
python generate_report.py --start-date 2025-09-29 --end-date 2025-10-05
```

### Specific Users Only
```bash
python generate_report.py \
  --start-date 2025-09-29 \
  --end-date 2025-10-05 \
  --users user1@example.com,user2@example.com
```

### Use Cached Data (Development)
```bash
python generate_report.py \
  --start-date 2025-09-29 \
  --end-date 2025-10-05 \
  --use-cache
```

### Custom Output Directory
```bash
python generate_report.py \
  --start-date 2025-09-29 \
  --end-date 2025-10-05 \
  --output-dir ./reports
```

### Debug Mode
```bash
python generate_report.py \
  --start-date 2025-09-29 \
  --end-date 2025-10-05 \
  --log-level DEBUG
```

## Output Files

All files are written to `./tmp/` with timestamps (format: `YYYY-MM-DD-HH-MM`):

### 1. Individual Reports
**File**: `toggl_individual_reports_2025-10-03-10-48.md`

Contains per-user activity reports with:
- Summary statistics (total hours, project vs other activities)
- Work on Project Entities (concise bullet list)
- Other Activities (meetings, admin, etc.)

**Example format:**
```markdown
# Individual Activity Report: user@example.com
**Period:** 2025-09-29 to 2025-10-05  
**Generated:** 2025-10-03-10-48

## Summary Statistics
- **Total Time Tracked:** 39.3 hours
- **Time on Project Entities:** 35.2 hours (89.6%)
- **Time on Other Activities:** 4.1 hours (10.4%)

## Work on Project Entities
- **#7521 [Scrum] [Task] [Moneyball]**: Configured OpenSearch Alerts. (11.3 hours)
- **#7673 [Scrum] [Task] [Volt - Internal]**: Added Summary tab with custom fields. (6.9 hours)

## Other Activities
- **Daily standup meetings**: Team sync meetings. (2.5 hours)
- **Email and planning**: Email review and planning. (1.6 hours)
```

### 2. Team Summary
**File**: `toggl_team_summary_2025-10-03-10-48.md`

Contains:
- Executive summary of team activities
- Team statistics table
- Major focus areas and projects
- Links to individual reports

### 3. Execution Log
**File**: `toggl_report_log_2025-10-03-10-48.log`

Detailed execution log with:
- API requests and responses
- Parsing results
- LLM token usage
- Any errors or warnings

## How It Works

### 1. Data Fetching
- Uses Toggl Reports API v3 with `enrich_response=true`
- Fetches data **day-by-day** to avoid pagination limits
- Gets ~200-250 entries per week for 11-person team
- Includes full metadata: user IDs, entry IDs, durations

### 2. Entity Parsing
Automatically extracts Fibery.io metadata from descriptions:

**Input:** `Fixed bug #1234 [Backend] [Bug] [AuthService]`

**Extracted:**
- Entity ID: `1234`
- Database: `Backend`
- Type: `Bug`
- Project: `AuthService`

### 3. Data Aggregation
- Groups entries by user + description + entity
- Sums durations for grouped entries
- Separates matched (with entity ID) vs unmatched activities

### 4. AI Summarization
- Uses OpenAI GPT-4 to generate concise summaries
- **Matched entities**: One line per entity with short summary
- **Unmatched activities**: Bullet points grouped by activity type
- Factual and concise - no fluff or made-up details

### 5. Report Generation
- Writes each user's report **immediately** to file (streaming)
- Generates team summary after all individual reports
- All reports in markdown format

## Data Caching

All fetched data is cached in `./data/toggl_cache.db` (SQLite) with:
- Raw time entries from Toggl
- Processed entries with parsed metadata
- Historical tracking by run ID

Benefits:
- ✅ Reduces API calls during development
- ✅ Enables `--use-cache` mode
- ✅ Historical tracking of report runs

## Configuration

### Config File: `config/config.yaml`
Customize:
- Toggl API settings (rate limits, timeouts)
- OpenAI model and parameters
- Database paths
- Output directory
- Parsing patterns

### Prompts: `config/prompts.yaml`
Customize LLM prompts for:
- Matched entities summary
- Unmatched activities summary
- Team-level summary

## Expected Results

### For a Team of ~11 People (4-day week):
- **Total entries**: ~200-250
- **Hours per person**: 30-45 hours
- **API calls**: 7-15 (one per day + pagination)
- **Generation time**: ~2 minutes
- **LLM tokens**: ~10-15K total

### Report Sizes:
- Individual reports: ~12KB (all users combined)
- Team summary: ~5KB
- Log file: ~13KB

## Troubleshooting

### "No entries found"
- Check date range (YYYY-MM-DD format)
- Verify workspace ID is correct
- Ensure team has tracked time in that period

### "Rate limit exceeded"
- Script has automatic retry with exponential backoff
- Starter plan: 240 requests/hour limit
- Use `--use-cache` to avoid hitting limits during development

### "Missing days of data"
- The system fetches day-by-day to avoid API limits
- Check log file for any failed day fetches
- Timezone differences may affect date boundaries

### "Reports are too long/short"
- Edit prompts in `config/prompts.yaml`
- Adjust `temperature` and `max_tokens` in config

## Project Structure

```
volt-agent/
├── config/
│   ├── config.yaml              # System configuration
│   └── prompts.yaml             # LLM prompt templates
├── data/
│   └── toggl_cache.db          # SQLite cache (auto-created)
├── src/
│   ├── cli.py                   # Command-line interface
│   ├── main.py                  # Main orchestration
│   ├── database/db.py           # SQLite operations
│   ├── toggl/client.py          # Toggl API client
│   ├── parser/fibery_parser.py  # Entity parser
│   ├── llm/client.py            # OpenAI client
│   └── reporting/generator.py   # Report generation
├── tmp/                         # Generated reports (created on first run)
├── tests/                       # Test suite
├── generate_report.py           # Main entry point
└── requirements.txt             # Python dependencies
```

## Key Features

✅ **Smart Caching**: SQLite database reduces API calls  
✅ **Streaming Reports**: Written incrementally as generated  
✅ **Concise Format**: One-line summaries per entity  
✅ **Timezone Aware**: Properly handles international teams  
✅ **Rate Limiting**: Respects API limits with automatic retry  
✅ **Daily Chunking**: Fetches day-by-day to avoid pagination limits  
✅ **Optional User Filter**: Generate for all users or specific ones  

## Documentation

- **[PRD](docs/features/1-toggl-reports/PRD_Toggl_Team_Activity_Report.md)** - Complete requirements and implementation notes
- **[SETUP.md](SETUP.md)** - Detailed setup guide

## Support

For issues or questions, check:
1. The log file in `./tmp/` for detailed error messages
2. The PRD for implementation details
3. Test files in `tests/` for usage examples

---

**Built with**: Python 3.11+, OpenAI GPT-4, Toggl Reports API v3
