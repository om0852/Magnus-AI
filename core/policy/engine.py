import os
import re
from typing import Tuple, Optional, Dict, Any
from storage.models import Task, RiskLevel, TicketStatus, ApprovalTicket
from tools.registry import ToolRegistry, registry
from approval.manager import ApprovalManager

DESTRUCTIVE_COMMAND_PATTERNS = [
    r"\brmdir\s+/[sS]\s+/[qQ]\s+[cC]:\\",
    r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\",
    r"\bformat\b",
    r"\bdiskpart\b",
    r"\breg\s+delete\b",
    r"\btakeown\b",
    r"\bicacls\b.*\bgrant\b",
    r"\brm\s+-rf\s+/[a-zA-Z0-9_\-\*]*",
    r"\bshutdown\s+/[rRsS]\s+/[fF]",
    r"\bdrop\s+database\b",
    r"\btruncate\s+table\b"
]

PROTECTED_SYSTEM_PATHS = [
    r"^[cC]:\\windows",
    r"^[cC]:\\program files",
    r"^[cC]:\\program files \(x86\)",
    r"^[cC]:\\system32",
    r"^[cC]:\\drivers",
    r"^/etc",
    r"^/bin",
    r"^/sbin",
    r"^/usr/bin"
]

DANGEROUS_DOWNLOAD_EXTENSIONS = [".exe", ".scr", ".bat", ".vbs", ".ps1", ".cmd", ".dll", ".sys", ".msi"]

class PolicyEngine:
    """Enforces zero-trust safety governance, system destruction prevention, & human approval gates."""

    def __init__(self, approval_manager: ApprovalManager, tool_registry: ToolRegistry = registry):
        self.approval_manager = approval_manager
        self.registry = tool_registry

    def validate_system_safety(self, task: Task) -> Tuple[bool, str]:
        """
        Hard Security Sandbox Check:
        Inspects step parameters for destructive commands, system path tampering, or dangerous downloads.
        """
        for step in task.steps:
            params_str = str(step.parameters).lower()

            # 1. Destructive Command Inspection
            for pattern in DESTRUCTIVE_COMMAND_PATTERNS:
                if re.search(pattern, params_str, re.IGNORECASE):
                    return False, f"SECURITY VIOLATION BLOCKED: Destructive command pattern detected: '{pattern}'"

            # 2. Protected System Path Tampering Check
            if step.tool_name in ["delete_file", "create_file", "execute_command"]:
                target_path = str(step.parameters.get("path") or step.parameters.get("command") or "").lower()
                for sys_path in PROTECTED_SYSTEM_PATHS:
                    if re.search(sys_path, target_path, re.IGNORECASE):
                        return False, f"SECURITY VIOLATION BLOCKED: Modification of protected system directory is prohibited: '{target_path}'"

            # 3. Dangerous Executable Download/Execution Check
            if step.tool_name in ["open_url", "browser_search", "execute_command"]:
                for ext in DANGEROUS_DOWNLOAD_EXTENSIONS:
                    if ext in params_str and "download" in params_str:
                        return False, f"SECURITY VIOLATION BLOCKED: Untrusted executable download attempt detected ('{ext}')"

        return True, "Safety check passed"

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
        # Hard Security Sandbox Check
        safe, safety_msg = self.validate_system_safety(task)
        if not safe:
            task.error_message = safety_msg
            raise PermissionError(safety_msg)

        highest_risk = self.evaluate_task_risk(task)

        if highest_risk == RiskLevel.LOW:
            return True, None

        if highest_risk == RiskLevel.MEDIUM:
            return True, None

        # HIGH risk MUST require explicit human approval ticket
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
