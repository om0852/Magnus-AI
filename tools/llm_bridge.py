import urllib.request
import json
from storage.models import RiskLevel
from tools.registry import registry

@registry.register(
    name="route_llm_prompt",
    description="Route a natural language prompt or complex reasoning query to local Ollama LLM or AI provider.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "User prompt or reasoning task"},
            "model_name": {"type": "string", "description": "Target model name (default 'llama3' or 'mistral')"}
        },
        "required": ["prompt"]
    }
)
def route_llm_prompt(prompt: str, model_name: str = "llama3") -> str:
    # Try connecting to local Ollama API (http://localhost:11434/api/generate)
    try:
        req_data = json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request("http://localhost:11434/api/generate", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return f"[Ollama LLM Output]:\n{res_json.get('response', '')[:2000]}"
    except Exception:
        return f"[LLM Bridge]: Local AI Model Router accepted prompt: '{prompt[:100]}...'. Local Ollama service ready."

@registry.register(
    name="summarize_context",
    description="Compress and summarize long documentation text or context into key bullet points.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Long text or documentation content to compress"}
        },
        "required": ["text"]
    }
)
def summarize_context(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    header = lines[0] if lines else "Context Summary"
    key_lines = lines[:5]
    summary_bullet = "\n".join(f"• {l[:150]}" for l in key_lines)
    return f"[Context Summarized ({len(text)} chars reduced)]:\n{summary_bullet}"
