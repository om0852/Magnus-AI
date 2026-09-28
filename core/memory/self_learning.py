import os
import json
import uuid
import time
from typing import Dict, Any, List, Optional

class SelfLearningEngine:
    """
    Self-Learning & Intent Correction Engine for Magnas AI.
    Learns from user corrections and misparsed execution failures to permanently override parser rules in long-term SQLite storage.
    """

    def _get_db(self):
        try:
            from apps.control_center.web_server import db_ref
            if db_ref:
                return db_ref
        except Exception:
            pass
        try:
            from storage.database import Database
            return Database()
        except Exception:
            return None

    def match_prompt(self, text: str) -> Optional[Dict[str, Any]]:
        text_clean = text.lower().strip()
        db = self._get_db()
        if not db:
            return None

        try:
            rules = db.list_learned_rules()
            # 1. Exact match check (highest priority)
            for r in rules:
                pattern = r["pattern"].lower().strip()
                if pattern == text_clean:
                    params = r.get("parameters", {})
                    entities = {"target_tool": r["target_tool"], **params} if r.get("target_tool") else params
                    return {
                        "intent": r["target_intent"],
                        "confidence": 1.0,
                        "agent_name": "self_learned_engine",
                        "entities": entities,
                        "learned_rule_id": r["rule_id"]
                    }

            # 2. Phrase / Substring match check
            for r in rules:
                pattern = r["pattern"].lower().strip()
                if len(pattern) >= 4 and pattern in text_clean:
                    params = r.get("parameters", {})
                    entities = {"target_tool": r["target_tool"], **params} if r.get("target_tool") else params
                    return {
                        "intent": r["target_intent"],
                        "confidence": 0.99,
                        "agent_name": "self_learned_engine",
                        "entities": entities,
                        "learned_rule_id": r["rule_id"]
                    }
        except Exception as e:
            print(f"[SelfLearningEngine Error] match_prompt failed: {e}")
            
        return None

    def learn_correction(self, pattern: str, target_intent: str, target_tool: str, parameters: dict = None) -> str:
        rule_id = f"rule_{uuid.uuid4().hex[:6]}"
        db = self._get_db()
        if not db:
            return "Error: Database instance unavailable for self-learning memory persistence."

        try:
            db.save_learned_rule(rule_id, pattern, target_intent, target_tool, parameters or {})
            return f"Successfully saved self-learned rule '{rule_id}' for pattern '{pattern}' -> Intent: {target_intent} (Tool: {target_tool})."
        except Exception as e:
            return f"Failed to save learned rule: {e}"

    def forget_rule(self, rule_id: str) -> str:
        db = self._get_db()
        if not db:
            return "Error: Database unavailable."
        try:
            db.delete_learned_rule(rule_id)
            return f"Successfully deleted learned rule '{rule_id}'."
        except Exception as e:
            return f"Failed to delete rule '{rule_id}': {e}"

    def auto_fix_and_learn_failure(self, prompt: str, error_msg: str, corrected_intent: str, target_tool: str, parameters: dict = None) -> str:
        """Automatically registers a learned correction rule after an execution failure or user correction feedback."""
        res = self.learn_correction(prompt, corrected_intent, target_tool, parameters)
        print(f"[SelfLearning Engine] Learned from failure on prompt '{prompt}': {res}")
        return res

self_learning_engine = SelfLearningEngine()
