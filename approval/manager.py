import uuid
import time
from typing import Dict, Optional, List
from storage.models import ApprovalTicket, TicketStatus, RiskLevel
from storage.database import Database

class ApprovalManager:
    """Manages human approval contracts, pending tickets, and approval authorizations."""

    def __init__(self, db: Database):
        self.db = db

    def create_ticket(self, task_id: str, action_type: str, target_summary: str, risk_level: RiskLevel, reason: str, details: dict = None) -> ApprovalTicket:
        ticket = ApprovalTicket(
            ticket_id=f"tkt_{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            action_type=action_type,
            target_summary=target_summary,
            risk_level=risk_level,
            reason=reason,
            status=TicketStatus.PENDING,
            details=details or {},
            created_at=time.time(),
            expires_at=time.time() + 300 # 5 minutes
        )
        self.db.save_approval_ticket(ticket)
        return ticket

    def approve_ticket(self, ticket_id: str) -> Optional[ApprovalTicket]:
        ticket = self.db.get_approval_ticket(ticket_id)
        if not ticket:
            return None
        ticket.status = TicketStatus.APPROVED
        self.db.save_approval_ticket(ticket)
        return ticket

    def reject_ticket(self, ticket_id: str) -> Optional[ApprovalTicket]:
        ticket = self.db.get_approval_ticket(ticket_id)
        if not ticket:
            return None
        ticket.status = TicketStatus.REJECTED
        self.db.save_approval_ticket(ticket)
        return ticket

    def get_pending_tickets(self) -> List[ApprovalTicket]:
        return self.db.list_pending_tickets()
