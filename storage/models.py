from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum
import time
import uuid

class TaskStatus(str, Enum):
    RECEIVED = "RECEIVED"
    UNDERSTOOD = "UNDERSTOOD"
    PLANNED = "PLANNED"
    POLICY_CHECK = "POLICY_CHECK"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TicketStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

@dataclass
class PlanStep:
    step_id: str
    tool_name: str
    parameters: Dict[str, Any]
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    status: str = "PENDING"
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "description": self.description,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else self.risk_level,
            "status": self.status,
            "result": self.result
        }

@dataclass
class Task:
    task_id: str
    raw_prompt: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    status: TaskStatus = TaskStatus.RECEIVED
    steps: List[PlanStep] = field(default_factory=list)
    highest_risk: RiskLevel = RiskLevel.LOW
    approval_ticket_id: Optional[str] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "raw_prompt": self.raw_prompt,
            "intent": self.intent,
            "entities": self.entities,
            "confidence": self.confidence,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "steps": [s.to_dict() for s in self.steps],
            "highest_risk": self.highest_risk.value if isinstance(self.highest_risk, RiskLevel) else self.highest_risk,
            "approval_ticket_id": self.approval_ticket_id,
            "error_message": self.error_message,
            "output": self.output,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

@dataclass
class ApprovalTicket:
    ticket_id: str
    task_id: str
    action_type: str
    target_summary: str
    risk_level: RiskLevel
    reason: str
    status: TicketStatus = TicketStatus.PENDING
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 300)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "task_id": self.task_id,
            "action_type": self.action_type,
            "target_summary": self.target_summary,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else self.risk_level,
            "reason": self.reason,
            "status": self.status.value if isinstance(self.status, TicketStatus) else self.status,
            "details": self.details,
            "created_at": self.created_at,
            "expires_at": self.expires_at
        }

@dataclass
class AuditLog:
    log_id: str
    task_id: Optional[str]
    action: str
    resource_service: str
    permission_used: str
    risk_level: RiskLevel
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "task_id": self.task_id,
            "action": self.action,
            "resource_service": self.resource_service,
            "permission_used": self.permission_used,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else self.risk_level,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp
        }

@dataclass
class SystemEvent:
    event_id: str
    event_type: str
    task_id: Optional[str]
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "task_id": self.task_id,
            "payload": self.payload,
            "timestamp": self.timestamp
        }
