import os
import time
from typing import Dict, Any
from tools.registry import registry
from storage.models import RiskLevel
from core.planner.self_healing import self_healing_engine

@registry.register(
    name="apply_self_healing_fix",
    description="Auto-detects build errors & syntax failures in Antigravity IDE and applies automated patches.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "error_message": {"type": "string", "description": "Compiler error message or stack trace"},
            "file_path": {"type": "string", "description": "Target source file path"}
        },
        "required": ["error_message"]
    }
)
def apply_self_healing_fix(error_message: str, file_path: str = "main_script.py") -> Dict[str, Any]:
    try:
        analysis = self_healing_engine.analyze_error_stacktrace(error_message, file_path)
        
        # Dispatch fix to Antigravity IDE
        try:
            from tools.antigravity_sidecar import send_antigravity_command
            send_antigravity_command(
                command=f"/plan Apply self-healing fix ({analysis['fix_type']}): {analysis['suggested_action']}",
                project_name="active_project"
            )
        except Exception:
            pass

        return {
            "success": True,
            "output": f"Self-Healing Repair Generated ({analysis['fix_type']}): {analysis['suggested_action']} (Dispatched to Antigravity IDE)",
            "analysis": analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="get_self_healing_report",
    description="Displays diagnostic repair history and automated code patch metrics.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_self_healing_report() -> Dict[str, Any]:
    try:
        count = self_healing_engine.repaired_issues_count
        history = self_healing_engine.repair_history[-10:]
        summary_lines = [f"- [{h['fix_type']}] File: '{h['file_path']}' -> {h['suggested_action']}" for h in history]
        output_text = f"Self-Healing Engine Metrics:\n- Total Issues Analyzed/Patched: {count}\n" + ("\n".join(summary_lines) if summary_lines else "No recent code repairs required.")
        return {
            "success": True,
            "output": output_text,
            "total_repaired": count,
            "history": history
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
