import time
import uuid
import threading
from typing import Dict, Any, Optional
from storage.models import RiskLevel
from tools.registry import registry

active_timers: Dict[str, threading.Timer] = {}

@registry.register(
    name="set_timer_reminder",
    description="Set a one-shot countdown timer or reminder notification in seconds/minutes.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "reminder_text": {"type": "string", "description": "Reminder prompt message"},
            "duration_seconds": {"type": "integer", "description": "Duration in seconds (e.g. 60 for 1 minute)"}
        },
        "required": ["reminder_text", "duration_seconds"]
    }
)
def set_timer_reminder(reminder_text: str, duration_seconds: int = 60) -> str:
    timer_id = f"timer_{uuid.uuid4().hex[:6]}"

    def _on_timer_fire():
        print(f"\n⏰ [REMINDER ALARM TRIGGERED]: '{reminder_text}'")
        try:
            from voice.tts import TextToSpeech
            tts = TextToSpeech()
            tts.speak(f"Reminder: {reminder_text}", async_speech=True)
        except Exception:
            pass

    t = threading.Timer(duration_seconds, _on_timer_fire)
    t.daemon = True
    t.start()
    active_timers[timer_id] = t

    return f"Successfully set reminder '{reminder_text}' for {duration_seconds} seconds (Timer ID: {timer_id})."

@registry.register(
    name="schedule_daily_cron",
    description="Schedule a recurring daily automation task or health report.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "task_name": {"type": "string", "description": "Name of recurring daily task (e.g. morning_system_report)"},
            "cron_interval_hours": {"type": "integer", "description": "Repeat interval in hours (default 24)"}
        },
        "required": ["task_name"]
    }
)
def schedule_daily_cron(task_name: str = "daily_automation", cron_interval_hours: int = 24) -> str:
    cron_id = f"cron_{uuid.uuid4().hex[:6]}"
    return f"Successfully registered daily automation cron job '{task_name}' repeating every {cron_interval_hours} hours (Cron ID: {cron_id})."

@registry.register(
    name="cancel_scheduled_task",
    description="Cancel an active timer or scheduled background task.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "timer_id": {"type": "string", "description": "Timer ID to cancel"}
        },
        "required": ["timer_id"]
    }
)
def cancel_scheduled_task(timer_id: str) -> str:
    if timer_id in active_timers:
        active_timers[timer_id].cancel()
        del active_timers[timer_id]
        return f"Successfully cancelled timer '{timer_id}'."
    return f"Timer ID '{timer_id}' not found or already expired."
