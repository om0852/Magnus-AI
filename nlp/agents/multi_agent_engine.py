import os
import json
import torch
from typing import Dict, Any, Optional
from nlp.tokenizer.tokenizer import CommandTokenizer
from nlp.model.transformer import MagnasNLPModel

class SingleMicroAgent:
    """Wrapper around single trained micro-agent model."""
    def __init__(self, name: str, model_dir: str):
        self.name = name
        self.model_dir = model_dir
        self.tokenizer = None
        self.labels = []
        self.model = None
        self._load()

    def _load(self):
        tok_path = os.path.join(self.model_dir, "tokenizer.json")
        lbl_path = os.path.join(self.model_dir, "labels.json")
        pth_path = os.path.join(self.model_dir, "model.pth")

        if os.path.exists(tok_path) and os.path.exists(lbl_path) and os.path.exists(pth_path):
            try:
                self.tokenizer = CommandTokenizer.load(tok_path)
                with open(lbl_path, "r", encoding="utf-8") as f:
                    label_map = json.load(f)
                    self.labels = [k for k, v in sorted(label_map.items(), key=lambda x: x[1])]
                
                self.model = MagnasNLPModel(
                    vocab_size=len(self.tokenizer.vocab),
                    num_intents=len(self.labels),
                    num_slots=5
                )
                self.model.load_state_dict(torch.load(pth_path, map_location="cpu"))
                self.model.eval()
            except Exception as e:
                print(f"[MicroAgent Warning] Failed loading '{self.name}': {e}")

    def predict(self, text: str) -> Dict[str, Any]:
        if not self.model or not self.tokenizer:
            return {"intent": "UNKNOWN", "confidence": 0.0}

        ids = self.tokenizer.encode(text, max_length=32)
        non_pad = [i for i in ids if i != 0]
        unk_count = sum(1 for i in non_pad if i == 1)
        if non_pad and (unk_count / len(non_pad)) >= 0.85:
            return {"intent": "UNKNOWN", "confidence": 0.0}

        tensor_in = torch.tensor([ids], dtype=torch.long)
        with torch.no_grad():
            logits, _ = self.model(tensor_in)
            probs = torch.softmax(logits[0], dim=-1)
            best_idx = torch.argmax(probs).item()
            confidence = probs[best_idx].item()
            label = self.labels[best_idx] if (best_idx < len(self.labels) and confidence >= 0.4) else "UNKNOWN"
            return {"intent": label, "confidence": round(float(confidence), 4)}

class MultiAgentNetwork:
    """
    11-Micro-Agent Classifier Network for Magnas AI.
    Routes prompts using RouterAgent and delegates to domain-specialized agent models.
    """
    def __init__(self, base_models_dir: str = "nlp/models/agents"):
        self.base_dir = base_models_dir
        self.router = SingleMicroAgent("router_agent", os.path.join(base_models_dir, "router_agent"))
        self.agents = {
            "DOMAIN_OS": SingleMicroAgent("os_agent", os.path.join(base_models_dir, "os_agent")),
            "DOMAIN_BROWSER": SingleMicroAgent("browser_agent", os.path.join(base_models_dir, "browser_agent")),
            "DOMAIN_IDE": SingleMicroAgent("ide_agent", os.path.join(base_models_dir, "ide_agent")),
            "DOMAIN_RESUME": SingleMicroAgent("resume_agent", os.path.join(base_models_dir, "resume_agent")),
            "DOMAIN_SECURITY": SingleMicroAgent("security_agent", os.path.join(base_models_dir, "security_agent")),
            "DOMAIN_DATABASE": SingleMicroAgent("database_agent", os.path.join(base_models_dir, "database_agent")),
            "DOMAIN_VISION_MEDIA": SingleMicroAgent("vision_agent", os.path.join(base_models_dir, "vision_agent")),
            "DOMAIN_SCHEDULER": SingleMicroAgent("scheduler_agent", os.path.join(base_models_dir, "scheduler_agent")),
            "DOMAIN_CLI": SingleMicroAgent("cli_agent", os.path.join(base_models_dir, "cli_agent")),
            "DOMAIN_LLM": SingleMicroAgent("llm_agent", os.path.join(base_models_dir, "llm_agent"))
        }
        print(f"[MultiAgentNetwork] Successfully initialized 11 micro-agents.")

    def predict(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower().strip()

        # Domain routing check
        target_domain = None
        if any(w in text_lower for w in ["database", "sqlite", "query", "sql", "export"]):
            target_domain = "DOMAIN_DATABASE"
        elif any(w in text_lower for w in ["ocr", "screen text", "image", "media", "playback", "pause", "play"]):
            target_domain = "DOMAIN_VISION_MEDIA"
        elif any(w in text_lower for w in ["timer", "reminder", "cron", "schedule"]):
            target_domain = "DOMAIN_SCHEDULER"
        elif any(w in text_lower for w in ["powershell", "npm", "pip", "ping", "port"]):
            target_domain = "DOMAIN_CLI"
        elif any(w in text_lower for w in ["ollama", "llm", "compress"]):
            target_domain = "DOMAIN_LLM"
        elif any(w in text_lower for w in ["antigravity"]):
            target_domain = "DOMAIN_IDE"
        elif any(w in text_lower for w in ["resume"]):
            target_domain = "DOMAIN_RESUME"

        if not target_domain:
            route_res = self.router.predict(text)
            target_domain = route_res.get("intent")
            if target_domain not in self.agents:
                target_domain = "DOMAIN_OS"

        agent = self.agents.get(target_domain, self.agents["DOMAIN_OS"])
        agent_res = agent.predict(text)

        return {
            "domain": target_domain,
            "agent_name": agent.name,
            "intent": agent_res.get("intent", "UNKNOWN"),
            "confidence": agent_res.get("confidence", 0.0)
        }
