import os
import json
import asyncio
from typing import List, Optional
from storage.database import Database
from core.events.bus import EventBus
from approval.manager import ApprovalManager
from core.tasks.machine import TaskStateMachine
from tools.registry import registry
from storage.models import TicketStatus, TaskStatus
from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from voice.wake_word import WakeWordListener

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# Global dependencies references
db_ref: Database = None
event_bus_ref: EventBus = None
approval_mgr_ref: ApprovalManager = None
task_machine_ref: TaskStateMachine = None
ws_connections: List = []
stt_engine = SpeechToText()
tts_engine = TextToSpeech()
wake_word_listener: Optional[WakeWordListener] = None

class CommandRequest(BaseModel):
    prompt: str

class SpeakRequest(BaseModel):
    text: str

class LearnRuleRequest(BaseModel):
    pattern: str
    target_intent: str
    target_tool: str
    parameters: Optional[dict] = None

class FixIssueRequest(BaseModel):
    prompt: str
    error_message: Optional[str] = ""
    corrected_intent: str
    target_tool: str
    parameters: Optional[dict] = None

if HAS_FASTAPI:
    app = FastAPI(title="Magnas Control Center API", version="0.2.0")

    @app.get("/api/status")
    def get_system_status():
        pending_tickets = db_ref.list_pending_tickets() if db_ref else []
        recent_tasks = db_ref.list_tasks(limit=10) if db_ref else []
        running_tasks = [t for t in recent_tasks if t.status in [TaskStatus.EXECUTING, TaskStatus.WAITING_APPROVAL]]
        wake_active = wake_word_listener.is_running if wake_word_listener else False
        return {
            "status": "ONLINE",
            "pending_approvals": len(pending_tickets),
            "running_tasks": len(running_tasks),
            "total_tools": len(registry.list_tools()),
            "wake_word_active": wake_active,
            "mic_available": stt_engine.is_microphone_available()
        }

    @app.get("/api/tasks")
    def list_tasks(limit: int = 50):
        tasks = db_ref.list_tasks(limit=limit) if db_ref else []
        return [t.to_dict() for t in tasks]

    @app.post("/api/tasks")
    async def submit_task(req: CommandRequest):
        if not task_machine_ref:
            raise HTTPException(status_code=500, detail="Task machine not initialized")
        
        # Check if prompt contains wake word and clean it up
        cleaned_prompt = req.prompt
        if wake_word_listener:
            cleaned_prompt = wake_word_listener.process_text_for_wake_word(req.prompt)

        task = await task_machine_ref.create_task(cleaned_prompt)
        asyncio.create_task(task_machine_ref.process_task(task.task_id))
        return task.to_dict()

    @app.get("/api/approvals")
    def list_approvals():
        tickets = db_ref.list_pending_tickets() if db_ref else []
        return [t.to_dict() for t in tickets]

    @app.post("/api/approvals/{ticket_id}/approve")
    async def approve_ticket(ticket_id: str):
        ticket = approval_mgr_ref.approve_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        task = db_ref.get_task(ticket.task_id)
        if task:
            task.status = TaskStatus.APPROVED
            db_ref.save_task(task)
            asyncio.create_task(task_machine_ref.process_task(task.task_id))

        await event_bus_ref.publish("approval_granted", ticket.task_id, {"ticket": ticket.to_dict()})
        return {"success": True, "ticket": ticket.to_dict()}

    @app.post("/api/approvals/{ticket_id}/reject")
    async def reject_ticket(ticket_id: str):
        ticket = approval_mgr_ref.reject_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        task = db_ref.get_task(ticket.task_id)
        if task:
            task.status = TaskStatus.REJECTED
            task.error_message = "Task rejected by human approval gate."
            db_ref.save_task(task)

        await event_bus_ref.publish("approval_rejected", ticket.task_id, {"ticket": ticket.to_dict()})
        return {"success": True, "ticket": ticket.to_dict()}

    @app.get("/api/tools")
    def list_tools():
        return registry.list_tools()

    @app.get("/api/audit-logs")
    def list_audit_logs(limit: int = 100):
        logs = db_ref.list_audit_logs(limit=limit) if db_ref else []
        return [l.to_dict() for l in logs]

    # Voice APIs
    @app.post("/api/voice/listen")
    async def listen_voice_command():
        text = stt_engine.listen_microphone(timeout=5)
        if not text:
            return {"success": False, "message": "No speech detected or microphone error."}

        cleaned = wake_word_listener.process_text_for_wake_word(text) if wake_word_listener else text
        if task_machine_ref:
            task = await task_machine_ref.create_task(cleaned)
            asyncio.create_task(task_machine_ref.process_task(task.task_id))
            return {"success": True, "transcript": text, "task": task.to_dict()}
        return {"success": True, "transcript": text}

    @app.post("/api/voice/speak")
    def speak_text(req: SpeakRequest):
        tts_engine.speak(req.text, async_speech=True)
        return {"success": True, "text": req.text}

    @app.post("/api/voice/wakeword/toggle")
    def toggle_wake_word(active: Optional[bool] = None):
        global wake_word_listener
        if not wake_word_listener:
            return {"success": False, "active": False}
        
        if active is None:
            active = not wake_word_listener.is_running

        if active:
            wake_word_listener.start()
        else:
            wake_word_listener.stop()

        return {"success": True, "active": wake_word_listener.is_running}

    # Self-Learning & Issue Correction APIs
    @app.get("/api/self-learning/rules")
    def list_self_learning_rules():
        from core.memory.self_learning import self_learning_engine
        db = self_learning_engine._get_db()
        rules = db.list_learned_rules() if db else []
        return {"success": True, "rules": rules}

    @app.post("/api/self-learning/learn")
    def create_self_learning_rule(req: LearnRuleRequest):
        from core.memory.self_learning import self_learning_engine
        res = self_learning_engine.learn_correction(req.pattern, req.target_intent, req.target_tool, req.parameters or {})
        return {"success": True, "output": res}

    @app.delete("/api/self-learning/rules/{rule_id}")
    def delete_self_learning_rule(rule_id: str):
        from core.memory.self_learning import self_learning_engine
        res = self_learning_engine.forget_rule(rule_id)
        return {"success": True, "output": res}

    @app.post("/api/self-learning/fix-issue")
    def fix_issue_and_learn(req: FixIssueRequest):
        from core.memory.self_learning import self_learning_engine
        res = self_learning_engine.auto_fix_and_learn_failure(
            req.prompt, req.error_message or "", req.corrected_intent, req.target_tool, req.parameters or {}
        )
        return {"success": True, "output": res}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        ws_connections.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("action") == "submit_command":
                    prompt = msg.get("prompt")
                    if prompt and task_machine_ref:
                        cleaned = wake_word_listener.process_text_for_wake_word(prompt) if wake_word_listener else prompt
                        task = await task_machine_ref.create_task(cleaned)
                        asyncio.create_task(task_machine_ref.process_task(task.task_id))
                elif msg.get("action") == "speak":
                    text = msg.get("text")
                    if text:
                        tts_engine.speak(text, async_speech=True)
        except WebSocketDisconnect:
            if websocket in ws_connections:
                ws_connections.remove(websocket)

    static_path = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_path):
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    app = None

def _on_wake_word_command(cmd: str):
    print(f"[Daemon] Received wake word command: '{cmd}'")
    if task_machine_ref and cmd:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.run_until_complete(task_machine_ref.create_task(cmd))
        loop.run_until_complete(task_machine_ref.process_task(task.task_id))
        loop.close()

def init_web_server(db: Database, event_bus: EventBus, approval_mgr: ApprovalManager, task_machine: TaskStateMachine):
    global db_ref, event_bus_ref, approval_mgr_ref, task_machine_ref, wake_word_listener
    db_ref = db
    event_bus_ref = event_bus
    approval_mgr_ref = approval_mgr
    task_machine_ref = task_machine

    wake_word_listener = WakeWordListener(on_command_callback=_on_wake_word_command)
    # Start wake word listener by default
    wake_word_listener.start()

    async def on_event(event):
        for ws in list(ws_connections):
            try:
                await ws.send_json({"type": "event", "event": event.to_dict()})
            except Exception:
                pass

    event_bus.subscribe(on_event)
