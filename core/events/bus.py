import asyncio
import uuid
import time
from typing import Callable, Dict, List, Any, Awaitable
from storage.models import SystemEvent
from storage.database import Database

SubscriberFunc = Callable[[SystemEvent], Awaitable[None]]

class EventBus:
    def __init__(self, db: Database = None):
        self.subscribers: List[SubscriberFunc] = []
        self.db = db

    def subscribe(self, callback: SubscriberFunc):
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback: SubscriberFunc):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def publish(self, event_type: str, task_id: str = None, payload: Dict[str, Any] = None) -> SystemEvent:
        if payload is None:
            payload = {}

        event = SystemEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            task_id=task_id,
            payload=payload,
            timestamp=time.time()
        )

        if self.db:
            try:
                self.db.save_event(event)
            except Exception as e:
                print(f"[EventBus Error] Failed to persist event {event.event_id}: {e}")

        # Notify subscribers asynchronously
        for sub in list(self.subscribers):
            try:
                if asyncio.iscoroutinefunction(sub):
                    await sub(event)
                else:
                    sub(event)
            except Exception as e:
                print(f"[EventBus Error] Subscriber failed on {event_type}: {e}")

        return event

# Global event bus singleton
default_bus = EventBus()
