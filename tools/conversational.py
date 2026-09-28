import time
from typing import Dict, Any
from tools.registry import registry
from storage.models import RiskLevel, TaskStatus
from voice.tts import TextToSpeech

tts_engine = TextToSpeech()

@registry.register(
    name="speak_response",
    description="Speaks a conversational text response aloud to the user using Text-to-Speech.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "The speech response to be spoken aloud."}
        },
        "required": ["message"]
    }
)
def speak_response(message: str) -> Dict[str, Any]:
    try:
        tts_engine.speak(message, async_speech=True)
        return {
            "success": True,
            "output": f"[Magnas Spoke]: {message}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to speak response: {str(e)}"
        }

@registry.register(
    name="get_task_progress",
    description="Queries the active or latest task state and speaks a clear human progress report out loud.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_task_progress() -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        
        if not db_ref:
            msg = "I am currently online and ready. No active database session."
            tts_engine.speak(msg, async_speech=True)
            return {"success": True, "output": msg}

        tasks = db_ref.list_tasks(limit=10)
        if not tasks:
            msg = "No tasks have been executed yet. All systems are operational and standing by for your command."
            tts_engine.speak(msg, async_speech=True)
            return {"success": True, "output": msg}

        # Check for active running task
        active_task = next((t for t in tasks if t.status in [TaskStatus.EXECUTING, TaskStatus.VERIFYING, TaskStatus.WAITING_APPROVAL, TaskStatus.PLANNED]), None)
        
        if active_task:
            steps = active_task.steps or []
            completed_steps = [s for s in steps if s.status == "COMPLETED"]
            current_step = next((s for s in steps if s.status == "RUNNING"), None)
            
            percent = int((len(completed_steps) / max(len(steps), 1)) * 100)
            
            if current_step:
                step_desc = current_step.description
            elif completed_steps:
                step_desc = f"Completed {len(completed_steps)} of {len(steps)} steps."
            else:
                step_desc = "Preparing execution plan."

            report = (
                f"Currently working on your task: '{active_task.raw_prompt}'. "
                f"Status is {active_task.status}. Progress is at {percent}%. "
                f"Current stage: {step_desc}."
            )
        else:
            last_task = tasks[0]
            status_text = "completed successfully" if last_task.status == TaskStatus.COMPLETED else f"ended with status {last_task.status}"
            report = (
                f"No task is currently running. Your last task was '{last_task.raw_prompt}', "
                f"which {status_text} and passed all verification checks."
            )

        tts_engine.speak(report, async_speech=True)
        return {
            "success": True,
            "output": report,
            "report": report
        }
    except Exception as e:
        err_msg = f"Unable to fetch progress: {str(e)}"
        tts_engine.speak("Sorry, I encountered an issue checking the task progress.", async_speech=True)
        return {
            "success": False,
            "error": err_msg
        }
