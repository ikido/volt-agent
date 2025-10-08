# Changelog

## [Latest] - 2025-10-08

### Added - Fibery Integration & Improved Reporting

#### 🎯 Core Features
- **Fibery Entity Context Integration**: Full integration with Fibery.io to enrich Toggl time entries with detailed entity information
- **Feature-Level Aggregation**: Automatically groups tasks under features with comprehensive statistics
- **AI-Powered Summaries**: OpenAI GPT-4 generates contextual summaries for entities
- **Smart Caching**: SQLite-based caching for Fibery entities to reduce API calls

#### 📊 Report Enhancements
- **3-File Per-User Structure**:
  - `feature_summary.md` - Feature-centric view with all tasks
  - `project_entities.md` - Individual entity details
  - `other_activities.md` - Non-project work
- **Complete Task Visibility**: Shows ALL tasks in a feature, not just worked-on tasks
- **Time Tracking**: Displays both "Time This Week" and "Total Time (Fibery)" for all tasks
- **Timeline Information**: Shows started dates, ETAs, days since started, days to complete
- **Overdue Detection**: Automatic flagging of overdue tasks and features
- **Progress Tracking**: Task completion statistics (e.g., "5/9 tasks completed")
- **Missing Context Flags**: Highlights entities without descriptions or comments
- **Fibery Links**: Direct links to all entities in Fibery

#### 🔧 Technical Improvements
- **Kill Previous Runs**: Automatically terminates stuck previous runs on startup
- **Verbose Logging**: Progress indicators show exactly what's happening:
  - "📝 Generating report for {user} (X/Y)..."
  - "🔄 Enriching X matched entities..."
  - "✓ Enriched X entities"
  - "🎯 Enriching features from tasks..."
- **Per-Run Subfolders**: Each run creates its own timestamped folder
- **GraphQL Integration**: Efficient Fibery API queries with proper field mapping
- **Pydantic Models**: Type-safe data validation for Fibery entities
- **Defensive Coding**: Handles missing fields gracefully (Sub-tasks, features, etc.)

#### 🐛 Bug Fixes
- **Fixed Sub-task Configuration**: Correct field names (`completedDate` vs `completionDate`)
- **Fixed Feature Date Fields**: Use Feature-specific fields (`devActualStartDate`, etc.)
- **Fixed Time Units**: Proper handling of hours vs seconds in different fields
- **Fixed State Extraction**: Handle both dict and string formats for state fields
- **Fixed Assignee Display**: Pull from enriched entity data correctly
- **Removed Duplicate Flags**: Single "Missing: no description, no comments" warning

#### 📦 Dependencies Added
- `psutil==5.9.6` - For process management and killing previous runs

### Configuration Changes
- **config.yaml**: Added `fibery` section with 7 entity types configured
- **config/prompts/**: Entity-type-specific prompts for AI summarization
- **database/schema.sql**: New tables for `fibery_entities` and `fibery_users`

### File Structure
```
tmp/run_2025-10-08-15-51/
├── {user_email}_at_{domain}_com/
│   ├── feature_summary.md
│   ├── project_entities.md
│   └── other_activities.md
├── team_summary.md
└── toggl_report_log_2025-10-08-15-51.log
```

### Usage
```bash
# Generate reports for entire team with Fibery enrichment
python generate_report.py --start-date 2025-09-29 --end-date 2025-10-08 --enrich-fibery

# Generate for specific user
python generate_report.py --start-date 2025-09-29 --end-date 2025-10-08 --enrich-fibery --users alex.akilin@wearevolt.com
```

### Known Limitations
- Some entity types not yet configured (Design/Work Version, Scrum/Release)
- Fibery user fetching may fail (non-critical, continues without it)
- Features without descriptions show as "⚠️ No description, no comments"

### Next Steps
- Add configuration for remaining entity types
- Implement work alignment analysis (comparing Toggl vs Fibery states)
- Add schema validation and unknown entity type detection
- Improve prompt templates for entities with better descriptions

