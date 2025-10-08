# PRD: Fibery Entity Context Integration - Analysis & Validation

**Version:** 2.0  
**Date:** October 8, 2025  
**Status:** 📝 Planning  

> **📚 Part of:** [Fibery Entity Context Integration](./README.md)  
> **Related Docs:** [Core Requirements](./PRD_Core.md) | [Configuration](./PRD_Configuration.md) | [Database Schema](./PRD_Database_Schema.md)

---

## Overview

This document outlines the analysis and validation features of the Fibery Entity Context Integration. Unlike traditional systems that store tracking data in databases, **we output all analysis as markdown reports** - keeping the database simple and analysis visible.

**Philosophy:** The database is just a cache. All intelligence goes into the reports.

---

## 1. The Challenge

Fibery is a flexible platform where workspace structure evolves over time:

- **New entity types** may be created
- **Existing entity types** may be modified (fields added/removed)
- **Entity types** may be logged in Toggl before we configure them
- **Our configuration** may become stale

**Without proactive handling**, the system would:
- Fail silently on unknown entity types
- Miss schema changes that affect data quality
- Require manual audits to maintain configuration health

**Solution:** Build a self-documenting system that analyzes and reports issues in every run.

---

## 2. Unknown Entity Type Handling

### 2.1 Detection

**When is an entity type considered "unknown"?**

An entity type is unknown when:
1. It appears in Toggl time entries (e.g., `#7890 [Scrum] [QA-Task]`)
2. It's NOT configured in `config/config.yaml` under `fibery.entity_types`

### 2.2 Handling Process

**Step 1: Attempt to fetch basic information**

Even for unknown types, try to fetch entity data using REST API or generic GraphQL:

```python
# Try to fetch using generic approach
try:
    entity_data = fibery_client.get_entity_by_public_id(
        public_id="7890",
        fallback_to_rest=True
    )
    # Store in cache with minimal info
    # Use generic prompt for summarization
except EntityNotFound:
    # Use only Toggl metadata
    entity_data = {"name": description_from_toggl}
```

**Step 2: Use fallback summarization**

Apply generic LLM prompt from `config/prompts/generic.txt`:

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

**Step 3: Flag in individual report**

```markdown
### #7890 [Scrum] [QA-Task] [Testing Project]
- **Time Spent:** 3.2 hours
- **Description:** Testing new features

⚠️ **Unknown Entity Type:** "Scrum/QA-Task" is not configured.
Using generic context extraction (limited information available).

**Generic Summary:**
This appears to be a quality assurance task focused on testing new features.
Based on Toggl logs, work involved manual testing and bug documentation.

**Action Required:** Add configuration for this entity type to get detailed context.
See: [Configuration Guide](./PRD_Configuration.md)
```

**Step 4: Collect statistics during run**

Track in-memory during report generation:

```python
unknown_types_stats = {
    "Scrum/QA-Task": {
        "count": 3,
        "total_hours": 5.2,
        "entities": ["7890", "7891", "7892"],
        "users": ["ivan@example.com", "maria@example.com"],
        "sample_data": {...}
    },
    "Scrum/Sprint": {
        "count": 1,
        "total_hours": 1.5,
        "entities": ["7901"],
        "users": ["anton@example.com"],
        "sample_data": {...}
    }
}
```

**Step 5: Output dedicated markdown report**

Generate `unknown_entities_YYYY-MM-DD.md`:

```markdown
# Unknown Entity Types Report

**Date:** 2025-10-07  
**Period:** 2025-09-29 to 2025-10-05

---

## Summary

- **Unknown Types Detected:** 2
- **Total Hours on Unknown Types:** 6.7 hours (15% of all logged time)
- **Entities Affected:** 4
- **Users Affected:** 3

---

## Unknown Entity Types

### 1. Scrum/QA-Task ⚠️ HIGH PRIORITY

**Impact:**
- **Occurrences:** 3 entities
- **Time Logged:** 5.2 hours
- **Users Affected:** 2 (Ivan Kuzmin, Maria Ivanova)
- **Sample IDs:** #7890, #7891, #7892

**Priority Score:** 72 (High)
- Formula: `(total_hours * 10) + (occurrence_count * 5) + (user_count * 2)`
- Calculation: `(5.2 * 10) + (3 * 5) + (2 * 2) = 72`

**Recommendation:** Configure immediately (significant usage)

**Sample Entity Data:**

```json
{
  "id": "uuid-...",
  "publicId": "7890",
  "name": "Test Feature X on staging",
  "type": "Scrum/QA-Task",
  "fields": {
    "description": "...",
    "state": "In Progress",
    ...
  }
}
```

**Recommended Configuration:**

Add to `config/config.yaml`:

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
    test_results: "testResults"
    related_feature: "relatedFeature { publicId name }"
  prompt_template: "qa_task"  # Create ./config/prompts/qa_task.txt
```

Create `./config/prompts/qa_task.txt`:

```
You are summarizing a QA Task entity from Fibery for a time tracking report.

Focus on:
- What is being tested
- Test results and findings
- Related features or bugs
- QA timeline and status

Keep it concise and factual.

QA Task Data:
{entity_json}

Generate the summary:
```

---

### 2. Scrum/Sprint 📊 LOW PRIORITY

**Impact:**
- **Occurrences:** 1 entity
- **Time Logged:** 1.5 hours
- **Users Affected:** 1 (Anton Potapov)
- **Sample IDs:** #7901

**Priority Score:** 17 (Low)

**Recommendation:** Monitor usage. Generic prompt may be sufficient for rare usage.

---

## Actions Required

### High Priority
1. ✅ **Configure Scrum/QA-Task** - Significant usage (5.2 hours, 3 entities)
   - Effort: 15-30 minutes
   - Impact: +15% coverage, better QA context

### Low Priority
2. 📊 **Monitor Scrum/Sprint** - Rare usage (1.5 hours, 1 entity)
   - Effort: N/A (wait for more usage)
   - Impact: Minimal

---

## Coverage Impact

**Current Coverage:** 85% (38 of 45 entities configured)  
**If QA-Task configured:** 91% (41 of 45 entities)  
**Improvement:** +6%

---

**Generated:** 2025-10-07 14:30  
**Next Steps:** Review recommendations and update configuration as needed.
```

---

## 3. Work Alignment Analysis

### 3.1 What is Work Alignment?

Work alignment checks consistency between Toggl (where time is logged) and Fibery (where work is tracked):

- **Properly tracked:** Time logged AND Fibery state matches
- **Fibery not updated:** Time logged BUT Fibery state is stale
- **Missing in Toggl:** Entity assigned in Fibery BUT no time logged
- **Open:** Entity assigned BUT not started yet

### 3.2 Analysis Process

**During report generation:**

```python
alignment_issues = []

for user in users:
    for entity in user.entities:
        toggl_hours = get_toggl_hours(user, entity)
        fibery_state = entity.metadata.get("state", {}).get("name")
        fibery_assigned = entity.metadata.get("assignees", [])
        
        # Check alignment
        if toggl_hours > 0 and fibery_state in ["Done", "Completed"]:
            # Properly tracked
            continue
        elif toggl_hours > 5 and fibery_state in ["Open", "To Do"]:
            # Fibery not updated!
            alignment_issues.append({
                "type": "fibery_not_updated",
                "entity": entity,
                "user": user,
                "toggl_hours": toggl_hours,
                "fibery_state": fibery_state
            })
        elif toggl_hours == 0 and user.email in [a.email for a in fibery_assigned]:
            if fibery_state not in ["Open", "To Do"]:
                # Missing time tracking!
                alignment_issues.append({
                    "type": "missing_in_toggl",
                    "entity": entity,
                    "user": user
                })
```

### 3.3 Work Alignment Report

Generate `work_alignment_YYYY-MM-DD.md`:

```markdown
# Work Alignment Analysis

**Date:** 2025-10-07  
**Period:** 2025-09-29 to 2025-10-05

---

## Summary

- **Entities Analyzed:** 45
- **Properly Tracked:** 38 (84%)
- **Issues Detected:** 7 (16%)
  - Fibery Not Updated: 4
  - Missing in Toggl: 2
  - Open (assigned but not started): 1

---

## Issues by Type

### 🔴 Fibery Not Updated (4 issues)

Time logged in Toggl but Fibery state not reflecting progress.

#### 1. #7658 - AWS Infrastructure Provisioning

**User:** Alex Akilin  
**Time Logged:** 17.7 hours  
**Fibery State:** ⚠️ "In Progress"  
**Expected State:** "Done" or "Completed"

**Issue:** Significant time logged (17.7 hours) but entity still marked "In Progress" in Fibery.

**Action:** Update Fibery state to reflect completion.

---

#### 2. #7634 - Twenty-CRM Deployment

**User:** Alex Akilin  
**Time Logged:** 8.5 hours  
**Fibery State:** ⚠️ "In Review"  
**Expected State:** "Done"

**Issue:** Work completed but not marked done.

**Action:** Mark as done in Fibery.

---

### 🟡 Missing in Toggl (2 issues)

Assigned in Fibery but no time logged in Toggl.

#### 1. #7825 - Security Audit

**User:** Maria Ivanova  
**Assigned in Fibery:** ✅ Yes  
**Time Logged in Toggl:** ❌ 0 hours  
**Fibery State:** "In Progress"

**Issue:** Entity assigned and marked in progress but no time tracking.

**Action:** Ensure time tracking is enabled for this work.

---

### ⚪ Open (1 issue)

Assigned but not yet started (normal state, tracking for visibility).

#### 1. #7830 - Documentation Handoff

**User:** Ivan Kuzmin  
**Assigned in Fibery:** ✅ Yes  
**Time Logged:** 0 hours  
**State:** "To Do"

**Status:** Normal - assigned but not started yet.

---

## Alignment by User

| User | Properly Tracked | Issues |
|------|-----------------|--------|
| Alex Akilin | 6 entities | 2 (Fibery not updated) |
| Ivan Kuzmin | 4 entities | 1 (Open) |
| Maria Ivanova | 3 entities | 1 (Missing in Toggl) |

---

## Actions Required

### High Priority
1. ✅ **Update Fibery states** for #7658, #7634 (completed work not marked done)
2. ✅ **Enable time tracking** for #7825 (work in progress but not logged)

### Low Priority
3. 📊 **Monitor** #7830 (assigned but not started - normal)

---

**Generated:** 2025-10-07 14:30  
**Next Run:** Check if issues were resolved
```

---

## 4. Configuration Validation

### 4.1 Validation Checks

**On script start (before fetching data):**

Validate configuration against live Fibery schema:

```python
validation_results = {
    "entity_type_checks": [],
    "field_checks": [],
    "coverage_check": {}
}

# 1. Check configured entity types exist
for config_type in configured_entity_types:
    if config_type not in workspace_schema:
        validation_results["entity_type_checks"].append({
            "type": "entity_type_missing",
            "entity_type": config_type,
            "severity": "error"
        })

# 2. Check configured fields exist
for config_type in configured_entity_types:
    for field in config_type.fields:
        if field not in schema[config_type].fields:
            validation_results["field_checks"].append({
                "type": "field_missing",
                "entity_type": config_type,
                "field": field,
                "severity": "warning"
            })

# 3. Check workspace types not configured
for schema_type in workspace_schema:
    if schema_type not in configured_entity_types:
        validation_results["coverage_check"][schema_type] = {
            "status": "not_configured",
            "in_toggl_logs": check_if_in_toggl(schema_type)
        }
```

### 4.2 Console Output

**Startup validation:**

```
🔍 Validating Fibery Configuration...

✅ Configuration Validation: Passed with warnings

**Entity Type Validation:**
✅ 14/14 configured entity types exist in workspace

**Field Validation:**
⚠️  1 issue detected:
  - Field "Scrum/Task/oldField" not found in workspace
  - Configured at: config/config.yaml (entity types → Scrum/Task)
  - Recommendation: Remove from configuration (field may have been removed)

**Coverage Check:**
⚠️  2 workspace entity types not configured:
  - Scrum/QA-Task (appears in recent Toggl logs)
  - Scrum/Sprint (not seen in logs)
  
**Recommendation:** Add configuration for Scrum/QA-Task (active usage detected)

---

✓ Validation complete. Proceeding with report generation...
```

### 4.3 Validation Report

Generate `config_validation_YYYY-MM-DD.md`:

```markdown
# Configuration Validation Report

**Date:** 2025-10-07  
**Validation Status:** ✅ Passed with warnings

---

## Summary

- **Configured Entity Types:** 14
- **Valid:** 14 (100%)
- **Errors:** 0
- **Warnings:** 1

---

## Validation Results

### ✅ Entity Type Validation

All 14 configured entity types exist in Fibery workspace.

**Configured Types:**
- Scrum/Task ✅
- Scrum/Sub-task ✅
- Scrum/Bug ✅
- Scrum/Sub-bug ✅
- Scrum/Feature ✅
- Scrum/Build ✅
- Scrum/Release ✅
- Scrum/Hotfix ✅
- Scrum/Chore ✅
- Scrum/Epic ✅
- Scrum/Sprint ✅
- Design/Design Feature ✅
- Design/Work Version ✅

---

### ⚠️ Field Validation

1 warning detected:

#### Warning: Field Not Found

**Entity Type:** Scrum/Task  
**Field:** `oldField`  
**Location:** `config/config.yaml` (entity_types → Scrum/Task → fields)  
**Severity:** Warning

**Issue:** Configured field "oldField" does not exist in workspace schema.

**Possible Causes:**
- Field was removed from Fibery
- Field name changed
- Typo in configuration

**Recommendation:** Remove from configuration or update field name.

---

### 📊 Coverage Analysis

**Workspace entity types NOT in configuration:**

| Type | In Toggl Logs? | Recommendation |
|------|----------------|----------------|
| Scrum/QA-Task | ✅ Yes | Configure (active usage) |
| Scrum/Sprint | ❌ No | Optional (no recent usage) |
| Design/Old Work Version | ❌ No | Deprecated (skip) |

---

## Actions Required

### High Priority
1. ⚠️ **Remove or fix field:** Scrum/Task/oldField in configuration
2. ✅ **Add configuration:** Scrum/QA-Task (found in Toggl logs)

### Low Priority
3. 📊 **Monitor:** Other unconfigured types (no usage detected)

---

**Generated:** 2025-10-07 14:30  
**Next Validation:** Next report generation run
```

---

## 5. Report Integration

### 5.1 Report Generation Workflow

**Step 1:** Generate analysis markdown files
- `work_alignment_YYYY-MM-DD.md`
- `unknown_entities_YYYY-MM-DD.md`
- `config_validation_YYYY-MM-DD.md`

**Step 2:** Generate main reports with LLM (individual + team summary)
- LLM generates main report content
- Does NOT include analysis sections in LLM prompt

**Step 3:** Append analysis reference section to combined reports
- After LLM generation completes
- Append standardized section to bottom of team summary
- Link to separate analysis markdown files

### 5.2 Analysis Reference Section (Appended After LLM)

This section is **appended to the bottom** of the team summary report after LLM generation:

```markdown
---

## 📊 Analysis & Recommendations

This report includes additional analysis files generated during this run:

- **[Work Alignment Analysis](./work_alignment_2025-10-07.md)** - 7 issues detected
- **[Unknown Entity Types](./unknown_entities_2025-10-07.md)** - 2 types need configuration  
- **[Configuration Validation](./config_validation_2025-10-07.md)** - 1 warning

**Action Required:** Review analysis files for configuration improvements.

### Quick Summary

**Work Alignment:** 7 issues (4 Fibery not updated, 2 missing tracking)  
**Configuration:** 14 types configured, 2 unknown types detected, 1 field warning  
**Coverage:** 85% (38 of 45 entities)

### Recommended Actions

**High Priority:**
1. ✅ Configure Scrum/QA-Task (+6% coverage)
2. ⚠️ Fix field configuration: Scrum/Task/oldField
3. 🔄 Update Fibery states for completed work

**Low Priority:**
4. 📊 Monitor Scrum/Sprint usage

**Details:** See individual analysis files linked above.
```

**Implementation:**
```python
# After LLM generates team summary
team_summary = llm.generate_team_summary(data)

# Append analysis section
analysis_section = generate_analysis_reference_section(
    work_alignment_issues=7,
    unknown_types_count=2,
    validation_warnings=1,
    coverage_percent=85,
    date="2025-10-07"
)

final_report = team_summary + "\n\n---\n\n" + analysis_section
```

---

## 6. File Output Structure

**Report generation creates:**

```
./tmp/report_2025-10-07-14-30/
├── toggl_individual_reports.md          # Main individual reports
├── toggl_team_summary.md                # Main team report
│
├── work_alignment_2025-10-07.md         # ← Work alignment analysis
├── unknown_entities_2025-10-07.md       # ← Unknown entity types
├── config_validation_2025-10-07.md      # ← Configuration validation
│
└── debug/
    ├── entity_7658_data.json
    ├── entity_7634_data.json
    └── unknown_entity_7890_sample.json
```

---

## 7. CLI Commands

### 7.1 Validate Configuration Only

```bash
# Validate config without generating report
python generate_report.py --validate-config-only

# Output:
# 🔍 Validating Fibery Configuration...
# ✅ Validation complete. See: ./tmp/validation_2025-10-07.md
```

### 7.2 Force Analysis

```bash
# Generate only analysis reports (no main reports)
python generate_report.py --analysis-only \
  --start-date 2025-09-29 \
  --end-date 2025-10-05
```

---

## 8. Best Practices

### 8.1 Regular Review

**After each report:**
- Review work alignment issues (fix mismatches)
- Check unknown entity types (configure high-priority)
- Review configuration validation (fix errors)

**Weekly:**
- Update configuration for high-priority unknown types
- Fix work alignment issues

**Monthly:**
- Review coverage trends
- Clean up deprecated configurations

### 8.2 When to Configure New Types

**Configure when:**
- Priority score > 50 (high impact)
- Appears in >5% of logged entities
- Multiple users affected
- Specific context needed

**Skip when:**
- Priority score < 20 (low impact)
- Rare occurrence (<2 instances)
- Generic prompt sufficient

---

## Related Documentation

- **[PRD_Core.md](./PRD_Core.md)** - Core requirements
- **[PRD_Configuration.md](./PRD_Configuration.md)** - How to configure entity types
- **[PRD_Database_Schema.md](./PRD_Database_Schema.md)** - Simple cache tables (no tracking)
- **[PRD_Report_Formats.md](./PRD_Report_Formats.md)** - Main report formats

---

**End of Analysis & Validation Document**
