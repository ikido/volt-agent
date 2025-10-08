# Fibery Workspace Structure
**Workspace:** wearevolt.fibery.io  
**Generated:** 2025-10-07 13:11:21  
**Total Databases:** 20  
**Total Entity Types:** 177  
**Total Users:** 101

---

## Table of Contents
1. [Overview](#overview)
2. [Databases](#databases)
3. [Key Entity Types](#key-entity-types)
4. [Users](#users)
5. [Integration Notes](#integration-notes)

---

## Overview

This document describes the complete structure of the wearevolt Fibery workspace, including all databases, entity types, and their fields. This information is used for the Fibery-Toggl integration to enrich time tracking reports with contextual information.

### Statistics
- **20 Databases** organized by functional area
- **177 Entity Types** with public IDs that can be referenced in Toggl
- **101 Users** with email addresses for matching with Toggl

---

## Databases

### Database Summary

| Database | Entity Types | Description |
|----------|--------------|-------------|
| **Scrum** | 52 | Main development workflow (tasks, bugs, features, releases) |
| **workflow** | 24 | Workflow states for various entity types |
| **TargetProcess mapping** | 18 | Integration with TargetProcess project management |
| **Design** | 13 | Design features, work versions, and review processes |
| **Product Management** | 13 | User requests, feedback, and business value tracking |
| **Test Cases** | 12 | QA test cases, steps, and test execution |
| **vacations** | 8 | Vacation tracking, holidays, and time off |
| **Project management** | 7 | High-level project and space organization |
| **Retrospective** | 7 | Retrospective meetings, actions, and improvement tracking |
| **GitHub** | 5 | GitHub integration (branches, PRs, releases) |
| **User Database** | 4 | Team structure, departments, roles, and projects |
| **QA** | 3 | Quality assurance reports and test states |
| **Notes** | 2 | General notes and documentation |
| **highlights** | 2 | Highlighted items or important notes |
| **user** | 2 | User entity type |
| **LLM Eval** | 1 | LLM evaluation and testing |
| **Time tracker** | 1 | Time tracking entries |
| **To-dos** | 1 | Personal to-do items |
| **User metrics** | 1 | User performance and effort tracking |
| **comments** | 1 | Comments system |

---

## Databases Detail

### Scrum (52 entity types)

**Main Entity Types:**
- **Bug** (`Scrum/Bug`) - 81 fields
- **Build** (`Scrum/Build`) - 45 fields
- **Chore** (`Scrum/Chore`) - 22 fields
- **Commitment** (`Scrum/Commitment`) - 37 fields
- **Environment** (`Scrum/Environment`) - 14 fields
- **Epic** (`Scrum/Epic`) - 20 fields
- **Feature** (`Scrum/Feature`) - 91 fields
- **Hotfix** (`Scrum/Hotfix`) - 32 fields
- **On duty** (`Scrum/On duty`) - 12 fields
- **QA release effort** (`Scrum/QA release effort`) - 25 fields
- **Release** (`Scrum/Release`) - 26 fields
- **Sprint** (`Scrum/Sprint`) - 14 fields
- **Sub-bug** (`Scrum/Sub-bug`) - 22 fields
- **Sub-task** (`Scrum/Sub-task`) - 23 fields
- **Sub-task Template** (`Scrum/Sub-task Template`) - 11 fields
- **Task** (`Scrum/Task`) - 99 fields
- **Template** (`Scrum/Template`) - 19 fields
- **Test coverage** (`Scrum/Test coverage`) - 33 fields
- **Theme** (`Scrum/Theme`) - 21 fields

### Product Management (13 entity types)

**Main Entity Types:**
- **Business value** (`Product Management/Business value`) - 9 fields
- **Feedback** (`Product Management/Feedback`) - 16 fields
- **Request** (`Product Management/Request`) - 65 fields
- **Request report** (`Product Management/Request report`) - 11 fields

### Design (13 entity types)

**Main Entity Types:**
- **Design Epic** (`Design/Design Epic`) - 9 fields
- **Design Feature** (`Design/Design Feature`) - 55 fields
- **Old Work Version** (`Design/Old Work Version`) - 36 fields
- **Review Logs** (`Design/Review Logs`) - 13 fields
- **Screen set** (`Design/Screen set`) - 14 fields
- **Work Version** (`Design/Work Version`) - 49 fields

### Test Cases (12 entity types)

**Main Entity Types:**
- **Status** (`Test Cases/Status`) - 11 fields
- **Step** (`Test Cases/Step`) - 15 fields
- **Sub-step** (`Test Cases/Sub-step`) - 12 fields
- **Test case** (`Test Cases/Test case`) - 21 fields
- **Test case Priority** (`Test Cases/Test case Priority`) - 10 fields
- **Test case Status** (`Test Cases/Test case Status`) - 11 fields
- **Test feature** (`Test Cases/Test feature`) - 19 fields
- **Test run** (`Test Cases/Test run`) - 11 fields
- **Test run case** (`Test Cases/Test run case`) - 12 fields
- **Test run step** (`Test Cases/Test run step`) - 12 fields
- **Test run sub-step** (`Test Cases/Test run sub-step`) - 12 fields

### User Database (4 entity types)

**Main Entity Types:**
- **Departments** (`User Database/Departments`) - 9 fields
- **Project** (`User Database/Project`) - 10 fields
- **Role** (`User Database/Role`) - 9 fields
- **Team** (`User Database/Team`) - 11 fields

---

## Key Entity Types

These are the main entity types referenced in Toggl time entries:

### Task (`Scrum/Task`)

**Date Fields (12):**
- `fibery/creation-date`
- `fibery/modification-date`
- `Scrum/Completion Date`
- `Scrum/Deploy instruction updated`
- `Scrum/FeatureorRequest Planned End`
- `Scrum/Planned End`
- `Scrum/Planned Start`
- `Scrum/Planned date conflict`
- `Scrum/QA build Planned End`
- `Scrum/Review Planned End`
- `Scrum/Start Timer in Toggl`
- `Scrum/Started Date`

**Description Fields (1):**
- `Scrum/Description`

**State Fields (6):**
- `Scrum/Notion State`
- `Scrum/TC state`
- `Scrum/Test QA state`
- `Scrum/Test Stage state`
- `Scrum/Test coverage state`
- `workflow/state`

**Comment Fields (1):**
- `comments/comments`

---

### Bug (`Scrum/Bug`)

**Date Fields (11):**
- `fibery/creation-date`
- `fibery/modification-date`
- `Scrum/Completion Date`
- `Scrum/Deploy instruction updated`
- `Scrum/FeatureorRequest Planned End`
- `Scrum/Planned End`
- `Scrum/Planned Start`
- `Scrum/QA build planned end`
- `Scrum/Review Planned End`
- `Scrum/Start Timer in Toggl`
- `Scrum/Started Date`

**Description Fields (2):**
- `Scrum/Debugging result description`
- `Scrum/description`

**State Fields (5):**
- `Scrum/Test Prod state`
- `Scrum/Test QA state`
- `Scrum/Test Stage state`
- `Scrum/Test coverage state`
- `workflow/state`

**Comment Fields (1):**
- `comments/comments`

---

### Sub-bug (`Scrum/Sub-bug`)

**Date Fields (3):**
- `fibery/creation-date`
- `fibery/modification-date`
- `Scrum/Start Timer in Toggl`

**Description Fields (1):**
- `Scrum/Description`

**State Fields (1):**
- `workflow/state`

**Comment Fields (1):**
- `comments/comments`

---

### Feature (`Scrum/Feature`)

**Date Fields (21):**
- `fibery/creation-date`
- `fibery/modification-date`
- `Scrum/Action point update at`
- `Scrum/Actual Kick-off date`
- `Scrum/Actual Ready for dev date`
- `Scrum/Actual Release Date`
- `Scrum/Appetite updated at`
- `Scrum/Current weekly update`
- `Scrum/Dev Actual End Date`
- `Scrum/Dev Actual Start Date`
- `Scrum/Dev Planned End Date`
- `Scrum/Dev Planned Start Date`
- `Scrum/From Creation to Completion (Days)`
- `Scrum/Latest BA planned end`
- `Scrum/Max Actual Release Date of linked Releases`
- `Scrum/Max Planned Release Date of linked Releases`
- `Scrum/Planned Release Date`
- `Scrum/Release Planned Release Date`
- `Scrum/Release date probability`
- `Scrum/Start Timer in Toggl`
- `Scrum/Status update`

**Description Fields (1):**
- `Scrum/description`

**State Fields (6):**
- `Scrum/Analysis state`
- `Scrum/Design state`
- `Scrum/Dev state`
- `Scrum/Notion State`
- `Scrum/QA state`
- `workflow/state`

**Comment Fields (1):**
- `comments/comments`

---

## Users

Total users in workspace: **101**

WeAreVolt users: **95**

**Sample users (first 20):**
- Alex Ponomarev `<alex.ponomarev@wearevolt.com>`
- Ikidoit `<ikidoit@gmail.com>`
- Ksenia Svetlichnaya `<ksenia.svetlichnaya@wearevolt.com>`
- Dmitriy Legkov `<dmitriy.legkov@wearevolt.com>`
- Dmitry Nikiforov `<dmitri.nikiforov@wearevolt.com>`
- Ivan Kuzmin `<ivan.kuzmin@wearevolt.com>`
- Sergey Likhachev `<sergey.likhachev@wearevolt.com>`
- Roman Pogorelov `<roman.pogorelov@wearevolt.com>`
- Fibery bot `<no-reply@wearevolt.com>`
- Dmitriy Tulchinskiy `<dmitriy.tulchinskiy@wearevolt.com>`
- Alexander Prozorov `<alexander.prozorov@wearevolt.com>`
- Alexander Puchkov `<alexander.puchkov@wearevolt.com>`
- Olga Kuhach `<olga.kuhach@wearevolt.com>`
- Elia Dreytser `<elia.dreytser@wearevolt.com>`
- Vyacheslav Voytovich `<vyacheslav.voytovich@wearevolt.com>`
- Victor Zagorski `<victor.zagorski@wearevolt.com>`
- Dmitry Babenko `<dmitry.babenko@wearevolt.com>`
- Danila Migachev `<danila.migachev@wearevolt.com>`
- Nikita Luparev `<nikita.luparev@wearevolt.com>`
- David `<david@crossclear.com>`

... and 81 more users

---

## Integration Notes

### Entity ID Format
Entities in Toggl descriptions are referenced using the format: `#<public_id>`

Example from Toggl: `#7658 [Scrum] [Task] [Volt - Internal]`
- **Public ID:** 7658
- **Database:** Scrum
- **Type:** Task
- **Project:** Volt - Internal

### Matching Toggl to Fibery

**Entity Matching:**
1. Parse entity ID from Toggl description (e.g., `#7658`)
2. Parse entity type from brackets (e.g., `[Scrum] [Task]`)
3. Query Fibery API to fetch complete entity data
4. Extract description, comments, relations, and state

**User Matching:**
- Match by email address
- Toggl `user_email` field → Fibery `user/email` field
- 101 Fibery users available for matching

### Key Fields to Fetch

**For all entity types:**
- `fibery/id` - Internal UUID
- `fibery/public-id` - Public ID (matches Toggl reference)
- `fibery/creation-date` - When entity was created
- `fibery/modification-date` - Last modified date
- `{Type}/description` or `{Type}/Description` - Entity description (may be markdown)
- `workflow/state` - Current workflow state
- `comments/comments` - Comments collection
- `assignments/assignees` - Assigned users (if applicable)

**Date fields to check (in priority order):**
1. `Scrum/Completion Date` - Actual completion
2. `Scrum/Started Date` - When work started
3. `Scrum/Planned End` - Planned end date
4. `Scrum/Planned Start` - Planned start date
5. `fibery/creation-date` - Fallback to creation date

**Relations to fetch:**
- `Scrum/Feature` - Parent feature
- `Product Management/Requests` - Related user requests
- `Scrum/Bug` - Related bugs
- `Scrum/Pull Requests` - Related GitHub PRs

### Query Structure

To fetch a Scrum Task by public ID:
```json
{
  "command": "fibery.entity/query",
  "args": {
    "query": {
      "q/from": "Scrum/Task",
      "q/select": [
        "fibery/id",
        "fibery/public-id",
        "Scrum/name",
        "Scrum/Description",
        "workflow/state",
        "Scrum/Completion Date",
        "Scrum/Planned End",
        {
          "comments/comments": [
            "fibery/id",
            "comments/text"
          ]
        },
        {
          "Scrum/Feature": [
            "fibery/public-id",
            "Scrum/name"
          ]
        }
      ],
      "q/where": ["=", ["fibery/public-id"], "$id"],
      "q/limit": 1
    }
  },
  "params": {
    "$id": "7658"
  }
}
```

### Recommended Entity Types for Integration

Based on Toggl usage patterns, prioritize these entity types:

1. **Scrum/Task** - Most common (99 fields available)
2. **Scrum/Bug** - Bug fixes (81 fields)
3. **Scrum/Sub-bug** - Sub-bug items (22 fields)
4. **Scrum/Feature** - Features (91 fields)
5. **Scrum/Build** - Build/deployment tasks (45 fields)
6. **Product Management/Request** - User requests
7. **Test Cases/Test case** - QA test cases

### Files in This Directory

- **full_schema.json** - Complete Fibery schema (all types, fields, enums)
- **entity_types.json** - List of all 177 entity types with their fields
- **users.json** - All 101 users with emails and names
- **main_types_detailed.json** - Detailed field breakdown for Task, Bug, Sub-bug, Feature
- **databases_summary.json** - Summary of databases and entity counts

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
