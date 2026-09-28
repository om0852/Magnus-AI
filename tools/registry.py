import inspect
from typing import Callable, Dict, Any, List, Optional
from storage.models import RiskLevel

class Tool:
    def __init__(self, name: str, description: str, risk_level: RiskLevel, func: Callable, schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.func = func
        self.schema = schema

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            result = self.func(**kwargs)
            return {"success": True, "output": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, name: str, description: str, risk_level: RiskLevel, schema: Dict[str, Any]):
        def decorator(func: Callable):
            tool = Tool(
                name=name,
                description=description,
                risk_level=risk_level,
                func=func,
                schema=schema
            )
            self._tools[name] = tool
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level.value if isinstance(t.risk_level, RiskLevel) else t.risk_level,
                "schema": t.schema
            }
            for t in self._tools.values()
        ]

# Global registry instance
registry = ToolRegistry()
