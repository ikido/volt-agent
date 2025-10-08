# Fibery Workspace Discovery - Summary

**Date:** October 7, 2025  
**Workspace:** wearevolt.fibery.io

---

## Key Findings

### Workspace Structure
- **Total Databases:** 20
- **Total Entity Types:** 177 (with public IDs)
- **Total Users:** 101 (with email addresses for Toggl matching)

### Main Databases

1. **Scrum** (52 entity types) - Primary development workflow
   - Scrum/Task, Scrum/Bug, Scrum/Sub-bug, Scrum/Feature
   - Scrum/Build, Scrum/Release, Scrum/Sprint, Scrum/Hotfix

2. **Product Management** (13 entity types) - User requests and feedback

3. **Design** (13 entity types) - Design features and work versions

4. **Test Cases** (12 entity types) - QA test management

5. **User Database** (4 entity types) - Team structure

### API Access Methods

We successfully validated **two methods** for accessing Fibery data:

#### Method 1: GraphQL API (Recommended) ✅
- **Endpoint:** `https://wearevolt.fibery.io/api/graphql/space/{database}`
- **Example:** `https://wearevolt.fibery.io/api/graphql/space/Scrum`
- **Advantages:**
  - Clean, intuitive syntax
  - Easy filtering by public ID
  - Type-safe queries
  - CamelCase field names (matches modern conventions)

**Example Query:**
```graphql
query getTask($searchId: String) {
  findTasks(publicId: {is: $searchId}) {
    id
    publicId
    name
    state { name }
    completionDate
    startedDate
    plannedEnd
    plannedStart
    feature {
      publicId
      name
    }
  }
}
```

**Variables:**
```json
{"searchId": "7658"}
```

#### Method 2: REST API (fibery.entity/query)
- **Endpoint:** `https://wearevolt.fibery.io/api/commands`
- **Complex syntax with q/from, q/select patterns**
- **Note:** More complex to use, GraphQL is preferred

### Sample Entity Retrieved

**Task #7658** (Successfully fetched via GraphQL):
```json
{
  "id": "9b19265e-beaa-4a72-8c0f-3334a3a6d50b",
  "publicId": "7658",
  "name": "Provision AWS Infrastructure in Huber AWS Org ID",
  "state": {"name": "In progress"},
  "completionDate": null,
  "startedDate": "2025-09-22T12:01:32.155Z",
  "plannedEnd": "2025-09-23",
  "plannedStart": "2025-09-20",
  "feature": {
    "publicId": "1575",
    "name": "Create AWS Infrastructure for Huber"
  }
}
```

### Field Naming Conventions

**Important:** Field names differ between storage and API:

| Schema/Storage | GraphQL API | Example |
|---------------|-------------|---------|
| `Scrum/Name` | `name` | Task name |
| `Scrum/Description` | `description` | Description (RichField) |
| `workflow/state` | `state` | State object |
| `Scrum/Completion Date` | `completionDate` | Completion date |
| `Scrum/Started Date` | `startedDate` | Start date |
| `Scrum/Planned End` | `plannedEnd` | Planned end |
| `Scrum/Planned Start` | `plannedStart` | Planned start |
| `Scrum/Feature` | `feature` | Feature relation |

**Key Insight:** GraphQL uses camelCase for field names!

### Entity Type Details

#### Scrum/Task (99 fields total)
**Essential Fields:**
- `publicId` - Public ID (matches Toggl references)
- `name` - Task name
- `description` - Rich text description
- `state` - Workflow state (object with `name`)
- `completionDate` - When completed
- `startedDate` - When started
- `plannedStart` - Planned start
- `plannedEnd` - Planned end

**Relations:**
- `feature` - Parent feature (Scrum/Feature)
- `requests` - Related requests (Product Management)

#### Scrum/Bug (81 fields)
Similar structure to Task with bug-specific fields

#### Scrum/Feature (91 fields)
**Date Fields:**
- `actualKickoffDate`
- `actualReleaseDate`
- `devActualStartDate`
- `devActualEndDate`
- `devPlannedStartDate`
- `devPlannedEndDate`

### Users

101 users available for matching with Toggl by email:
- Alex Akilin <alex.akilin@wearevolt.com>
- Alexander Prozorov <alexander.prozorov@wearevolt.com>
- Anton Potapov <anton.potapov@wearevolt.com>
- ... and 98 more

---

## Implementation Recommendations

### 1. Use GraphQL API for Entity Fetching
- Simpler syntax
- Better for filtering by public ID
- CamelCase fields are more developer-friendly

### 2. Entity Type Mapping

```yaml
entity_types:
  - database: "Scrum"
    graphql_type: "Task"
    storage_type: "Scrum/Task"
    query_function: "findTasks"
    fields:
      name: "name"
      description: "description"
      state: "state { name }"
      completion_date: "completionDate"
      started_date: "startedDate"
      planned_end: "plannedEnd"
      planned_start: "plannedStart"
      feature: "feature { publicId name }"
      
  - database: "Scrum"
    graphql_type: "Bug"
    storage_type: "Scrum/Bug"
    query_function: "findBugs"
    
  - database: "Scrum"
    graphql_type: "SubBug"  
    storage_type: "Scrum/Sub-bug"
    query_function: "findSubBugs"
    
  - database: "Scrum"
    graphql_type: "Feature"
    storage_type: "Scrum/Feature"
    query_function: "findFeatures"
```

### 3. Query Pattern for Integration

```python
# Parse Toggl entry: "#7658 [Scrum] [Task] [Volt - Internal]"
entity_id = "7658"
database = "Scrum"
entity_type = "Task"

# Build GraphQL query
query = '''
query getEntity($id: String) {
  findTasks(publicId: {is: $id}) {
    id
    publicId
    name
    description
    state { name }
    completionDate
    startedDate
    feature { publicId name }
  }
}
'''

# Execute
response = post(
    f"https://wearevolt.fibery.io/api/graphql/space/{database}",
    json={"query": query, "variables": {"id": entity_id}}
)
```

### 4. Description Field Handling

**Note:** The `description` field is a RichField type in Fibery. In GraphQL, it may not expose content directly. Options:
1. Query it as-is and handle the structure
2. Use the REST API if full rich text content is needed
3. Consider using entity summary from `name` + `state` if description isn't critical

---

## Files Generated

All documentation saved to: `/docs/features/2-fibery-reports/workspace-structure/`

1. **README.md** - Comprehensive workspace documentation
2. **full_schema.json** - Complete Fibery schema (52K lines)
3. **entity_types.json** - All 177 entity types with fields
4. **users.json** - All 101 users with emails
5. **main_types_detailed.json** - Detailed breakdown of Task/Bug/Sub-bug/Feature
6. **databases_summary.json** - Database summary
7. **sample_entity_task_7658.json** - Real task from your workspace
8. **integration_summary.json** - Integration recommendations

---

## Next Steps for PRD Update

1. Update API endpoints to use GraphQL (simpler)
2. Update field names to camelCase
3. Add database parameter to queries
4. Update configuration examples with real entity types
5. Add working query examples
6. Include user matching strategy
7. Document both GraphQL and REST API options

