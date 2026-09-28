import time
from typing import Dict, Any, List
from tools.registry import registry
from storage.models import RiskLevel

@registry.register(
    name="remember_fact",
    description="Stores a persistent fact, preference, profile item, or project note in Magnas long-term memory.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Memory key identifier (e.g. user_skills, github_username, preferred_ide, java_version)"},
            "value": {"type": "string", "description": "Fact or context value to store"},
            "category": {"type": "string", "description": "Category label (e.g. profile, preferences, resume, project)"}
        },
        "required": ["key", "value"]
    }
)
def remember_fact(key: str, value: str, category: str = "general") -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            db_ref.save_memory(key, value, category)
            return {
                "success": True,
                "output": f"Successfully remembered '{key}': '{value}' under category '{category}'."
            }
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="recall_memory",
    description="Retrieves a specific memory item by key from Magnas long-term knowledge base.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Memory key identifier to look up"}
        },
        "required": ["key"]
    }
)
def recall_memory(key: str) -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            item = db_ref.get_memory(key)
            if item:
                return {"success": True, "output": f"Memory '{key}': {item['value']}", "item": item}
            return {"success": True, "output": f"No memory item found for key '{key}'."}
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="search_knowledge_base",
    description="Searches long-term persistent memory and knowledge base for matching query terms.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search keyword or topic"}
        },
        "required": ["query"]
    }
)
def search_knowledge_base(query: str) -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            items = db_ref.search_memory(query)
            if items:
                formatted = "\n".join([f"- [{i['category'].upper()}] {i['key']}: {i['value']}" for i in items])
                return {"success": True, "output": f"Found {len(items)} matching memory items:\n{formatted}", "items": items}
            return {"success": True, "output": f"No memory items matched query '{query}'."}
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}
