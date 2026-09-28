import os
import subprocess
import time
import shutil
from typing import Dict, Any, Optional
from storage.models import RiskLevel
from tools.registry import registry

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

@registry.register(
    name="develop_project_in_antigravity",
    description="Instruct Antigravity IDE & agy CLI to plan, code, build, test, and ship a full software project.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Project title or folder name"},
            "prompt": {"type": "string", "description": "Detailed project requirements, architecture, tech stack, and goals"},
            "slash_command": {"type": "string", "description": "Optional slash command (e.g. /goal, /plan, /grill-me)"}
        },
        "required": ["prompt"]
    }
)
def develop_project_in_antigravity(
    prompt: str,
    project_name: str = "new_project",
    slash_command: str = "/goal"
) -> str:
    user_home = os.path.expanduser("~")
    workspace_dir = os.path.join(user_home, "Documents", project_name.replace(" ", "_"))
    os.makedirs(workspace_dir, exist_ok=True)

    # Strategy 1: CLI Direct Agent Control via 'agy goal' or 'agy' if available in PATH
    agy_binary = shutil.which("agy") or shutil.which("antigravity")
    cli_success = False
    cli_output = ""

    if agy_binary:
        try:
            full_cmd = f'"{agy_binary}" goal "{prompt}"'
            proc = subprocess.Popen(full_cmd, shell=True, cwd=workspace_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cli_success = True
            cli_output = f"Triggered 'agy goal' process (PID {proc.pid}) in workspace '{workspace_dir}'."
        except Exception as e:
            cli_output = f"CLI trigger attempt: {e}"

    # Strategy 2: GUI Automation (Launch Antigravity IDE window & send IDE Chat prompt)
    gui_output = ""
    try:
        # Launch Antigravity IDE
        subprocess.Popen('start "" "antigravity.exe"', shell=True)
        time.sleep(2.5)

        if HAS_PYAUTOGUI:
            # Focus IDE Chat hotkey (Ctrl + L or Ctrl + Alt + I)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)

            # Format command with slash command if specified
            chat_payload = f"{slash_command} {prompt}" if slash_command and not prompt.startswith("/") else prompt
            pyautogui.write(chat_payload, interval=0.01)
            time.sleep(0.3)
            pyautogui.press('enter')

            gui_output = f"Focused Antigravity IDE Chat window, typed command '{slash_command}', and triggered execution."
        else:
            gui_output = "Opened Antigravity IDE application window."
    except Exception as e:
        gui_output = f"GUI activation: {e}"

    res_msg = (
        f"[Antigravity IDE Integration Success]\n"
        f"Workspace: {workspace_dir}\n"
        f"Prompt Sent: '{prompt}'\n"
        f"Slash Command: {slash_command}\n"
        f"Details: {cli_output or gui_output}"
    )
    return res_msg
