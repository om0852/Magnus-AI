import os
import tempfile
import tools
from storage.database import Database
from approval.manager import ApprovalManager
from core.policy.engine import PolicyEngine
from storage.models import Task, RiskLevel, TicketStatus
from core.planner.planner import TaskPlanner

def test_policy_high_risk_gate():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = Database(db_path)
    approval_mgr = ApprovalManager(db)
    policy_engine = PolicyEngine(approval_mgr)
    planner = TaskPlanner()

    # Low risk task (open app)
    task_low = Task(task_id="t1", raw_prompt="open notepad", intent="OPEN_APP", entities={"application": "notepad"})
    planner.plan_task(task_low)
    allowed_low, ticket_low = policy_engine.check_execution_permission(task_low)
    assert allowed_low is True
    assert ticket_low is None

    # High risk task (delete file)
    task_high = Task(task_id="t2", raw_prompt="delete file temp.tmp", intent="DELETE_FILE", entities={"path": "temp.tmp"})
    planner.plan_task(task_high)
    allowed_high, ticket_high = policy_engine.check_execution_permission(task_high)
    assert allowed_high is False
    assert ticket_high is not None
    assert ticket_high.risk_level == RiskLevel.HIGH
    assert ticket_high.status == TicketStatus.PENDING

    # Approve ticket and re-check
    approval_mgr.approve_ticket(ticket_high.ticket_id)
    task_high.approval_ticket_id = ticket_high.ticket_id
    allowed_approved, _ = policy_engine.check_execution_permission(task_high)
    assert allowed_approved is True

    # Cleanup
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
