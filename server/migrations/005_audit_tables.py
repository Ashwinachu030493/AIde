"""
SQLite migration for audit persistence
Run this script to create audit tables
"""

import os
import sqlite3


def create_audit_tables():
    """Create audit persistence tables in SQLite"""

    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    db_path = os.path.join(root_dir, "aide.db")

    print(f"Migrating database at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create audit_runs_persistent table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_runs_persistent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        total_files INTEGER DEFAULT 0,
        files_with_issues INTEGER DEFAULT 0,
        total_issues INTEGER DEFAULT 0,
        critical_issues INTEGER DEFAULT 0,
        high_issues INTEGER DEFAULT 0,
        medium_issues INTEGER DEFAULT 0,
        low_issues INTEGER DEFAULT 0,
        health_score INTEGER DEFAULT 100,
        status TEXT DEFAULT 'completed',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        error_message TEXT
    )
    """)

    # Create audit_findings_persistent table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_findings_persistent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_run_id INTEGER,
        project_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        rule_id TEXT NOT NULL,
        line_number INTEGER,
        column_number INTEGER,
        message TEXT NOT NULL,
        snippet TEXT,
        severity TEXT NOT NULL,
        fix_suggestion TEXT,
        status TEXT DEFAULT 'open',
        audit_metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (audit_run_id) REFERENCES audit_runs_persistent(id)
    )
    """)

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_runs_p_project ON audit_runs_persistent(project_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_runs_p_status ON audit_runs_persistent(status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_findings_p_run ON audit_findings_persistent(audit_run_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_findings_p_file ON audit_findings_persistent(file_path)"
    )

    conn.commit()
    conn.close()

    print("✅ Audit tables created successfully (audit_runs_persistent, audit_findings_persistent)")


if __name__ == "__main__":
    create_audit_tables()
