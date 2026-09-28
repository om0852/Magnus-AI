import os
import asyncio
import tempfile
import tools
from storage.database import Database
from core.events.bus import EventBus
from approval.manager import ApprovalManager
from core.policy.engine import PolicyEngine
from nlp.inference.engine import InferenceEngine
from core.planner.planner import TaskPlanner
from core.tasks.machine import TaskStateMachine
from storage.models import TaskStatus

async def test_full_state_machine_flow():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = Database(db_path)
    bus = EventBus(db)
    appr_mgr = ApprovalManager(db)
    policy_engine = PolicyEngine(appr_mgr)
    nlp_engine = InferenceEngine()
    planner = TaskPlanner()

    machine = TaskStateMachine(
        db=db,
        event_bus=bus,
        nlp_engine=nlp_engine,
        planner=planner,
        policy_engine=policy_engine
    )

    # Process a safe low-risk command: "take screenshot"
    task = await machine.create_task("take screenshot")
    processed = await machine.process_task(task.task_id)

    assert processed.status == TaskStatus.COMPLETED
    assert processed.intent == "TAKE_SCREENSHOT"
    assert processed.output is not None
    assert "step_results" in processed.output

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
