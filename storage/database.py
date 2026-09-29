import sqlite3
import json
import os
import time
from typing import List, Optional, Dict, Any
from storage.models import Task, ApprovalTicket, SystemEvent, AuditLog, TaskStatus, TicketStatus, RiskLevel, PlanStep

class Database:
    def __init__(self, db_path: str = None):
        if not db_path or db_path == "magnas.db":
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "storage", "magnas.db")
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def cleanup_stale_tasks(self):
        """Marks old orphan EXECUTING or WAITING_APPROVAL tasks as FAILED on server initialization."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'FAILED', error_message = 'Task interrupted by system restart or thread timeout.'
                    WHERE status IN ('EXECUTING', 'WAITING_APPROVAL', 'PARSING')
                """)
                conn.commit()
        except Exception as e:
            print(f"[Database Warning] Stale task cleanup: {e}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        return conn


    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    raw_prompt TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    confidence REAL,
                    status TEXT NOT NULL,
                    steps TEXT,
                    highest_risk TEXT,
                    approval_ticket_id TEXT,
                    error_message TEXT,
                    output TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)

            # Approval tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS approval_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_summary TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at REAL,
                    expires_at REAL
                )
            """)

            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    action TEXT NOT NULL,
                    resource_service TEXT NOT NULL,
                    permission_used TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp REAL
                )
            """)

            # System events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    task_id TEXT,
                    payload TEXT,
                    timestamp REAL
                )
            """)

            # Persistent memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at REAL
                )
            """)

            # Cron jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cron_jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    interval_minutes INTEGER DEFAULT 60,
                    status TEXT DEFAULT 'ACTIVE',
                    last_run REAL,
                    next_run REAL
                )
            """)

            # Self-Learned Rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_rules (
                    rule_id TEXT PRIMARY KEY,
                    pattern TEXT NOT NULL,
                    target_intent TEXT NOT NULL,
                    target_tool TEXT NOT NULL,
                    parameters TEXT,
                    created_at REAL
                )
            """)
            conn.commit()




    def save_task(self, task: Task):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks (
                    task_id, raw_prompt, intent, entities, confidence, status, steps,
                    highest_risk, approval_ticket_id, error_message, output, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                task.raw_prompt,
                task.intent,
                json.dumps(task.entities),
                task.confidence,
                task.status.value if isinstance(task.status, TaskStatus) else task.status,
                json.dumps([s.to_dict() for s in task.steps]),
                task.highest_risk.value if isinstance(task.highest_risk, RiskLevel) else task.highest_risk,
                task.approval_ticket_id,
                task.error_message,
                json.dumps(task.output) if task.output else None,
                task.created_at,
                task.updated_at
            ))
            conn.commit()

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_task(row)

    def list_tasks(self, limit: int = 50) -> List[Task]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [self._row_to_task(r) for r in rows]

    def save_approval_ticket(self, ticket: ApprovalTicket):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO approval_tickets (
                    ticket_id, task_id, action_type, target_summary, risk_level,
                    reason, status, details, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.ticket_id,
                ticket.task_id,
                ticket.action_type,
                ticket.target_summary,
                ticket.risk_level.value if isinstance(ticket.risk_level, RiskLevel) else ticket.risk_level,
                ticket.reason,
                ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
                json.dumps(ticket.details),
                ticket.created_at,
                ticket.expires_at
            ))
            conn.commit()

    def get_approval_ticket(self, ticket_id: str) -> Optional[ApprovalTicket]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approval_tickets WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_ticket(row)

    def list_pending_tickets(self) -> List[ApprovalTicket]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approval_tickets WHERE status = 'PENDING' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_ticket(r) for r in rows]

    def save_audit_log(self, audit: AuditLog):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (
                    log_id, task_id, action, resource_service, permission_used, risk_level, status, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit.log_id,
                audit.task_id,
                audit.action,
                audit.resource_service,
                audit.permission_used,
                audit.risk_level.value if isinstance(audit.risk_level, RiskLevel) else audit.risk_level,
                audit.status,
                json.dumps(audit.details),
                audit.timestamp
            ))
            conn.commit()

    def list_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                AuditLog(
                    log_id=r["log_id"],
                    task_id=r["task_id"],
                    action=r["action"],
                    resource_service=r["resource_service"],
                    permission_used=r["permission_used"],
                    risk_level=RiskLevel(r["risk_level"]) if r["risk_level"] else RiskLevel.LOW,
                    status=r["status"],
                    details=json.loads(r["details"]) if r["details"] else {},
                    timestamp=r["timestamp"]
                )
                for r in rows
            ]

    def save_event(self, event: SystemEvent):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (event_id, event_type, task_id, payload, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type,
                event.task_id,
                json.dumps(event.payload),
                event.timestamp
            ))
            conn.commit()

    def list_events(self, limit: int = 100) -> List[SystemEvent]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                SystemEvent(
                    event_id=r["event_id"],
                    event_type=r["event_type"],
                    task_id=r["task_id"],
                    payload=json.loads(r["payload"]) if r["payload"] else {},
                    timestamp=r["timestamp"]
                )
                for r in rows
            ]

    def save_memory(self, key: str, value: str, category: str = "general"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO memory_store (key, value, category, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, time.time()))
            conn.commit()

    def get_memory(self, key: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory_store WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return None
            return {"key": row["key"], "value": row["value"], "category": row["category"], "updated_at": row["updated_at"]}

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{query}%"
            cursor.execute("SELECT * FROM memory_store WHERE key LIKE ? OR value LIKE ? OR category LIKE ? ORDER BY updated_at DESC", (pattern, pattern, pattern))
            rows = cursor.fetchall()
            return [{"key": r["key"], "value": r["value"], "category": r["category"], "updated_at": r["updated_at"]} for r in rows]

    def save_cron_job(self, job_id: str, name: str, prompt: str, interval_minutes: int = 60, status: str = "ACTIVE"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = time.time()
            next_run = now + (interval_minutes * 60)
            cursor.execute("""
                INSERT OR REPLACE INTO cron_jobs (job_id, name, prompt, interval_minutes, status, last_run, next_run)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_id, name, prompt, interval_minutes, status, now, next_run))
            conn.commit()

    def list_cron_jobs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cron_jobs ORDER BY next_run ASC")
            rows = cursor.fetchall()
            return [{"job_id": r["job_id"], "name": r["name"], "prompt": r["prompt"], "interval_minutes": r["interval_minutes"], "status": r["status"], "last_run": r["last_run"], "next_run": r["next_run"]} for r in rows]

    def delete_cron_job(self, job_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cron_jobs WHERE job_id = ?", (job_id,))
            conn.commit()

    def save_learned_rule(self, rule_id: str, pattern: str, target_intent: str, target_tool: str, parameters: dict):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO learned_rules (rule_id, pattern, target_intent, target_tool, parameters, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule_id, pattern.lower().strip(), target_intent, target_tool, json.dumps(parameters), time.time()))
            conn.commit()

    def list_learned_rules(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learned_rules ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [{
                "rule_id": r["rule_id"],
                "pattern": r["pattern"],
                "target_intent": r["target_intent"],
                "target_tool": r["target_tool"],
                "parameters": json.loads(r["parameters"]) if r["parameters"] else {},
                "created_at": r["created_at"]
            } for r in rows]

    def delete_learned_rule(self, rule_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM learned_rules WHERE rule_id = ?", (rule_id,))
            conn.commit()



    def _row_to_task(self, row) -> Task:

        raw_steps = json.loads(row["steps"]) if row["steps"] else []
        steps = [
            PlanStep(
                step_id=s["step_id"],
                tool_name=s["tool_name"],
                parameters=s["parameters"],
                description=s["description"],
                risk_level=RiskLevel(s["risk_level"]),
                status=s["status"],
                result=s.get("result")
            )
            for s in raw_steps
        ]
        return Task(
            task_id=row["task_id"],
            raw_prompt=row["raw_prompt"],
            intent=row["intent"],
            entities=json.loads(row["entities"]) if row["entities"] else {},
            confidence=row["confidence"],
            status=TaskStatus(row["status"]),
            steps=steps,
            highest_risk=RiskLevel(row["highest_risk"]) if row["highest_risk"] else RiskLevel.LOW,
            approval_ticket_id=row["approval_ticket_id"],
            error_message=row["error_message"],
            output=json.loads(row["output"]) if row["output"] else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _row_to_ticket(self, row) -> ApprovalTicket:
        return ApprovalTicket(
            ticket_id=row["ticket_id"],
            task_id=row["task_id"],
            action_type=row["action_type"],
            target_summary=row["target_summary"],
            risk_level=RiskLevel(row["risk_level"]),
            reason=row["reason"],
            status=TicketStatus(row["status"]),
            details=json.loads(row["details"]) if row["details"] else {},
            created_at=row["created_at"],
            expires_at=row["expires_at"]
        )
