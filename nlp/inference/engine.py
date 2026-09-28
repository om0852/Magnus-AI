import os
import re
import json
from typing import Dict, Any, Tuple
from nlp.tokenizer.tokenizer import CommandTokenizer

try:
    import torch
    from nlp.model.transformer import MagnasNLPModel
    from nlp.training.dataset_generator import INTENTS
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from nlp.tokenizer.tokenizer import CommandTokenizer
from nlp.agents.multi_agent_engine import MultiAgentNetwork

try:
    import torch
    from nlp.model.transformer import MagnasNLPModel
    from nlp.training.dataset_generator import INTENTS
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

class InferenceEngine:
    """
    Magnas specialized local NLP Inference Engine powered by 11-Micro-Agent Network.
    Combines Router Agent, Domain-Specialized Micro-Agents, and deterministic slot parsing.
    """

    def __init__(self, model_dir: str = "nlp/models/magnas-nlp"):
        self.model_dir = model_dir
        self.onnx_session = None
        self.pytorch_model = None
        self.tokenizer = None
        self.labels = []
        self.multi_agent_net = None
        try:
            self.multi_agent_net = MultiAgentNetwork()
        except Exception as e:
            print(f"[InferenceEngine Warning] MultiAgentNetwork init note: {e}")
        self._load_model()

    def _load_model(self):
        tokenizer_path = os.path.join(self.model_dir, "tokenizer.json")
        labels_path = os.path.join(self.model_dir, "labels.json")
        onnx_path = os.path.join(self.model_dir, "model.onnx")
        pth_path = os.path.join(self.model_dir, "model.pth")

        if os.path.exists(tokenizer_path) and os.path.exists(labels_path):
            try:
                self.tokenizer = CommandTokenizer.load(tokenizer_path)
                with open(labels_path, "r", encoding="utf-8") as f:
                    label_map = json.load(f)
                    self.labels = [k for k, v in sorted(label_map.items(), key=lambda x: x[1])]
            except Exception as e:
                print(f"[InferenceEngine Warning] Failed to load tokenizer/labels: {e}")

        # Load PyTorch model if available
        if HAS_TORCH and os.path.exists(pth_path) and self.tokenizer:
            try:
                self.pytorch_model = MagnasNLPModel(
                    vocab_size=len(self.tokenizer.vocab),
                    num_intents=len(INTENTS),
                    num_slots=10
                )
                self.pytorch_model.load_state_dict(torch.load(pth_path, map_location="cpu"))
                self.pytorch_model.eval()
                print(f"[InferenceEngine] Loaded trained PyTorch Transformer model from '{pth_path}'.")
            except Exception as e:
                print(f"[InferenceEngine Warning] PyTorch model load failed: {e}")

        # Load ONNX session if available
        if os.path.exists(onnx_path):
            try:
                import onnxruntime as ort
                self.onnx_session = ort.InferenceSession(onnx_path)
            except Exception as e:
                print(f"[InferenceEngine Warning] ONNX Runtime session failed: {e}")

    def parse(self, text: str) -> Dict[str, Any]:
        text_clean = text.strip()

        # Step 0: Check Self-Learned Rule Overrides
        try:
            from core.memory.self_learning import self_learning_engine
            learned_match = self_learning_engine.match_prompt(text_clean)
            if learned_match:
                return learned_match
        except Exception:
            pass

        # Step 1: Rule-based & Compound phrase matching
        rule_result = self._rule_parse(text_clean)
        if rule_result["confidence"] >= 0.85:
            return rule_result


        # Step 2: 11-Micro-Agent Network Inference
        if self.multi_agent_net:
            try:
                agent_res = self.multi_agent_net.predict(text_clean)
                if agent_res.get("intent") != "UNKNOWN" and agent_res.get("confidence", 0.0) >= 0.7:
                    intent_lbl = agent_res.get("intent")
                    entities = self._extract_entities_for_intent(intent_lbl, text_clean)
                    return {
                        "intent": intent_lbl,
                        "confidence": agent_res.get("confidence"),
                        "domain": agent_res.get("domain"),
                        "agent_name": agent_res.get("agent_name"),
                        "entities": entities
                    }
            except Exception as e:
                pass
        if self.pytorch_model and self.tokenizer:
            try:
                input_ids = self.tokenizer.encode(text_clean, max_length=32)
                # Check if non-padding tokens are mostly UNK (id 1)
                non_pad = [i for i in input_ids if i != 0]
                unk_count = sum(1 for i in non_pad if i == 1)
                if non_pad and unk_count / len(non_pad) >= 0.5:
                    return {"intent": "UNKNOWN", "confidence": 0.0, "entities": {}}

                tensor_input = torch.tensor([input_ids], dtype=torch.long)
                with torch.no_grad():
                    intent_logits, _ = self.pytorch_model(tensor_input)
                    probs = torch.softmax(intent_logits[0], dim=-1)
                    best_idx = torch.argmax(probs).item()
                    confidence = probs[best_idx].item()
                    intent_label = self.labels[best_idx] if (best_idx < len(self.labels) and confidence >= 0.75) else "UNKNOWN"
                    
                    entities = self._extract_entities_for_intent(intent_label, text_clean) if intent_label != "UNKNOWN" else {}
                    return {
                        "intent": intent_label,
                        "confidence": round(float(confidence), 4),
                        "entities": entities
                    }
            except Exception as e:
                print(f"[InferenceEngine Error] PyTorch prediction failed: {e}")

        # Step 3: ONNX Model inference if available
        if self.onnx_session and self.tokenizer:
            try:
                input_ids = [self.tokenizer.encode(text_clean, max_length=32)]
                outputs = self.onnx_session.run(None, {"input_ids": input_ids})
                intent_logits = outputs[0][0]
                import numpy as np
                probs = np.exp(intent_logits) / np.sum(np.exp(intent_logits))
                best_idx = int(np.argmax(probs))
                confidence = float(probs[best_idx])
                intent_label = self.labels[best_idx] if (best_idx < len(self.labels) and confidence >= 0.65) else "UNKNOWN"
                
                entities = self._extract_entities_for_intent(intent_label, text_clean) if intent_label != "UNKNOWN" else {}
                return {
                    "intent": intent_label,
                    "confidence": round(confidence, 4),
                    "entities": entities
                }
            except Exception as e:
                print(f"[InferenceEngine Error] ONNX prediction failed: {e}")

        # Fallback to rule result or UNKNOWN
        return rule_result

    def _rule_parse(self, text: str) -> Dict[str, Any]:
        lower = text.lower().strip()

        # Priority Check: Casual Voice Greeting & Chat
        if lower in ["hi", "hello", "hey", "hi magnas", "hey magnas", "hello magnas", "hey magnus", "hi magnus", "are you there", "who are you", "what can you do"]:
            return {
                "intent": "GREETING",
                "confidence": 0.99,
                "entities": {"message": "Hello! I am Magnas, your AI assistant. I am fully online and ready to help you build software projects in Antigravity IDE, search web docs, design resumes, or automate daily tasks. How can I assist you right now?"}
            }

        # Priority Check: Voice Progress Inquiry
        if any(kw in lower for kw in ["progress", "how far along", "status update", "what are you working on", "is task done", "current task", "tell me progress"]):
            return {
                "intent": "GET_PROGRESS",
                "confidence": 0.99,
                "entities": {}
            }

        # Priority Check: Self-Learning Command Intents
        if lower in ["list learned rules", "show learned rules", "view learned rules"]:
            return {
                "intent": "LIST_LEARNED_RULES",
                "confidence": 0.99,
                "entities": {}
            }

        m_forget = re.search(r"^(?:forget|delete|remove)\s+(?:rule\s+)?(rule_[a-f0-9]+)$", lower)
        if m_forget:
            return {
                "intent": "FORGET_LEARNED_RULE",
                "confidence": 0.99,
                "entities": {"rule_id": m_forget.group(1)}
            }

        m_learn = re.search(r"^(?:learn|teach|remember|fix\s+issue\s+for)\s+['\"]?(.+?)['\"]?\s+(?:to\s+|means\s+|as\s+)?(?:use\s+)?(?:intent\s+)?([a-zA-Z0-9_]+)\s*(?:with\s+tool\s+([a-zA-Z0-9_]+))?", lower)
        if m_learn:
            pat = m_learn.group(1).strip()
            intent_val = m_learn.group(2).strip().upper()
            tool_val = m_learn.group(3).strip().lower() if m_learn.group(3) else intent_val.lower()
            return {
                "intent": "LEARN_CORRECTION",
                "confidence": 0.99,
                "entities": {
                    "prompt_pattern": pat,
                    "correct_intent": intent_val,
                    "target_tool": tool_val,
                    "parameters": {}
                }
            }

        # Priority Check: Antigravity IDE Project Development Intent
        if "antigravity" in lower and any(w in lower for w in ["develop", "build", "create", "make", "project", "app", "ide"]):
            m_proj = re.search(r"(?:develop|build|create|make)\s+(?:a\s+|an\s+)?([a-zA-Z0-9_\-\s]+?)(?:\s+using|\s+in|\s+with|\s+on|$)", lower)
            proj_name = m_proj.group(1).strip() if m_proj else "new_antigravity_project"
            return {
                "intent": "DEVELOP_PROJECT_ANTIGRAVITY",
                "confidence": 0.98,
                "entities": {"project_name": proj_name, "prompt": text}
            }

        # Priority Check: Resume Design Intent (prevent compound splitting on 'and' in conversational resume prompts)
        if "resume" in lower and any(w in lower for w in ["design", "create", "generate", "build", "make", "new", "sde", "java", "developer"]):
            extracted_title = self._extract_resume_title(lower)
            return {
                "intent": "DESIGN_RESUME",
                "confidence": 0.98,
                "entities": {"name": "Om Salunke", "title": extracted_title}
            }


        # Check for Compound Commands joined by " and "
        if " and " in lower:
            parts = [p.strip() for p in lower.split(" and ") if p.strip()]
            sub_tasks = []
            for part in parts:
                sub_res = self._single_rule_parse(part)
                if sub_res.get("intent") == "COMPOUND_TASK" and "sub_tasks" in sub_res.get("entities", {}):
                    sub_tasks.extend(sub_res["entities"]["sub_tasks"])
                elif sub_res.get("intent") != "UNKNOWN":
                    sub_tasks.append(sub_res)
            
            if len(sub_tasks) > 1:
                return {
                    "intent": "COMPOUND_TASK",
                    "confidence": 0.98,
                    "entities": {"sub_tasks": sub_tasks}
                }


        return self._single_rule_parse(lower)

    def _single_rule_parse(self, lower: str) -> Dict[str, Any]:
        # 4. Search Web / Search Site
        if lower.startswith("search web") or "for " in lower or any(w in lower for w in ["youtube", "google", "bing", "github", "wikipedia", "scrapper", "scraper", "apify", "low price", "cheapest", "best", "price"]):
            m_search_site = re.search(r"^(?:search\s+web\s+for|search)\s+([a-zA-Z0-9]+)\s+for\s+(.+)$", lower)
            if m_search_site:
                site = m_search_site.group(1).strip()
                query = m_search_site.group(2).strip()
                return {
                    "intent": "SEARCH_WEB",
                    "confidence": 0.95,
                    "entities": {"query": query, "site": site}
                }
            
            m_search = re.search(r"^(?:search|find|locate)\s+(?:web\s+for\s+|for\s+)?(.+?)(?:\s+on\s+([a-zA-Z0-9]+))?$", lower)
            if m_search:
                query = m_search.group(1).strip()
                site = m_search.group(2).strip() if m_search.group(2) else "google"
                return {
                    "intent": "SEARCH_WEB",
                    "confidence": 0.95,
                    "entities": {"query": query, "site": site}
                }

        # Search files / find file (only for explicit local file queries)
        m_find = re.search(r"^(?:find|search|locate)\s+(?:my\s+)?(?:latest\s+)?(?:file\s+)?([a-zA-Z0-9_\-\.\s]+)$", lower)
        if m_find and not lower.startswith("open"):
            kw = m_find.group(1).strip()
            if not any(w in kw for w in ["best", "scrapper", "scraper", "apify", "low price", "cheapest", "price", "buy", "online", "web"]) and kw not in ["chrome", "firefox", "discord", "spotify", "vscode", "file explorer"]:
                return {
                    "intent": "SEARCH_FILES",
                    "confidence": 0.95,
                    "entities": {"query": kw}
                }
            else:
                return {
                    "intent": "SEARCH_WEB",
                    "confidence": 0.95,
                    "entities": {"query": kw, "site": "google"}
                }

        # Resume Design Intent
        if "resume" in lower and any(w in lower for w in ["design", "create", "generate", "build", "make", "new", "sde", "java", "developer"]):
            extracted_title = self._extract_resume_title(lower)
            return {
                "intent": "DESIGN_RESUME",
                "confidence": 0.98,
                "entities": {"name": "Om Salunke", "title": extracted_title}
            }

        # 1. Open Application / Navigation Split
        m_app = re.search(r"^(?:open|launch|start|run|bring up|switch to)\s+([a-zA-Z0-9_\-\.\s]+)$", lower)
        if m_app:
            app_raw = m_app.group(1).strip()
            if " go to " in app_raw or " navigate to " in app_raw:
                parts = re.split(r"\s+(?:go\s+to|navigate\s+to)\s+", app_raw, maxsplit=1)
                app_name = parts[0].strip()
                target_site = parts[1].strip() if len(parts) > 1 else ""
                return {
                    "intent": "COMPOUND_TASK",
                    "confidence": 0.99,
                    "entities": {
                        "sub_tasks": [
                            {"intent": "OPEN_APP", "confidence": 0.98, "entities": {"application": app_name}},
                            {"intent": "SEARCH_WEB", "confidence": 0.95, "entities": {"query": target_site, "site": "google"}}
                        ]
                    }
                }
            
            if not app_raw.startswith("http") and app_raw not in ["file", "folder", "directory"]:
                return {
                    "intent": "OPEN_APP",
                    "confidence": 0.98,
                    "entities": {"application": app_raw}
                }


        # 2. Close Application
        m_close = re.search(r"^(?:close|exit|terminate|kill|shut down)\s+([a-zA-Z0-9_\-\.\s]+)$", lower)
        if m_close:
            app_name = m_close.group(1).strip()
            return {
                "intent": "CLOSE_APP",
                "confidence": 0.98,
                "entities": {"application": app_name}
            }

        # 3. List Directory / List Files / List items on App
        if lower.startswith("list "):
            m_list_dir = re.search(r"^list\s+(?:files|directory|folder|dir)\s*(?:in|at)?\s*([a-zA-Z0-9_\-\.\/\\]*)$", lower)
            if m_list_dir:
                path = m_list_dir.group(1).strip() or "."
                return {
                    "intent": "READ_FILE",
                    "confidence": 0.95,
                    "entities": {"path": path}
                }

            # Search or app query ("list channels on discord")
            m_list_app = re.search(r"^list\s+(.+?)\s+on\s+([a-zA-Z0-9]+)$", lower)
            if m_list_app:
                query = m_list_app.group(1).strip()
                site = m_list_app.group(2).strip()
                return {
                    "intent": "SEARCH_WEB",
                    "confidence": 0.95,
                    "entities": {"query": f"list {query}", "site": site}
                }

        # 4. Search Web / Search Site
        m_search = re.search(r"^search\s+(?:for\s+)?(.+?)(?:\s+on\s+([a-zA-Z0-9]+))?$", lower)
        if m_search:
            query = m_search.group(1).strip()
            site = m_search.group(2).strip() if m_search.group(2) else "google"
            m_search_site = re.search(r"^search\s+([a-zA-Z0-9]+)\s+for\s+(.+)$", lower)
            if m_search_site:
                site = m_search_site.group(1).strip()
                query = m_search_site.group(2).strip()
            return {
                "intent": "SEARCH_WEB",
                "confidence": 0.95,
                "entities": {"query": query, "site": site}
            }

        # 5. Open URL
        if lower.startswith("http://") or lower.startswith("https://") or lower.startswith("www."):
            return {
                "intent": "OPEN_WEBSITE",
                "confidence": 0.99,
                "entities": {"url": lower}
            }

        # 6. Change Volume
        if "volume" in lower:
            m_vol = re.search(r"(increase|decrease|mute|turn up|turn down)\s*(?:the)?\s*volume\s*(?:by\s*)?(\d+)?", lower)
            if m_vol:
                action = m_vol.group(1)
                amount = int(m_vol.group(2)) if m_vol.group(2) else 10
                direction = "increase" if "up" in action or "increase" in action else ("decrease" if "down" in action or "decrease" in action else "mute")
                return {
                    "intent": "CHANGE_VOLUME",
                    "confidence": 0.95,
                    "entities": {"amount": amount, "direction": direction}
                }

        # 7. File Operations
        m_read = re.search(r"^(?:read|show|cat|display|view)\s+(?:file\s+)?([a-zA-Z0-9_\-\.\/\\]+)$", lower)
        if m_read:
            return {
                "intent": "READ_FILE",
                "confidence": 0.92,
                "entities": {"path": m_read.group(1)}
            }

        m_del = re.search(r"^(?:delete|remove|rm|erase)\s+(?:file\s+)?([a-zA-Z0-9_\-\.\/\\]+)$", lower)
        if m_del:
            return {
                "intent": "DELETE_FILE",
                "confidence": 0.95,
                "entities": {"path": m_del.group(1)}
            }

        # 8. Screenshot
        if "screenshot" in lower or "capture screen" in lower or "snapshot" in lower:
            return {
                "intent": "TAKE_SCREENSHOT",
                "confidence": 0.98,
                "entities": {}
            }

        # 9. Type Text
        m_type = re.search(r"^(?:type|write)\s+(.+)$", lower)
        if m_type:
            return {
                "intent": "TYPE_TEXT",
                "confidence": 0.90,
                "entities": {"text": m_type.group(1)}
            }

        # 10. Press Key
        m_key = re.search(r"^(?:press|hit)\s+(?:key\s+)?([a-zA-Z0-9\+\s]+)$", lower)
        if m_key:
            return {
                "intent": "PRESS_KEY",
                "confidence": 0.92,
                "entities": {"key": m_key.group(1).strip()}
            }

        # 11. Shell Command / Execute
        m_exec = re.search(r"^(?:run|exec|execute)\s+(?:command\s+)?(.+)$", lower)
        if m_exec:
            return {
                "intent": "EXECUTE_COMMAND",
                "confidence": 0.90,
                "entities": {"command": m_exec.group(1)}
            }

        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "entities": {}
        }

    def _extract_entities_for_intent(self, intent: str, text: str) -> Dict[str, Any]:
        return self._rule_parse(text).get("entities", {})

    def _extract_resume_title(self, lower: str) -> str:
        m_role = re.search(r"(?:role\s+(?:of\s+)?|for\s+a\s+|for\s+)(.+?)(?:\s+resume|\s+in\s+word|$)", lower)
        if m_role:
            candidate = m_role.group(1).strip()
            clean_cand = re.sub(r"\b(generate|create|design|build|make|open|show|my|me|for|a|an|new|role)\b", "", candidate, flags=re.IGNORECASE).strip()
            if len(clean_cand) >= 3:
                return clean_cand.upper()

        if "java" in lower or "spring" in lower:
            return "FULL STACK JAVA DEVELOPER"
        elif "sde" in lower:
            return "SOFTWARE DEVELOPMENT ENGINEER (SDE)"
        elif "ai" in lower or "ml" in lower or "machine learning" in lower:
            return "AI & SOFTWARE ENGINEER"
        elif "python" in lower or "backend" in lower:
            return "PYTHON BACKEND ENGINEER"
        elif "frontend" in lower or "react" in lower:
            return "FULL STACK REACT DEVELOPER"
        
        return "FULL STACK JAVA DEVELOPER"

