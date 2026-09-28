from typing import Tuple, Optional
from storage.models import Task, RiskLevel, TicketStatus, ApprovalTicket
from tools.registry import ToolRegistry, registry
from approval.manager import ApprovalManager

class PolicyEngine:
    """Enforces safety governance and human approval gates across tool executions."""

    def __init__(self, approval_manager: ApprovalManager, tool_registry: ToolRegistry = registry):
        self.approval_manager = approval_manager
        self.registry = tool_registry

    def evaluate_task_risk(self, task: Task) -> RiskLevel:
        highest_risk = RiskLevel.LOW
        for step in task.steps:
            tool = self.registry.get_tool(step.tool_name)
            tool_risk = tool.risk_level if tool else RiskLevel.MEDIUM
            step.risk_level = tool_risk
            
            if tool_risk == RiskLevel.HIGH:
                highest_risk = RiskLevel.HIGH
            elif tool_risk == RiskLevel.MEDIUM and highest_risk == RiskLevel.LOW:
                highest_risk = RiskLevel.MEDIUM
                
        task.highest_risk = highest_risk
        return highest_risk

    def check_execution_permission(self, task: Task) -> Tuple[bool, Optional[ApprovalTicket]]:
        highest_risk = self.evaluate_task_risk(task)

        if highest_risk == RiskLevel.LOW:
            return True, None

        if highest_risk == RiskLevel.MEDIUM:
            # Medium risk can proceed automatically or via ticket if required by config
            return True, None

        # HIGH risk MUST require human approval ticket
        if task.approval_ticket_id:
            ticket = self.approval_manager.db.get_approval_ticket(task.approval_ticket_id)
            if ticket and ticket.status == TicketStatus.APPROVED:
                return True, ticket

        # Create new pending approval ticket if none exists or not approved
        target_summary = ", ".join([f"{s.tool_name}({s.parameters})" for s in task.steps])
        ticket = self.approval_manager.create_ticket(
            task_id=task.task_id,
            action_type=task.intent or "MULTIPLE_ACTIONS",
            target_summary=target_summary[:200],
            risk_level=highest_risk,
            reason=f"Task contains HIGH-risk action requiring user confirmation: {task.raw_prompt}",
            details={"prompt": task.raw_prompt, "intent": task.intent}
        )
        task.approval_ticket_id = ticket.ticket_id
        return False, ticket
