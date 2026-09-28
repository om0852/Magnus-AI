import os
import json
import uuid
import time
from typing import Dict, Any, List, Optional

class SelfLearningEngine:
    """
    Self-Learning & Intent Correction Engine for Magnas AI.
    Learns from user corrections and misparsed execution failures to permanently override parser rules.
    """

    def match_prompt(self, text: str) -> Optional[Dict[str, Any]]:
        text_clean = text.lower().strip()
        try:
            from apps.control_center.web_server import db_ref
            if db_ref:
                rules = db_ref.list_learned_rules()
                for r in rules:
                    pattern = r["pattern"].lower().strip()
                    if pattern in text_clean or text_clean in pattern:
                        return {
                            "intent": r["target_intent"],
                            "confidence": 0.99,
                            "agent_name": "self_learned_engine",
                            "entities": r.get("parameters", {}),
                            "learned_rule_id": r["rule_id"]
                        }
        except Exception:
            pass
        return None

    def learn_correction(self, pattern: str, target_intent: str, target_tool: str, parameters: dict = None) -> str:
        rule_id = f"rule_{uuid.uuid4().hex[:6]}"
        try:
            from apps.control_center.web_server import db_ref
            if db_ref:
                db_ref.save_learned_rule(rule_id, pattern, target_intent, target_tool, parameters or {})
                return f"Successfully learned rule correction '{rule_id}' for pattern '{pattern}'."
        except Exception as e:
            return f"Failed to save learned rule: {e}"
        return f"Registered pattern '{pattern}' -> {target_intent}."

self_learning_engine = SelfLearningEngine()
