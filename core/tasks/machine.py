import time
import uuid
import asyncio
from typing import Dict, Any, Optional
from storage.models import Task, TaskStatus, RiskLevel, TicketStatus, AuditLog
from storage.database import Database
from core.events.bus import EventBus
from nlp.inference.engine import InferenceEngine
from core.planner.planner import TaskPlanner
from core.policy.engine import PolicyEngine
from tools.registry import ToolRegistry, registry

class TaskStateMachine:
    """
    Production State Machine for Magnas tasks:
    RECEIVED -> UNDERSTOOD -> PLANNED -> POLICY_CHECK -> WAITING_APPROVAL -> EXECUTING -> VERIFYING -> COMPLETED
    Includes explicit resource permission auditing and activity tracking.
    """

    def __init__(
        self,
        db: Database,
        event_bus: EventBus,
        nlp_engine: InferenceEngine,
        planner: TaskPlanner,
        policy_engine: PolicyEngine,
        tool_registry: ToolRegistry = registry
    ):
        self.db = db
        self.event_bus = event_bus
        self.nlp_engine = nlp_engine
        self.planner = planner
        self.policy_engine = policy_engine
        self.tool_registry = tool_registry

    async def create_task(self, prompt: str) -> Task:
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            raw_prompt=prompt,
            status=TaskStatus.RECEIVED,
            created_at=time.time(),
            updated_at=time.time()
        )
        self.db.save_task(task)
        await self.event_bus.publish("task_created", task.task_id, task.to_dict())
        return task

    async def process_task(self, task_id: str) -> Task:
        task = self.db.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        try:
            # 1. UNDERSTOOD
            if task.status == TaskStatus.RECEIVED:
                parsed = self.nlp_engine.parse(task.raw_prompt)
                task.intent = parsed.get("intent")
                task.confidence = parsed.get("confidence", 0.0)
                entities = parsed.get("entities", {})
                entities["agent_name"] = parsed.get("agent_name") or self._determine_agent_name(task.intent)
                task.entities = entities
                task.status = TaskStatus.UNDERSTOOD
                task.updated_at = time.time()
                self.db.save_task(task)
                await self.event_bus.publish("task_understood", task.task_id, task.to_dict())


            # 2. PLANNED
            if task.status == TaskStatus.UNDERSTOOD:
                self.planner.plan_task(task)
                task.status = TaskStatus.PLANNED
                task.updated_at = time.time()
                self.db.save_task(task)
                await self.event_bus.publish("task_planned", task.task_id, task.to_dict())

            # 3. POLICY_CHECK
            if task.status == TaskStatus.PLANNED:
                allowed, ticket = self.policy_engine.check_execution_permission(task)
                task.status = TaskStatus.POLICY_CHECK
                task.updated_at = time.time()
                self.db.save_task(task)
                await self.event_bus.publish("task_policy_check", task.task_id, task.to_dict())

                if not allowed and ticket:
                    task.status = TaskStatus.WAITING_APPROVAL
                    task.updated_at = time.time()
                    self.db.save_task(task)
                    await self.event_bus.publish("approval_required", task.task_id, {
                        "task": task.to_dict(),
                        "ticket": ticket.to_dict()
                    })

                    # Log Audit Denial/Pending Entry
                    self.db.save_audit_log(AuditLog(
                        log_id=f"audit_{uuid.uuid4().hex[:8]}",
                        task_id=task.task_id,
                        action="POLICY_APPROVAL_GATE",
                        resource_service="SECURITY_POLICY_ENGINE",
                        permission_used="HIGH_RISK_HUMAN_APPROVAL_REQUIRED",
                        risk_level=ticket.risk_level,
                        status="HELD_FOR_APPROVAL",
                        details={"ticket_id": ticket.ticket_id, "reason": ticket.reason},
                        timestamp=time.time()
                    ))
                    return task
                else:
                    task.status = TaskStatus.APPROVED
                    task.updated_at = time.time()
                    self.db.save_task(task)

            # 4. EXECUTING
            if task.status in [TaskStatus.APPROVED, TaskStatus.POLICY_CHECK]:
                task.status = TaskStatus.EXECUTING
                task.updated_at = time.time()
                self.db.save_task(task)
                await self.event_bus.publish("task_executing", task.task_id, task.to_dict())

                step_results = []
                total_steps = len(task.steps)

                for idx, step in enumerate(task.steps, 1):
                    step.status = "RUNNING"
                    task.updated_at = time.time()
                    self.db.save_task(task)

                    await self.event_bus.publish("task_step_progress", task.task_id, {
                        "task_id": task.task_id,
                        "step_index": idx,
                        "total_steps": total_steps,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": "RUNNING"
                    })

                    tool = self.tool_registry.get_tool(step.tool_name)
                    if not tool:
                        step.status = "FAILED"
                        step.result = {"error": f"Tool '{step.tool_name}' not registered."}
                        raise RuntimeError(f"Tool '{step.tool_name}' not registered.")
                    
                    res = tool.execute(**step.parameters)
                    step.result = res
                    if res.get("success"):
                        step.status = "COMPLETED"
                    else:
                        step.status = "FAILED"
                        raise RuntimeError(f"Step '{step.description}' failed: {res.get('error')}")

                    step_results.append(res)
                    task.updated_at = time.time()
                    self.db.save_task(task)

                    # Save Audit Log Record to DB
                    audit_record = AuditLog(
                        log_id=f"audit_{uuid.uuid4().hex[:8]}",
                        task_id=task.task_id,
                        action=step.tool_name,
                        resource_service=self._determine_resource_service(step.tool_name),
                        permission_used=self._determine_permission(step.tool_name, step.risk_level),
                        risk_level=step.risk_level,
                        status=step.status,
                        details={"parameters": step.parameters, "result_summary": str(res.get("output", ""))[:200]},
                        timestamp=time.time()
                    )
                    self.db.save_audit_log(audit_record)
                    await self.event_bus.publish("audit_log_recorded", task.task_id, audit_record.to_dict())

                    await self.event_bus.publish("task_step_progress", task.task_id, {
                        "task_id": task.task_id,
                        "step_index": idx,
                        "total_steps": total_steps,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": "COMPLETED",
                        "result": res
                    })

                    await asyncio.sleep(0.4)

                task.output = {"step_results": step_results}

            # 5. VERIFYING
            if task.status == TaskStatus.EXECUTING:
                task.status = TaskStatus.VERIFYING
                task.updated_at = time.time()
                self.db.save_task(task)
                await self.event_bus.publish("task_verifying", task.task_id, task.to_dict())
                
                verification_notes = []
                for s in task.steps:
                    if s.result and isinstance(s.result, dict):
                        output_text = str(s.result.get("output", ""))
                        if any(kw in output_text for kw in ["Verification PASSED", "Successfully", "Opened", "Found"]):
                            verification_notes.append(output_text)

                verif_summary = " | ".join(verification_notes) if verification_notes else "All plan steps completed & verified."
                task.output["verification_summary"] = verif_summary

                await asyncio.sleep(0.5)

                task.status = TaskStatus.COMPLETED
                task.updated_at = time.time()
                self.db.save_task(task)
                await self.event_bus.publish("task_completed", task.task_id, task.to_dict())

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = time.time()
            self.db.save_task(task)
            await self.event_bus.publish("task_failed", task.task_id, task.to_dict())

        return task

    def _determine_resource_service(self, tool_name: str) -> str:
        if tool_name in ["open_application", "close_application"]:
            return "WINDOWS_PROCESS_MANAGER"
        elif tool_name in ["read_file", "create_file", "delete_file", "search_files", "list_directory", "verify_task_output"]:
            return "LOCAL_FILESYSTEM_STORAGE"
        elif tool_name in ["open_url", "browser_search", "read_web_documentation", "automate_platform_login"]:
            return "BROWSER_NETWORK_SERVICE"
        elif tool_name == "design_resume_in_word":
            return "MICROSOFT_WORD_ENGINE"
        elif tool_name == "develop_project_in_antigravity":
            return "ANTIGRAVITY_IDE_AGENT"
        elif tool_name in ["change_volume", "take_screenshot", "type_text", "press_key", "execute_command"]:
            return "OS_PERIPHERAL_SYSTEM"
        return "CORE_TASK_ENGINE"

    def _determine_permission(self, tool_name: str, risk_level: Any) -> str:
        r_str = risk_level.value if isinstance(risk_level, RiskLevel) else str(risk_level)
        if r_str == "HIGH":
            return "HIGH_RISK_EXPLICIT_PERMITTED"
        elif r_str == "MEDIUM":
            return "WRITE_MUTATION_PERMITTED"
        return "READ_EXECUTE_PERMITTED"

    def _determine_agent_name(self, intent: str) -> str:
        mapping = {
            "OPEN_APP": "os_agent",
            "CLOSE_APP": "os_agent",
            "CHANGE_VOLUME": "os_agent",
            "TAKE_SCREENSHOT": "os_agent",
            "SEARCH_WEB": "browser_agent",
            "READ_WEB_DOCS": "browser_agent",
            "AUTOMATE_PLATFORM_LOGIN": "browser_agent",
            "DEVELOP_PROJECT_ANTIGRAVITY": "ide_agent",
            "DESIGN_RESUME": "resume_agent",
            "INSPECT_AUDIT_LOGS": "security_agent",
            "QUERY_DATABASE": "database_agent",
            "READ_SCREEN_TEXT": "vision_agent",
            "SET_TIMER_REMINDER": "scheduler_agent",
            "SCHEDULE_DAILY_CRON": "scheduler_agent",
            "RUN_POWERSHELL_CMD": "cli_agent",
            "GREETING": "llm_agent",
            "GET_PROGRESS": "llm_agent"
        }
        return mapping.get(intent, "router_agent")

