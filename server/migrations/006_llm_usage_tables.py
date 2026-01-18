"""
SQLite migration for LLM usage tracking
"""

import os
import sqlite3


def create_llm_usage_tables():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aide.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Migrating database at: {db_path}")

    # Table: llm_usage_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS llm_usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider TEXT NOT NULL,              -- openai, anthropic, groq
        model TEXT NOT NULL,                 -- gpt-4, claude-3, etc.
        operation TEXT NOT NULL,             -- chat, code_gen, explanation
        prompt_tokens INTEGER DEFAULT 0,
        completion_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        estimated_cost_usd REAL DEFAULT 0.0,
        user_id TEXT DEFAULT 'local_user',   -- Single user for now
        project_id TEXT,                     -- Which project was this for?
        error_message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table: file_index_status
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_index_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,             -- Detect changes
        status TEXT NOT NULL,                -- indexed, pending, error
        chunks_count INTEGER DEFAULT 0,
        indexed_at TIMESTAMP,
        error_message TEXT,
        UNIQUE(project_id, file_path)
    )
    """)

    # Indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_logs(timestamp)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_usage_project ON llm_usage_logs(project_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_file_status_project ON file_index_status(project_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_file_status_path ON file_index_status(file_path)"
    )

    conn.commit()
    conn.close()

    print("✅ LLM usage and file status tables created")


if __name__ == "__main__":
    create_llm_usage_tables()
