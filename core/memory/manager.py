from typing import Dict, Any, Optional

class MemoryManager:
    """Stores session context, working variables, active window info, and conversation memory."""

    def __init__(self):
        self._memory: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._memory.get(key, default)

    def delete(self, key: str):
        if key in self._memory:
            del self._memory[key]

    def clear(self):
        self._memory.clear()

    def get_all(self) -> Dict[str, Any]:
        return dict(self._memory)
