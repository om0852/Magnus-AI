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
    workspace_dir = os.path.abspath(os.path.join(user_home, "Documents", project_name.replace(" ", "_")))
    os.makedirs(workspace_dir, exist_ok=True)

    # Resolve Antigravity IDE CLI binary
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    ide_cli = (
        shutil.which("antigravity-ide")
        or shutil.which("antigravity-ide.cmd")
        or shutil.which("agy")
        or os.path.join(local_appdata, "Programs", "Antigravity IDE", "bin", "antigravity-ide.cmd")
    )

    details = []

    # 1. Open project folder in Antigravity IDE
    if ide_cli and os.path.exists(ide_cli):
        try:
            subprocess.Popen(f'"{ide_cli}" "{workspace_dir}"', shell=True)
            details.append(f"Opened workspace folder '{workspace_dir}' in Antigravity IDE.")
            time.sleep(2.0)
        except Exception as e:
            details.append(f"Folder launch note: {e}")

        # 2. Trigger native Antigravity IDE Chat Agent session directly in project workspace
        try:
            chat_payload = f"{slash_command} {prompt}" if slash_command and not prompt.startswith("/") else prompt
            chat_cmd = f'"{ide_cli}" chat -m agent "{chat_payload}"'
            proc = subprocess.Popen(chat_cmd, cwd=workspace_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            details.append(f"Triggered Antigravity IDE Chat Agent session (PID {proc.pid}) with command '{slash_command}'.")
        except Exception as e:
            details.append(f"Native chat trigger note: {e}")

    # 3. Fallback / GUI Keyboard Focus
    if HAS_PYAUTOGUI:
        try:
            time.sleep(1.0)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            chat_payload = f"{slash_command} {prompt}" if slash_command and not prompt.startswith("/") else prompt
            pyautogui.write(chat_payload, interval=0.01)
            time.sleep(0.2)
            pyautogui.press('enter')
            details.append(f"Sent IDE chat keyboard hotkey focus sequence.")
        except Exception as e:
            pass

    res_msg = (
        f"[Antigravity IDE Project Development Triggered]\n"
        f"Workspace Directory: '{workspace_dir}'\n"
        f"Prompt Sent: '{prompt}'\n"
        f"Slash Command: '{slash_command}'\n"
        f"Execution Summary: {' | '.join(details)}"
    )
    return res_msg
