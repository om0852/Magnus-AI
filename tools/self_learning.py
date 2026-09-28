import time
from typing import Dict, Any, List
from tools.registry import registry
from storage.models import RiskLevel
from core.memory.self_learning import self_learning_engine

@registry.register(
    name="learn_pattern_correction",
    description="Teaches Magnas AI a new pattern correction so it remembers how to parse and execute specific prompts accurately in the future.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "prompt_pattern": {"type": "string", "description": "User prompt phrase pattern to learn (e.g. 'open firefox go to apify console')"},
            "correct_intent": {"type": "string", "description": "Correct intent (e.g. 'OPEN_WEBSITE', 'SEARCH_WEB', 'DEVELOP_PROJECT_ANTIGRAVITY')"},
            "target_tool": {"type": "string", "description": "Target tool name (e.g. 'open_url', 'browser_search')"},
            "parameters": {"type": "object", "description": "Parameters payload dictionary (e.g. {'url': 'https://console.apify.com'})"}
        },
        "required": ["prompt_pattern", "correct_intent", "target_tool"]
    }
)
def learn_pattern_correction(prompt_pattern: str, correct_intent: str, target_tool: str, parameters: dict = None) -> Dict[str, Any]:
    try:
        res = self_learning_engine.learn_correction(prompt_pattern, correct_intent, target_tool, parameters or {})
        return {
            "success": True,
            "output": f"[Self-Learning Memory Updated]: {res}",
            "pattern": prompt_pattern,
            "intent": correct_intent
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="list_learned_rules",
    description="Lists all self-learned rule corrections stored in Magnas long-term memory.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_learned_rules() -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            rules = db_ref.list_learned_rules()
            if rules:
                formatted = "\n".join([f"- [{r['rule_id']}] Pattern: '{r['pattern']}' -> Intent: {r['target_intent']} ({r['target_tool']})" for r in rules])
                return {"success": True, "output": f"Learned Rule Corrections ({len(rules)}):\n{formatted}", "rules": rules}
            return {"success": True, "output": "No custom learned rule corrections stored yet."}
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="forget_learned_rule",
    description="Removes a specific learned rule correction by rule ID.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "rule_id": {"type": "string", "description": "Rule ID to delete"}
        },
        "required": ["rule_id"]
    }
)
def forget_learned_rule(rule_id: str) -> Dict[str, Any]:
    try:
        from apps.control_center.web_server import db_ref
        if db_ref:
            db_ref.delete_learned_rule(rule_id)
            return {"success": True, "output": f"Successfully deleted learned rule '{rule_id}'."}
        return {"success": False, "error": "Database session unavailable."}
    except Exception as e:
        return {"success": False, "error": str(e)}
