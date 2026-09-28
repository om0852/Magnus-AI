import os
import sqlite3
import json
import csv
import time
from typing import Dict, Any, Optional
from storage.models import RiskLevel
from tools.registry import registry

@registry.register(
    name="query_database",
    description="Inspect SQLite database tables, schema, or execute read queries on magnas.db or custom DB.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "db_path": {"type": "string", "description": "Database file path (default 'magnas.db')"},
            "query": {"type": "string", "description": "SQL query to execute (e.g., SELECT * FROM tasks LIMIT 10)"}
        },
        "required": []
    }
)
def query_database(db_path: str = "magnas.db", query: str = "SELECT name FROM sqlite_master WHERE type='table';") -> str:
    if not os.path.exists(db_path):
        return f"Database file '{db_path}' not found."

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"Query executed successfully on '{db_path}'. 0 rows returned."

        results = [dict(r) for r in rows[:20]]
        return f"Query returned {len(rows)} row(s) from '{db_path}':\n" + json.dumps(results, indent=2)
    except Exception as e:
        return f"[Database Error]: {e}"

@registry.register(
    name="export_data",
    description="Export database tables or JSON logs into CSV or Markdown format.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "table_name": {"type": "string", "description": "Table to export (e.g. tasks, audit_logs, approval_tickets)"},
            "output_format": {"type": "string", "description": "Export format: 'csv' or 'markdown'"}
        },
        "required": ["table_name"]
    }
)
def export_data(table_name: str = "audit_logs", output_format: str = "csv") -> str:
    db_path = "magnas.db"
    if not os.path.exists(db_path):
        return f"Database '{db_path}' not found."

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"No records found in table '{table_name}' to export."

        user_home = os.path.expanduser("~")
        desktop_dir = os.path.join(user_home, "Desktop")
        filename = f"Export_{table_name}_{int(time.time())}.{output_format}"
        out_path = os.path.join(desktop_dir, filename)

        dict_rows = [dict(r) for r in rows]

        if output_format.lower() == "csv":
            fieldnames = dict_rows[0].keys()
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dict_rows)
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# Export Table: {table_name}\n\n")
                for r in dict_rows:
                    f.write(f"- {r}\n")

        return f"Successfully exported {len(dict_rows)} records from '{table_name}' to '{out_path}'."
    except Exception as e:
        return f"[Export Error]: {e}"

@registry.register(
    name="backup_database",
    description="Create a timestamped backup copy of magnas.db database.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "db_path": {"type": "string", "description": "Target database file to backup"}
        },
        "required": []
    }
)
def backup_database(db_path: str = "magnas.db") -> str:
    if not os.path.exists(db_path):
        return f"Database '{db_path}' not found."

    import shutil
    backup_name = f"magnas_backup_{int(time.time())}.db"
    user_home = os.path.expanduser("~")
    backup_dir = os.path.join(user_home, "Documents", "MagnasBackups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, backup_name)

    shutil.copy(db_path, backup_path)
    return f"Successfully created database backup at '{backup_path}'."
