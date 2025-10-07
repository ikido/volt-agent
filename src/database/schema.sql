-- Runs table: tracks each execution of the report generation
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    user_emails TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'in_progress', 'completed', 'failed'
    total_entries INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Raw time entries from Toggl API
CREATE TABLE IF NOT EXISTS toggl_time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    toggl_id INTEGER NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    workspace_id INTEGER NOT NULL,
    user_id INTEGER,  -- Nullable in case user data is missing
    username TEXT,
    user_email TEXT,
    description TEXT,
    start_time DATETIME,
    stop_time DATETIME,
    duration INTEGER DEFAULT 0,  -- in seconds
    tags TEXT,  -- JSON array
    project_id INTEGER,
    project_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- Processed entries with parsed metadata
CREATE TABLE IF NOT EXISTS processed_time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    description_clean TEXT NOT NULL,  -- Description without metadata
    entity_id TEXT,  -- e.g., "1112"
    entity_database TEXT,  -- e.g., "Scrum"
    entity_type TEXT,  -- e.g., "Sub-bug"
    project TEXT,  -- e.g., "Moneyball"
    is_matched BOOLEAN NOT NULL,  -- TRUE if entity ID was found
    total_duration INTEGER NOT NULL,  -- summed duration in seconds
    entry_count INTEGER NOT NULL,  -- number of raw entries aggregated
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id),
    UNIQUE(run_id, user_email, description_clean, entity_id, entity_database, entity_type, project)
);

-- Generated reports
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    report_type TEXT NOT NULL,  -- 'individual', 'team'
    user_email TEXT,  -- NULL for team reports
    content TEXT NOT NULL,  -- Markdown content
    file_path TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_toggl_time_entries_run_id ON toggl_time_entries(run_id);
CREATE INDEX IF NOT EXISTS idx_toggl_time_entries_toggl_id ON toggl_time_entries(toggl_id);
CREATE INDEX IF NOT EXISTS idx_toggl_time_entries_user_email ON toggl_time_entries(user_email);
CREATE INDEX IF NOT EXISTS idx_toggl_time_entries_start_time ON toggl_time_entries(start_time);
CREATE INDEX IF NOT EXISTS idx_processed_time_entries_run_id ON processed_time_entries(run_id);
CREATE INDEX IF NOT EXISTS idx_processed_time_entries_user_email ON processed_time_entries(user_email);
CREATE INDEX IF NOT EXISTS idx_processed_time_entries_entity_id ON processed_time_entries(entity_id);
CREATE INDEX IF NOT EXISTS idx_processed_time_entries_project ON processed_time_entries(project);
CREATE INDEX IF NOT EXISTS idx_processed_time_entries_is_matched ON processed_time_entries(is_matched);

