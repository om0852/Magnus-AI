import time
import uuid
from typing import Dict, Any, List
from tools.registry import registry
from storage.models import RiskLevel

@registry.register(
    name="schedule_cron_job",
    description="Schedule a recurring background cron automation job with interval in minutes (e.g. daily backup, hourly system check, 30-min log digest).",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of recurring cron task"},
            "prompt": {"type": "string", "description": "Command prompt or intent to execute automatically"},
            "interval_minutes": {"type": "integer", "description": "Repeat interval in minutes (default 60 for hourly, 1440 for daily)"}
        },
        "required": ["name", "prompt"]
    }
)
def schedule_cron_job(name: str, prompt: str, interval_minutes: int = 60) -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        job_id = f"cron_{uuid.uuid4().hex[:6]}"
        if db_ref:
            db_ref.save_cron_job(job_id, name, prompt, interval_minutes)
            return {
                "success": True,
                "output": f"Successfully registered recurring cron job '{name}' (ID: {job_id}) repeating every {interval_minutes} minutes.",
                "job_id": job_id
            }
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="list_cron_jobs",
    description="List all active recurring background cron automation jobs.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_cron_jobs() -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            jobs = db_ref.list_cron_jobs()
            if jobs:
                formatted = "\n".join([f"- [{j['job_id']}] '{j['name']}': '{j['prompt']}' (Every {j['interval_minutes']} mins)" for j in jobs])
                return {"success": True, "output": f"Active Cron Jobs ({len(jobs)}):\n{formatted}", "jobs": jobs}
            return {"success": True, "output": "No recurring cron jobs active."}
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="delete_cron_job",
    description="Cancel and remove a recurring cron automation job by ID.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Cron Job ID to remove"}
        },
        "required": ["job_id"]
    }
)
def delete_cron_job(job_id: str) -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            db_ref.delete_cron_job(job_id)
            return {"success": True, "output": f"Successfully removed cron job '{job_id}'."}
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}
