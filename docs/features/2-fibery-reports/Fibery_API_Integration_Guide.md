# Fibery API Integration Guide
**Workspace:** wearevolt.fibery.io  
**Last Updated:** October 7, 2025  
**For:** Toggl-Fibery Integration Project

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Methods](#api-methods)
4. [Entity Types](#entity-types)
5. [Query Examples](#query-examples)
6. [Field Mapping](#field-mapping)
7. [Best Practices](#best-practices)

---

## Overview

### Workspace Statistics
- **Total Databases:** 20
- **Total Entity Types:** 177 (with public IDs)
- **Total Users:** 101
- **Main Database:** Scrum (52 entity types)

### Key Databases

| Database | Entity Types | Purpose |
|----------|--------------|---------|
| **Scrum** | 52 | Main development workflow (Tasks, Bugs, Features, Releases) |
| **Product Management** | 13 | User requests, feedback, business value tracking |
| **Design** | 13 | Design features, work versions, review processes |
| **Test Cases** | 12 | QA test management and execution |
| **User Database** | 4 | Team structure, departments, roles |
| **GitHub** | 5 | GitHub integration (branches, PRs, releases) |
| **Time tracker** | 1 | Time tracking entries |
| **vacations** | 8 | Vacation and time-off tracking |

**Full workspace structure:** See `workspace-structure/README.md`

---

## Authentication

### API Token
```bash
# .env file
FIBERY_API_TOKEN=your_fibery_api_token_here
FIBERY_WORKSPACE_NAME=wearevolt
```

### Request Headers
```python
headers = {
    "Authorization": f"Token {FIBERY_API_TOKEN}",
    "Content-Type": "application/json"
}
```

---

## API Methods

### Method 1: GraphQL API (✅ Recommended)

**Why GraphQL?**
- Clean, intuitive syntax
- Easy filtering by public ID
- Type-safe queries
- CamelCase field names (modern conventions)
- Simpler to maintain

**Base Endpoint:**
```
https://wearevolt.fibery.io/api/graphql/space/{database}
```

**Examples:**
- Tasks/Bugs: `https://wearevolt.fibery.io/api/graphql/space/Scrum`
- Requests: `https://wearevolt.fibery.io/api/graphql/space/Product%20Management`

### Method 2: REST API (fibery.entity/query)

**Base Endpoint:**
```
https://wearevolt.fibery.io/api/commands
```

**Use When:**
- Need to query schema
- Need to get all users
- Need batch operations
- GraphQL doesn't support the operation

---

## Entity Types

### Scrum Database

#### Main Entity Types

| Entity Type | GraphQL Type | Query Function | Fields Count | Used in Toggl |
|-------------|--------------|----------------|--------------|---------------|
| Scrum/Task | `Task` | `findTasks` | 99 | ✅ Yes (#7658) |
| Scrum/Bug | `Bug` | `findBugs` | 81 | ✅ Yes |
| Scrum/Sub-bug | `SubBug` | `findSubBugs` | 22 | ✅ Yes |
| Scrum/Feature | `Feature` | `findFeatures` | 91 | ✅ Yes |
| Scrum/Build | `Build` | `findBuilds` | 45 | Yes |
| Scrum/Release | `Release` | `findReleases` | 26 | Yes |
| Scrum/Hotfix | `Hotfix` | `findHotfixes` | 32 | Yes |

#### Priority Entity Types for Integration

Based on Toggl usage patterns, focus on:
1. **Scrum/Task** (most common)
2. **Scrum/Bug** (bug fixes)
3. **Scrum/Sub-bug** (sub-items)
4. **Scrum/Feature** (high-level features)

---

## Query Examples

### GraphQL: Fetch Task by Public ID

```graphql
query getTask($searchId: String) {
  findTasks(publicId: {is: $searchId}) {
    id
    publicId
    name
    description
    state {
      name
    }
    completionDate
    startedDate
    plannedStart
    plannedEnd
    feature {
      id
      publicId
      name
    }
    requests {
      id
      publicId
      name
    }
  }
}
```

**Variables:**
```json
{
  "searchId": "7658"
}
```

**Python Example:**
```python
import requests

def fetch_task_by_id(task_id: str) -> dict:
    url = "https://wearevolt.fibery.io/api/graphql/space/Scrum"
    headers = {
        "Authorization": f"Token {FIBERY_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    query = """
    query getTask($searchId: String) {
      findTasks(publicId: {is: $searchId}) {
        id
        publicId
        name
        state { name }
        completionDate
        startedDate
        plannedEnd
        feature {
          publicId
          name
        }
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {"searchId": task_id}
    }
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if 'data' in result and 'findTasks' in result['data']:
        tasks = result['data']['findTasks']
        return tasks[0] if tasks else None
    
    return None
```

### GraphQL: Fetch Multiple Entity Types

```python
ENTITY_TYPE_MAPPING = {
    'Task': {
        'graphql_type': 'Task',
        'query_function': 'findTasks',
        'database': 'Scrum'
    },
    'Bug': {
        'graphql_type': 'Bug',
        'query_function': 'findBugs',
        'database': 'Scrum'
    },
    'Sub-bug': {
        'graphql_type': 'SubBug',
        'query_function': 'findSubBugs',
        'database': 'Scrum'
    },
    'Feature': {
        'graphql_type': 'Feature',
        'query_function': 'findFeatures',
        'database': 'Scrum'
    }
}

def fetch_entity(entity_type: str, public_id: str) -> dict:
    """Fetch any entity type by public ID"""
    mapping = ENTITY_TYPE_MAPPING.get(entity_type)
    if not mapping:
        return None
    
    url = f"https://wearevolt.fibery.io/api/graphql/space/{mapping['database']}"
    
    query = f"""
    query getEntity($searchId: String) {{
      {mapping['query_function']}(publicId: {{is: $searchId}}) {{
        id
        publicId
        name
        state {{ name }}
        completionDate
        startedDate
        plannedEnd
        plannedStart
      }}
    }}
    """
    
    # ... rest of implementation
```

### REST API: Get Users

```python
def get_fibery_users() -> list:
    """Get all users from Fibery"""
    url = "https://wearevolt.fibery.io/api/commands"
    headers = {
        "Authorization": f"Token {FIBERY_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "command": "fibery.entity/query",
        "args": {
            "query": {
                "q/from": "fibery/user",
                "q/select": [
                    "fibery/id",
                    "user/name",
                    "user/email"
                ],
                "q/limit": "q/no-limit"
            }
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if result.get('success'):
        return result.get('result', [])
    
    return []
```

### REST API: Get Schema

```python
def get_fibery_schema() -> dict:
    """Get complete Fibery schema"""
    url = "https://wearevolt.fibery.io/api/commands"
    headers = {
        "Authorization": f"Token {FIBERY_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "command": "fibery.schema/query",
        "args": {}
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

---

## Field Mapping

### Field Name Conventions

**Important:** Field names differ between schema storage and GraphQL API!

| Schema/Storage Name | GraphQL API Name | Type | Description |
|---------------------|------------------|------|-------------|
| `Scrum/Name` | `name` | String | Entity name |
| `Scrum/Description` | `description` | RichField | Description (rich text) |
| `workflow/state` | `state` | Object | Workflow state |
| `Scrum/Completion Date` | `completionDate` | DateTime | When completed |
| `Scrum/Started Date` | `startedDate` | DateTime | When started |
| `Scrum/Planned Start` | `plannedStart` | Date | Planned start date |
| `Scrum/Planned End` | `plannedEnd` | Date | Planned end date |
| `Scrum/Feature` | `feature` | Relation | Parent feature |
| `Product Management/Requests` | `requests` | Collection | Related requests |
| `comments/comments` | `comments` | Collection | Comments |
| `assignments/assignees` | `assignees` | Collection | Assigned users |

**Rule:** GraphQL uses **camelCase** for all field names.

### Common Fields Across Entity Types

All Scrum entities have:
- `id` - Internal UUID
- `publicId` - Public ID (matches Toggl references like #7658)
- `name` - Entity name
- `state` - Current workflow state
- `creationDate` - When created
- `modificationDate` - Last modified

### Date Fields by Entity Type

**Scrum/Task:**
```graphql
completionDate    # Actual completion
startedDate       # When work started
plannedStart      # Planned start
plannedEnd        # Planned end
```

**Scrum/Feature:**
```graphql
actualKickoffDate      # Actual kickoff
actualReleaseDate      # Actual release
devActualStartDate     # Dev started
devActualEndDate       # Dev completed
devPlannedStartDate    # Dev planned start
devPlannedEndDate      # Dev planned end
plannedReleaseDate     # Planned release
```

**Scrum/Bug:**
```graphql
completionDate    # Fixed date
startedDate       # Started fixing
plannedStart      # Planned start
plannedEnd        # Planned completion
```

### State Field Structure

```graphql
state {
  name  # e.g., "In progress", "Done", "To Do"
}
```

**Example response:**
```json
{
  "state": {
    "name": "In progress"
  }
}
```

### Relation Fields

**Single Relation (Feature):**
```graphql
feature {
  id
  publicId
  name
}
```

**Collection Relation (Requests):**
```graphql
requests {
  id
  publicId
  name
}
```

---

## Best Practices

### 1. Entity Fetching Strategy

```python
# Parse Toggl entry
# Input: "#7658 [Scrum] [Task] [Volt - Internal]"
entity_id = "7658"        # From #7658
database = "Scrum"        # From [Scrum]
entity_type = "Task"      # From [Task]

# Map to GraphQL
query_function = "findTasks"  # Based on entity_type
graphql_url = f"https://wearevolt.fibery.io/api/graphql/space/{database}"

# Fetch entity
entity = fetch_entity_graphql(graphql_url, query_function, entity_id)
```

### 2. Error Handling

```python
def fetch_entity_safe(entity_type: str, public_id: str) -> Optional[dict]:
    """Safely fetch entity with error handling"""
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code} fetching {entity_type} #{public_id}")
            return None
        
        result = response.json()
        
        # Check for GraphQL errors
        if 'errors' in result:
            for error in result['errors']:
                logger.error(f"GraphQL error: {error.get('message')}")
            return None
        
        # Extract entity
        if 'data' in result:
            query_function = ENTITY_TYPE_MAPPING[entity_type]['query_function']
            entities = result['data'].get(query_function, [])
            
            if entities:
                return entities[0]
            else:
                logger.warning(f"Entity {entity_type} #{public_id} not found")
                return None
        
        return None
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {entity_type} #{public_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {entity_type} #{public_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {entity_type} #{public_id}: {e}")
        return None
```

### 3. Caching Strategy

```python
# Cache schema and users (change infrequently)
SCHEMA_CACHE_TTL = 24 * 3600  # 24 hours
USER_CACHE_TTL = 24 * 3600    # 24 hours

# Cache entities (may be updated frequently)
ENTITY_CACHE_TTL = 3600       # 1 hour

# Cache by key: {entity_type}:{public_id}
cache_key = f"Scrum/Task:7658"
```

### 4. Batch Operations

```python
def fetch_entities_batch(entities: List[Tuple[str, str]]) -> Dict[str, dict]:
    """
    Fetch multiple entities efficiently
    
    Args:
        entities: List of (entity_type, public_id) tuples
    
    Returns:
        Dict mapping "entity_type:public_id" to entity data
    """
    results = {}
    
    # Group by entity type for efficient batching
    by_type = {}
    for entity_type, public_id in entities:
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(public_id)
    
    # Fetch each type
    for entity_type, ids in by_type.items():
        for public_id in ids:
            entity = fetch_entity(entity_type, public_id)
            if entity:
                key = f"{entity_type}:{public_id}"
                results[key] = entity
    
    return results
```

### 5. Rate Limiting

```python
import time
from collections import deque

class FiberyAPIClient:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_rpm = max_requests_per_minute
        self.request_times = deque()
    
    def wait_if_needed(self):
        """Implement rate limiting"""
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        
        # If at limit, wait
        if len(self.request_times) >= self.max_rpm:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(now)
```

### 6. User Matching with Toggl

```python
def match_fibery_toggl_users(fibery_users: List[dict], toggl_users: List[dict]) -> Dict[str, str]:
    """
    Match Fibery users with Toggl users by email
    
    Returns:
        Dict mapping toggl_email to fibery_id
    """
    fibery_by_email = {
        user['user/email']: user['fibery/id']
        for user in fibery_users
    }
    
    matches = {}
    for toggl_user in toggl_users:
        toggl_email = toggl_user['user_email']
        if toggl_email in fibery_by_email:
            matches[toggl_email] = fibery_by_email[toggl_email]
    
    return matches
```

---

## Sample Response Structure

### Task Entity Response

```json
{
  "data": {
    "findTasks": [
      {
        "id": "9b19265e-beaa-4a72-8c0f-3334a3a6d50b",
        "publicId": "7658",
        "name": "Provision AWS Infrastructure in Huber AWS Org ID",
        "state": {
          "name": "In progress"
        },
        "completionDate": null,
        "startedDate": "2025-09-22T12:01:32.155Z",
        "plannedStart": "2025-09-20",
        "plannedEnd": "2025-09-23",
        "feature": {
          "id": "6a64e340-9224-11f0-9ec4-978aaf70e48d",
          "publicId": "1575",
          "name": "Create AWS Infrastructure for Huber"
        }
      }
    ]
  }
}
```

---

## Configuration Template

```yaml
# config/config.yaml

fibery:
  api_base_url: "https://wearevolt.fibery.io"
  timeout_seconds: 30
  max_retries: 3
  retry_backoff_factor: 2.0
  
  # Use GraphQL API (recommended)
  use_graphql: true
  
  # Entity types to process
  entity_types:
    - storage_type: "Scrum/Task"
      graphql_type: "Task"
      query_function: "findTasks"
      database: "Scrum"
      display_name: "Task"
      
    - storage_type: "Scrum/Bug"
      graphql_type: "Bug"
      query_function: "findBugs"
      database: "Scrum"
      display_name: "Bug"
      
    - storage_type: "Scrum/Sub-bug"
      graphql_type: "SubBug"
      query_function: "findSubBugs"
      database: "Scrum"
      display_name: "Sub-bug"
      
    - storage_type: "Scrum/Feature"
      graphql_type: "Feature"
      query_function: "findFeatures"
      database: "Scrum"
      display_name: "Feature"
  
  # Caching
  cache:
    enabled: true
    schema_ttl_hours: 24
    entity_ttl_hours: 1
    user_ttl_hours: 24
```

---

## References

### Documentation Files
- **Full Workspace Structure:** `workspace-structure/README.md`
- **Discovery Summary:** `workspace-structure/DISCOVERY_SUMMARY.md`
- **Sample Entities:** `workspace-structure/sample_entity_*.json`
- **Complete Schema:** `workspace-structure/full_schema.json`
- **All Users:** `workspace-structure/users.json`

### External Resources
- **Fibery API Overview:** https://the.fibery.io/@public/User_Guide/Guide/Fibery-API-Overview-279
- **Fibery GraphQL:** Use via `/api/graphql/space/{database}` endpoint
- **Fibery Community:** https://community.fibery.io/

---

**Last Updated:** October 7, 2025

