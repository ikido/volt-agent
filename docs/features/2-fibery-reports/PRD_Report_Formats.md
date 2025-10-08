# PRD: Fibery Entity Context Integration - Report Formats

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** 📝 Planning  

> **📚 Part of:** [Fibery Entity Context Integration](./README.md)  
> **Related Docs:** [Core Requirements](./PRD_Core.md) | [Configuration](./PRD_Configuration.md)

---

## Overview

This document defines the enhanced report formats for the Fibery Entity Context Integration feature. These formats extend the existing Toggl reports with rich contextual information from Fibery.

---

## 1. Individual Report (Enriched)

### 1.1 Report Header

```markdown
# Enhanced Activity Report: Alex Akilin
**Email:** alex.akilin@wearevolt.com  
**Period:** 2025-09-29 to 2025-10-05  
**Generated:** 2025-10-07 14:30  
**Report Type:** Enriched with Fibery Context

---
```

### 1.2 Executive Summary

```markdown
## Executive Summary

Alex worked 58.1 hours this week, with 53.2 hours (91.4%) on project entities and 5.0 hours (8.6%) on other activities. Primary focus areas included AWS infrastructure provisioning for Huber, OpenSearch alert configuration for Moneyball, and SnowFlake replication fixes.

**Key Deliverables:**
- ✅ Complete AWS infrastructure deployed in Huber AWS Organization
- ✅ OpenSearch alerting system configured and operational
- ✅ SnowFlake data replication issues resolved
- ✅ Twenty-CRM deployment completed with custom configurations

---
```

### 1.3 Summary Statistics

```markdown
## Summary Statistics

- **Total Time Tracked:** 58.1 hours
- **Time on Project Entities:** 53.2 hours (91.4%)
- **Time on Other Activities:** 5.0 hours (8.6%)
- **Entities Worked On:** 6
- **Entities Completed:** 5

---
```

### 1.4 Entity Details (Full Context)

#### Detailed Entity Section

```markdown
## Work on Project Entities (53.2 hours)

### #7658: Provision AWS Infrastructure in Huber AWS Org ID
**Time:** 17.7 hours | **Type:** Task | **Status:** ✅ Done | **Database:** Scrum | **Project:** Volt - Internal

**What was accomplished:**
Provisioned complete AWS infrastructure in Huber AWS Organization including VPC setup, subnet configuration, security groups, IAM roles, and EC2 instances for production environment. Infrastructure follows best practices for security and scalability.

**Task Timeline:**
- **Started:** 2025-09-29 (Planned: 2025-09-20)
- **Completed:** 2025-10-05 (Planned: 2025-09-23)
- **Duration:** 7 days (3 days over estimate)
- **Status:** ✅ Done

**Part of Feature #1575: Create AWS Infrastructure for Huber**

**Feature Progress & Timeline:**
- **Feature Started:** 2025-09-15
- **Feature ETA:** 2025-10-15 (still on track)
- **Progress:** 4 of 7 tasks completed (57%)
- **Time Invested:** 45.2 hours across team
- **Estimated Remaining:** 30 hours

**What's Done:**
- ✅ #7658 - AWS Infrastructure provisioning (this task)
- ✅ #7634 - Twenty-CRM deployment
- ✅ #7695 - Twenty-CRM additional configuration
- ✅ #7693 - Environment variable setup

**What's Left:**
- 🔄 #7812 - Load testing and performance optimization
- ⏳ #7825 - Security audit and hardening
- ⏳ #7830 - Documentation and handoff to Huber team

**Connected User Requests:**
- User Request #456: AWS Environment Requirements (Priority: High)

**Why this matters:**
This task is part of strategic infrastructure work for Huber client. Completing this enables the deployment of their production CRM system, which is blocking go-live scheduled for October 20th.

**Key activities from Fibery:**
- Designed VPC architecture with multi-AZ support
- Configured security groups and network ACLs
- Set up IAM roles and policies for service access
- Deployed EC2 instances and load balancers
- Documented infrastructure setup in Confluence

---
```

#### Nested Entity Section

For entities like Sub-tasks that need parent context:

```markdown
### #9234: Update user authentication logic
**Time:** 3.2 hours | **Type:** Sub-task | **Status:** ✅ Done | **Database:** Scrum | **Project:** Volt - Internal

**What was accomplished:**
Updated user authentication logic to support OAuth 2.0 and JWT token refresh mechanisms.

**Context Chain:**
- **Sub-task of Task #7658:** Implement user management system
- **Part of Feature #1575:** User Authentication & Authorization
- **Strategic Goal:** Complete authentication overhaul for Q4 2025

**Why this matters:**
This sub-task is a specific technical component of the larger user management system. Without the parent context, it would appear as isolated technical work, but it's actually part of a strategic authentication initiative tied to the Q4 roadmap.

**Timeline:**
- Started: 2025-10-03
- Completed: 2025-10-04
- **Parent Task Status:** In Progress (60% complete)
- **Feature Status:** On track for Oct 20 release

---
```

#### Simplified Entity Section

For entities with less context or shorter work time:

```markdown
### #7634: Deploy Twenty-CRM for Huber
**Time:** 4.5 hours | **Type:** Task | **Status:** ✅ Done | **Database:** Scrum | **Project:** Volt - Internal

**What was accomplished:**
Deployed Twenty-CRM application for Huber client with custom configurations and integrations.

**Timeline:**
- Completed: 2025-10-02

---
```

### 1.5 Other Activities

```markdown
## Other Activities (5.0 hours)

### SnowFlake Discussion
**Time:** 3.0 hours  
**Description:** Technical discussion with Ivan Kuzmin regarding SnowFlake architecture and replication strategy.

### Cost Management
**Time:** 2.0 hours  
**Description:** Analyzed and optimized AWS infrastructure costs.

---
```

### 1.6 Work Alignment Analysis

```markdown
## Work Alignment Analysis

### ✅ Properly Tracked (6 entities)
All entities worked on this week are properly reflected in both Toggl and Fibery.

### ⚠️ Items Needing Attention (0)
No discrepancies found this week.

### 📋 Open Entities (2 entities)

**Assigned to you but not yet started:**
- #7710 - API Integration Task (To Do, Planned Start: 2025-10-08)
- #7805 - Security Audit (In Progress, Started: 2025-10-01, no time logged this week)

---
```

### 1.7 Configuration & Coverage Report

```markdown
## 📊 Configuration & Coverage Report

### Entity Type Coverage
- ✅ **Configured:** 7 entity types (100% of your logged entities)
- ✅ **Unknown:** 0 entity types

**Your Entity Types This Week:**
- Scrum/Task: 4 entities, 51.2 hours
- Scrum/Bug: 1 entity, 2.0 hours  
- All types are configured with full context extraction

### Schema Status
- ✅ Schema validation: Passed
- Last validated: 2025-10-07
- No changes detected since last run

---
```

---

## 2. Team Summary (Enhanced)

### 2.1 Report Header

```markdown
# Team Activity Report (Enhanced)
**Period:** 2025-09-29 to 2025-10-05  
**Generated:** 2025-10-07 14:30  
**Team Members:** 11

---
```

### 2.2 Executive Summary

```markdown
## Executive Summary

The team logged 358.5 hours this week across infrastructure, development, and operational tasks. Major focus areas included AWS infrastructure provisioning, CRM deployments, data pipeline fixes, and feature development. Most work (82%) was properly tracked with entity IDs, showing good discipline in time tracking practices.

**Key Team Achievements:**
- ✅ Complete AWS infrastructure deployed for Huber client
- ✅ Multiple Twenty-CRM deployments completed
- ✅ Critical SnowFlake data replication issues resolved
- ✅ OpenSearch monitoring and alerting implemented

**Areas of Focus:**
1. Infrastructure & DevOps (35% of tracked time)
2. CRM Development & Deployment (28% of tracked time)
3. Data Pipeline & Backend (22% of tracked time)
4. Frontend Development (15% of tracked time)

---
```

### 2.3 Team Statistics

```markdown
## Team Statistics

- **Total Team Time Tracked:** 358.5 hours
- **Time on Project Entities:** 293.4 hours (82%)
- **Time on Other Activities:** 65.1 hours (18%)
- **Total Entities Worked On:** 42 unique entities
- **Total Entities Completed:** 35 entities

### Time Distribution by Team Member

| Team Member | Total Hours | Project Work | Other Work | Entities |
|-------------|-------------|--------------|------------|----------|
| Alex Akilin | 58.1 | 53.2 (91%) | 5.0 (9%) | 6 |
| Alexander Prozorov | 41.6 | 28.0 (67%) | 13.6 (33%) | 2 |
| Anton Potapov | 45.2 | 38.5 (85%) | 6.7 (15%) | 5 |
| ... | ... | ... | ... | ... |

---
```

### 2.4 Major Projects & Initiatives

```markdown
## Major Projects & Initiatives

### Infrastructure & DevOps (125 hours)

**Huber AWS Infrastructure (#7658, #7634, #7695, #7693)**
- Complete AWS environment provisioned
- Twenty-CRM deployed with custom configurations
- Team: Alex Akilin (lead), Anton Potapov (support)
- Status: ✅ Completed

**Monitoring & Observability (#7521)**
- OpenSearch alerting system configured
- Team: Alex Akilin
- Status: ✅ Completed

### Data & Backend (95 hours)

**SnowFlake Data Pipeline (#7686, #7685)**
- Replication issues resolved
- Validation and monitoring implemented
- Team: Alex Akilin, Ivan Kuzmin
- Status: 🔄 In Progress (95% complete)

### Frontend Development (68 hours)

**UI Component Updates (#7702, #7703, #7704)**
- Multiple component refactorings
- Team: Alexander Prozorov, Maria Ivanova
- Status: ✅ Completed

---
```

### 2.5 Work Alignment Summary

```markdown
## Work Alignment Summary

### Team-Wide Metrics
- **Properly Tracked:** 40 entities (95%)
- **Needs Fibery Update:** 2 entities (5%)
- **Missing Time Logs:** 3 entities
- **Open Entities:** 15 entities

### Items Needing Attention

**Entities logged in Toggl but not updated in Fibery:**
- #7634 - Deploy Twenty-CRM (Alex Akilin, 4.5h logged, status still "To Do")
- #7702 - UI Component Update (Alexander Prozorov, 3.2h logged, status "In Progress" but work completed)

**Entities assigned in Fibery but no time logged:**
- #7800 - Database Migration (Alex Akilin, assigned, no time logged)
- #7815 - API Documentation (Anton Potapov, assigned, no time logged)

---
```

### 2.6 Team Configuration & Coverage Report

```markdown
## 📊 Team Configuration & Coverage Report

### Entity Type Coverage
- ✅ **Configured:** 7 entity types (85% of all logged entities)
- ⚠️ **Unknown:** 2 entity types (15% of all logged entities)

**Unknown Entity Types Detected:**

#### 1. Scrum/QA-Task (High Priority)
- **Impact:** 5.2 hours logged across 2 team members
- **Occurrences:** 3 entities
- **Sample:** #7890, #7891, #7892
- **Users Affected:** QA team, Ivan Kuzmin
- **Action Required:** Add configuration for QA-specific context
  ```yaml
  # Add to config/config.yaml
  - storage_type: "Scrum/QA-Task"
    graphql_type: "QATask"
    query_function: "findQATasks"
  ```
- **Recommended Prompt:** Create `fibery_entity_summary_prompt_qa_task`

#### 2. Scrum/Sprint (Low Priority)
- **Impact:** 1.5 hours logged, 1 occurrence
- **Users Affected:** Anton Potapov
- **Action:** Generic prompt may be sufficient (low usage)

### Schema Status
- ⚠️ **Changes Detected:** 2 schema changes since last run
- Last validated: 2025-10-01
- Current date: 2025-10-07

**Changes Detected:**

1. **New Field Added:**
   - Entity: Scrum/Task
   - Field: `Task/Estimated Hours`
   - Impact: Medium (optional field, not breaking)
   - Action: Consider adding to enrichment queries

2. **Field Removed:**
   - Entity: Scrum/Feature
   - Field: `Feature/Kickoff Date`  
   - Impact: Low (field was not in our config)

**Action Required:**
1. Review schema changes (see: `./tmp/run_2025-10-07-14-30/schema_diff.json`)
2. Add configuration for Scrum/QA-Task
3. Update config to include new `Task/Estimated Hours` field (optional)
4. Re-run report to get updated context

### Configuration Health
- ✅ All configured entity types exist in workspace
- ✅ All configured fields are valid
- ⚠️ 2 new entity types detected in workspace (see above)

**Recommendation:**
Update configuration and re-run to improve coverage from 85% to 100%.

---
```

### 2.7 Appendix: Individual Reports

```markdown
## Appendix: Individual Reports

- [Alex Akilin](./toggl_data/alex.akilin@wearevolt.com/06_enriched_report.md)
- [Alexander Prozorov](./toggl_data/alexander.prozorov@wearevolt.com/06_enriched_report.md)
- [Anton Potapov](./toggl_data/anton.potapov@wearevolt.com/06_enriched_report.md)
...

---
```

---

## 3. Status Icons & Formatting

### Status Icons

Use consistent icons across reports:

| Icon | Meaning |
|------|---------|
| ✅ | Done / Complete / Success |
| 🔄 | In Progress |
| ⏳ | Planned / To Do |
| ⚠️ | Warning / Needs Attention |
| ❓ | Question / Unknown |
| ❌ | Error / Failed |
| 📋 | List / Open Items |
| 📊 | Statistics / Metrics |

### Emphasis

**Bold**: Entity names, field labels, important metrics  
*Italic*: Questions, hypothetical scenarios  
`Code`: Entity IDs, file paths, technical terms

### Sections

Use `---` horizontal rules to separate major sections for clarity.

---

## 4. Report Variants

### 4.1 Basic Report (No Fibery Enrichment)

When `--enrich-fibery` is NOT used, generate standard Toggl report:

```markdown
# Activity Report: Alex Akilin
**Email:** alex.akilin@wearevolt.com  
**Period:** 2025-09-29 to 2025-10-05  
**Generated:** 2025-10-07 14:30  
**Report Type:** Standard

## Matched Entities (53.2 hours)

### #7658 [Scrum] [Task] [Volt - Internal]
- **Time Spent:** 17.7 hours
- **Description:** Provisioned AWS Infrastructure in Huber AWS Org ID

### #7521 [Scrum] [Task] [Moneyball]
- **Time Spent:** 13.4 hours
- **Description:** Configured OpenSearch Alerts

...
```

### 4.2 Enriched Report (Fibery Enabled)

When `--enrich-fibery` is used, generate enhanced report with full context (see Section 1).

### 4.3 Full Analysis Report (Fibery + Analysis)

When both `--enrich-fibery` and `--fibery-analysis` are used, include all sections including work alignment (see Sections 1.6-1.7).

---

## 5. Intermediate Files Structure

### Per-User Directory Structure

```
./tmp/run_2025-10-07-14-30/toggl_data/alex.akilin@wearevolt.com/
├── 01_raw_toggl_report.md           # Base Toggl report
├── 02_entity_7658_raw.json          # Raw Fibery response
├── 03_entity_7658_summary.md        # LLM summary
├── 04_entity_7521_raw.json          # Raw Fibery response
├── 05_entity_7521_summary.md        # LLM summary
└── 06_enriched_report.md            # Final enriched report
```

### Analysis Directory Structure

```
./tmp/run_2025-10-07-14-30/fibery_analysis/alex.akilin@wearevolt.com/
├── entities_in_fibery.json          # All entities assigned to user
├── entities_in_toggl.json           # All entities logged in Toggl
├── discrepancies.json               # Structured discrepancy data
└── work_alignment.md                # Human-readable alignment report
```

---

## 6. Error Handling in Reports

### When Entity Fetch Fails

```markdown
### #7658 [Scrum] [Task] [Volt - Internal]
- **Time Spent:** 17.7 hours
- **Description:** Provisioned AWS Infrastructure in Huber AWS Org ID

⚠️ **Fibery Context:** Unable to fetch entity details (API error). 
Using basic information from Toggl only.
```

### When Entity Not Found in Fibery

```markdown
### #7999 [Scrum] [Task] [Unknown Project]
- **Time Spent:** 2.5 hours
- **Description:** Some work

⚠️ **Fibery Context:** Entity #7999 not found in Fibery. 
This may be a deleted entity or incorrect ID.
```

### When Entity Type Not Configured

```markdown
### #7890 [Scrum] [QA-Task] [Testing Project]
- **Time Spent:** 3.2 hours
- **Description:** Testing new features

⚠️ **Fibery Context:** Entity type "Scrum/QA-Task" is not yet configured.
Using generic context extraction (limited information available).

**Action Required:** Add configuration for this entity type to get full context.
See: docs/features/2-fibery-reports/PRD_Configuration.md
```

---

## 7. Output Files

### Generated Files Per Run

```
./tmp/run_2025-10-07-14-30/
├── toggl_data/                      # Per-user enriched data
│   ├── user1@example.com/
│   └── user2@example.com/
├── fibery_analysis/                 # Work alignment analysis
│   ├── user1@example.com/
│   └── user2@example.com/
├── combined_individual_reports.md   # All individual reports concatenated
├── team_summary_enriched.md         # Enhanced team summary
├── schema_diff.json                 # Schema changes (if detected)
└── run_log.log                      # Execution log
```

### File Naming Convention

- Individual reports: `06_enriched_report.md`
- Team summary: `team_summary_enriched.md`
- Combined reports: `combined_individual_reports.md`
- Raw data: `XX_entity_{public_id}_raw.json`
- Summaries: `XX_entity_{public_id}_summary.md`

---

## 8. Report Generation Logic

### Decision Tree

```
START
│
├─ Fibery enrichment enabled?
│  ├─ NO  → Generate basic Toggl report
│  └─ YES → Continue
│          │
│          ├─ For each entity ID:
│          │   ├─ Fetch entity from Fibery
│          │   ├─ Generate LLM summary
│          │   └─ Embed in report
│          │
│          ├─ Fibery analysis enabled?
│          │   ├─ NO  → Skip alignment section
│          │   └─ YES → Generate work alignment analysis
│          │
│          └─ Generate final enriched report
│
END
```

---

## 9. Analysis Reports (New)

These are standalone markdown files generated alongside main reports to provide configuration insights and recommendations.

### 9.1 Work Alignment Report

**File:** `work_alignment_YYYY-MM-DD.md`

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

## Actions Required

### High Priority
1. ✅ **Update Fibery states** for #7658, #7634 (completed work not marked done)
2. ✅ **Enable time tracking** for #7825 (work in progress but not logged)
```

---

### 9.2 Unknown Entities Report

**File:** `unknown_entities_YYYY-MM-DD.md`

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

**Recommendation:** Configure immediately (significant usage)

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
  prompt_template: "qa_task"
```

Create `./config/prompts/qa_task.txt`:
```
You are summarizing a QA Task entity from Fibery for a time tracking report.
Focus on: testing scope, results, and related features/bugs.

QA Task Data:
{entity_json}

Generate the summary:
```

---

### 2. Scrum/Sprint 📊 LOW PRIORITY

**Impact:**
- **Occurrences:** 1 entity
- **Time Logged:** 1.5 hours
- **Priority Score:** 17 (Low)

**Recommendation:** Monitor usage. Generic prompt may be sufficient.

---

## Coverage Impact

**Current Coverage:** 85% (38 of 45 entities configured)  
**If QA-Task configured:** 91% (41 of 45 entities)  
**Improvement:** +6%
```

---

### 9.3 Configuration Validation Report

**File:** `config_validation_YYYY-MM-DD.md`

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

---

### ⚠️ Field Validation

1 warning detected:

#### Warning: Field Not Found

**Entity Type:** Scrum/Task  
**Field:** `oldField`  
**Location:** `config/config.yaml` (entity_types → Scrum/Task → fields)

**Issue:** Configured field "oldField" does not exist in workspace schema.

**Recommendation:** Remove from configuration or update field name.

---

### 📊 Coverage Analysis

**Workspace entity types NOT in configuration:**

| Type | In Toggl Logs? | Recommendation |
|------|----------------|----------------|
| Scrum/QA-Task | ✅ Yes | Configure (active usage) |
| Scrum/Sprint | ❌ No | Optional (no recent usage) |

---

## Actions Required

### High Priority
1. ⚠️ **Remove or fix field:** Scrum/Task/oldField in configuration
2. ✅ **Add configuration:** Scrum/QA-Task (found in Toggl logs)
```

---

### 9.4 Report Directory Structure

All reports are generated together:

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
    └── unknown_entity_7890_sample.json
```

---

## 10. Template Variables

### Available Variables

Reports can use these template variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{user_name}` | User's display name | "Alex Akilin" |
| `{user_email}` | User's email | "alex.akilin@wearevolt.com" |
| `{period_start}` | Report start date | "2025-09-29" |
| `{period_end}` | Report end date | "2025-10-05" |
| `{generated_at}` | Generation timestamp | "2025-10-07 14:30" |
| `{total_hours}` | Total hours tracked | "58.1" |
| `{entity_count}` | Number of entities | "6" |
| `{run_id}` | Run identifier | "run_2025-10-07-14-30" |

---

## Related Documentation

- **[PRD_Core.md](./PRD_Core.md)** - Core requirements and functional specs
- **[PRD_Configuration.md](./PRD_Configuration.md)** - Configuration and prompts
- **[PRD_Schema_Management.md](./PRD_Schema_Management.md)** - Self-maintaining features
- **[PRD_Implementation.md](./PRD_Implementation.md)** - Implementation plan

---

**End of Report Formats Document**

