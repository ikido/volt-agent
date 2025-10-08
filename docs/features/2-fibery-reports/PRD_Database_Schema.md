# PRD: Fibery Entity Context Integration - Database Schema

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** 📝 Planning  

> **📚 Part of:** [Fibery Entity Context Integration](./README.md)  
> **Related Docs:** [Core Requirements](./PRD_Core.md) | [Configuration](./PRD_Configuration.md)

---

## Overview

This document defines all database schema extensions required for the Fibery Entity Context Integration feature. These tables will be added to the existing `toggl_cache.db` database.

---

## Caching Strategy

Following the same pattern as Toggl data:

**CLI Argument:**
```bash
--use-cache    # Use cached Fibery data instead of fetching from API
```

**Behavior:**
- **Default (no flag):** Fetch fresh data from Fibery API and upsert to database
- **With `--use-cache`:** Use cached data from database, no API calls
- **Upsert Pattern:** New data always updates existing records (no duplicates)

**Use Cases:**
- ✅ Development: Use `--use-cache` to avoid API calls while testing report formats
- ✅ Production: Omit flag to get fresh data
- ✅ Experimentation: Cache data once, iterate on prompts/formatting without re-fetching

---

## Database Tables

### 1. fibery_entities

Stores fetched Fibery entities with core information and flexible metadata.

```sql
CREATE TABLE fibery_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fibery_id TEXT NOT NULL UNIQUE,  -- UUID from Fibery
    public_id TEXT NOT NULL,  -- Public ID like "7658"
    entity_type TEXT NOT NULL,  -- e.g., "Scrum/Task"
    entity_name TEXT NOT NULL,
    description_md TEXT,  -- Markdown description
    comments TEXT,  -- JSONB array of comment objects
    metadata TEXT NOT NULL,  -- JSONB object with entity-specific fields
    summary_md TEXT,  -- AI-generated summary (cached)
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fibery_entities_public_id ON fibery_entities(public_id);
CREATE INDEX idx_fibery_entities_type ON fibery_entities(entity_type);
CREATE INDEX idx_fibery_entities_fibery_id ON fibery_entities(fibery_id);
```

**Fields:**
- `fibery_id`: Internal UUID from Fibery API
- `public_id`: Human-readable ID shown in UI (e.g., "7658")
- `entity_type`: Full type name (e.g., "Scrum/Task")
- `entity_name`: Display name of the entity
- `description_md`: Markdown description (extracted from Fibery document)
- `comments`: JSONB array of comment objects (see structure below)
- `metadata`: JSONB object containing all fetched entity-specific fields (see structure below)
- `summary_md`: AI-generated summary in markdown (cached after first generation)

**Comments JSON Structure:**

Comments are stored as a nested tree structure to preserve threading:

```json
[
  {
    "id": "comment-uuid-1",
    "author_name": "John Doe",
    "author_email": "john@example.com",
    "body": "Implemented the user authentication logic...",
    "created_at": "2025-10-05T14:30:00+00:00",
    "replies": [
      {
        "id": "comment-uuid-2",
        "author_name": "Jane Smith",
        "author_email": "jane@example.com",
        "body": "Looks good! Just one question about the password hashing.",
        "created_at": "2025-10-05T15:15:00+00:00",
        "replies": [
          {
            "id": "comment-uuid-3",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "body": "Using bcrypt with salt rounds of 12.",
            "created_at": "2025-10-05T15:30:00+00:00",
            "replies": []
          }
        ]
      }
    ]
  },
  {
    "id": "comment-uuid-4",
    "author_name": "Mike Johnson",
    "author_email": "mike@example.com",
    "body": "Tested on staging - works perfectly!",
    "created_at": "2025-10-05T16:45:00+00:00",
    "replies": []
  }
]
```

**Structure:**
- Top-level array contains root comments
- Each comment has a `replies` array for nested comments
- Preserves comment threading/conversation structure
- `id` field for tracking individual comments

**Metadata JSON Structure:**

The `metadata` column stores everything we fetch except name, description, and comments:

```json
{
  "state": {
    "name": "In Progress",
    "color": "#FFA500"
  },
  "dates": {
    "completionDate": "2025-10-05T14:30:00Z",
    "startedDate": "2025-10-01T09:00:00Z",
    "plannedEnd": "2025-10-06"
  },
  "assignees": [
    {
      "fibery_id": "uuid-123",
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "relations": {
    "feature": {
      "publicId": "1575",
      "name": "User Authentication & Authorization"
    },
    "task": {
      "publicId": "7658",
      "name": "Parent task"
    }
  },
  "custom": {
    "severity": "High",
    "priority": "P1",
    "effort": 3.5
  }
}
```

**Why JSONB columns?**
- ✅ Different entity types have different fields - no schema changes needed
- ✅ Store raw fetched data without complex processing
- ✅ Easy to add new entity types
- ✅ Queryable with SQLite JSON functions (e.g., `json_extract(metadata, '$.state.name')`)
- ✅ Everything for an entity in one row - simple upserts
- ✅ Only fetch what we need, store it as-is

---

### 2. fibery_users

Stores Fibery users for resolving user IDs to emails (matches with Toggl and GitHub).

```sql
CREATE TABLE fibery_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fibery_id TEXT NOT NULL UNIQUE,  -- UUID from Fibery
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT,  -- User role in Fibery workspace (e.g., "Admin", "Member")
    is_active BOOLEAN DEFAULT 1,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fibery_users_email ON fibery_users(email);
CREATE INDEX idx_fibery_users_fibery_id ON fibery_users(fibery_id);
```

**Fields:**
- `fibery_id`: Internal Fibery user UUID
- `email`: User's email (primary key for matching)
- `name`: User's display name
- `role`: User's role in Fibery workspace
- `is_active`: Whether user is currently active
- `fetched_at`: When we first fetched this user
- `updated_at`: Last time we updated this user record

**Purpose:**
- Resolve Fibery user IDs to emails for matching with Toggl
- Future: Match with GitHub users for PR/commit context
- Always fetch all workspace users at the start of each run

**Fetching Strategy:**
- Fetch all users via REST API: `GET /api/workspaces/{workspaceId}/users`
- Upsert to this table (update if exists, insert if new)
- Used to resolve `assignedUser`, comment authors, etc.

---

## What About Analysis & Tracking?

All analysis, tracking, and validation is **output as markdown files**, not stored in the database:

### Generated Markdown Reports:

1. **Work Alignment Analysis**
   - Output: `work_alignment_YYYY-MM-DD.md`
   - Content: Discrepancies between Toggl and Fibery
   - Ephemeral: Generated fresh each run

2. **Unknown Entity Types**
   - Output: `unknown_entities_YYYY-MM-DD.md`
   - Content: Entity types not in config with usage stats
   - Ephemeral: Generated fresh each run

3. **Schema Validation**
   - Output: `config_validation_YYYY-MM-DD.md`
   - Content: Config issues, missing fields, recommendations
   - Ephemeral: Generated fresh each run

4. **Coverage Report**
   - Output: Part of team summary report
   - Content: Entity type coverage, configuration health
   - Ephemeral: Generated fresh each run

**Philosophy:** Keep the database simple - it's just a cache. All intelligence and analysis goes into the reports.

---

## Database Migration

### Migration Script

Add to `src/database/schema.sql`:

```sql
-- Fibery Integration Cache Tables
-- Simple cache for Fibery entities and users

-- Table 1: Fibery Entities Cache
CREATE TABLE fibery_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fibery_id TEXT NOT NULL UNIQUE,
    public_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    description_md TEXT,
    comments TEXT,  -- JSONB nested tree
    metadata TEXT NOT NULL,  -- JSONB
    summary_md TEXT,  -- AI-generated, cached
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fibery_entities_public_id ON fibery_entities(public_id);
CREATE INDEX idx_fibery_entities_type ON fibery_entities(entity_type);
CREATE INDEX idx_fibery_entities_fibery_id ON fibery_entities(fibery_id);

-- Table 2: Fibery Users Reference
CREATE TABLE fibery_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fibery_id TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT,
    is_active BOOLEAN DEFAULT 1,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fibery_users_email ON fibery_users(email);
CREATE INDEX idx_fibery_users_fibery_id ON fibery_users(fibery_id);
```

### Migration Process

1. **Backup existing database** before migration
2. **Run migration script** to add 2 new tables
3. **Verify table creation** with schema inspection
4. **Test with sample data** before production use

### Backwards Compatibility

- New tables are independent additions
- Existing Toggl functionality unaffected
- Can run without Fibery enrichment enabled
- Graceful degradation if tables don't exist

### Why So Simple?

We deliberately keep the database minimal:
- ✅ **Just caching** - entities and users
- ✅ **No complex tracking** - that goes in markdown reports
- ✅ **Easy to understand** - 2 tables, flat structure
- ✅ **Easy to maintain** - no foreign keys, no cascades
- ✅ **Fast upserts** - just update one row per entity

---

## Data Relationships

```
┌─────────────────┐
│ fibery_users    │  ← Reference table (fetched separately)
└─────────────────┘     Used to resolve user IDs in entity metadata
         

┌─────────────────┐
│ fibery_entities │  ← Main cache (flat, everything in one row)
└─────────────────┘     Includes:
                        - metadata (JSONB)
                        - comments (JSONB nested tree)
                        - summary_md (AI-generated, cached)

That's it! Just 2 tables.
```

**Design Philosophy:**
- ✅ **Dead simple** - just 2 cache tables
- ✅ **Flat structure** - everything for an entity in one row
- ✅ **JSONB columns** - flexible, schema-less storage
- ✅ **Easy upserts** - just update the entity row
- ✅ **AI summaries cached** - directly on entities
- ✅ **Users separate** - for reference lookups
- ✅ **Analysis in markdown** - not cluttering the database

---

## Data Retention

| Table | Retention Policy | Reason |
|-------|-----------------|---------|
| `fibery_entities` | 90 days | Cache for repeated queries |
| `fibery_users` | Keep indefinitely | User mapping reference |

**Note:** 
- Relations, comments, and AI summaries are stored in columns on `fibery_entities` - same 90-day retention
- All analysis reports (work alignment, unknown entities, schema validation) are markdown files - ephemeral, generated fresh each run

---

## Indexes Strategy

**Performance optimization:**
- Index on `public_id` for entity lookups (most common query)
- Index on `entity_type` for type-specific queries
- Index on `fibery_id` for uniqueness and lookups
- Index on `email` in users table for user resolution

**Common query patterns:**
```sql
-- Lookup entity by public ID
SELECT * FROM fibery_entities WHERE public_id = '7658';

-- Get entities by type
SELECT * FROM fibery_entities WHERE entity_type = 'Scrum/Task';

-- Get entity with summary
SELECT summary_md FROM fibery_entities WHERE public_id = '7658';

-- Resolve user by email
SELECT * FROM fibery_users WHERE email = 'john@example.com';

-- Extract from metadata (SQLite JSON functions)
SELECT json_extract(metadata, '$.state.name') 
FROM fibery_entities WHERE public_id = '7658';

-- Extract from nested comments
SELECT json_extract(comments, '$[0].body') 
FROM fibery_entities WHERE public_id = '7658';
```

---

## Related Documentation

- **[PRD_Core.md](./PRD_Core.md)** - Core requirements and functional specs
- **[PRD_Configuration.md](./PRD_Configuration.md)** - Configuration for entity types
- **[PRD_Schema_Management.md](./PRD_Schema_Management.md)** - How schema tracking works
- **[PRD_Implementation.md](./PRD_Implementation.md)** - Implementation plan

---

**End of Database Schema Document**

