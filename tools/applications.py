import subprocess
import os
import sys
import glob
import shutil
import webbrowser
from storage.models import RiskLevel
from tools.registry import registry

@registry.register(
    name="open_application",
    description="Launch an application by executable name, protocol, web app, or shortcut on Windows.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "application": {"type": "string", "description": "Application name (e.g. chrome, firefox, chatgpt, antigravity ide, file explorer, notepad, vscode, calc)"}
        },
        "required": ["application"]
    }
)
def open_application(application: str) -> str:
    app_lower = application.lower().strip()

    # Web App shortcuts
    if app_lower in ["chatgpt", "chat gpt", "openai chatgpt"]:
        webbrowser.open("https://chatgpt.com")
        return "Opened ChatGPT web application (https://chatgpt.com) in default browser."

    # Dictionary of known application targets & protocol handlers
    app_map = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "mozilla firefox": "firefox",
        "antigravity ide": "antigravity-ide",
        "antigravity": "antigravity-ide",
        "agy": "antigravity-ide",
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "my computer": "explorer.exe",
        "folders": "explorer.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "settings": "ms-settings:",
        "control panel": "control.exe",
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        "terminal": "wt.exe",
        "mspaint": "mspaint.exe",
        "paint": "mspaint.exe",
        "snipping tool": "snippingtool.exe",
        "discord": "discord:",
        "spotify": "spotify:",
        "edge": "msedge.exe",
        "msedge": "msedge.exe",
        "brave": "brave.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "steam": "steam://",
        "vlc": "vlc.exe"
    }

    target = app_map.get(app_lower, application)

    # Protocol Handler (e.g. ms-settings:, discord:, steam://)
    if ":" in target and not os.path.exists(target):
        try:
            webbrowser.open(target)
            return f"Opened protocol handler '{target}' for application '{application}'."
        except Exception as e:
            raise RuntimeError(f"Failed to launch protocol '{target}': {e}")

    # 1. Resolve executable via PATH (shutil.which)
    resolved_path = (
        shutil.which(target)
        or shutil.which(f"{target}.exe")
        or shutil.which(f"{target}.cmd")
        or shutil.which(f"{target}.bat")
    )

    # 2. Check standard installation directories if not on PATH
    if not resolved_path:
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")

        candidate_paths = [
            os.path.join(local_appdata, "Programs", "Antigravity IDE", "Antigravity IDE.exe"),
            os.path.join(local_appdata, "Programs", "Antigravity IDE", "bin", "antigravity-ide.cmd"),
            os.path.join(local_appdata, "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(local_appdata, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
            os.path.join(local_appdata, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files, "Mozilla Firefox", "firefox.exe"),
            os.path.join(program_files_x86, "Mozilla Firefox", "firefox.exe"),
        ]

        for cand in candidate_paths:
            if os.path.exists(cand) and (target in cand.lower() or app_lower in cand.lower()):
                resolved_path = cand
                break

        if not resolved_path:
            # Recursive search in Programs & Start Menu
            search_dirs = [
                os.path.join(local_appdata, "Programs"),
                os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs"),
                os.path.join(program_files),
                os.path.join(program_files_x86)
            ]
            for sdir in search_dirs:
                if os.path.exists(sdir):
                    matches = glob.glob(os.path.join(sdir, "**", f"*{app_lower}*.exe"), recursive=True)
                    matches_lnk = glob.glob(os.path.join(sdir, "**", f"*{app_lower}*.lnk"), recursive=True)
                    found = matches or matches_lnk
                    if found:
                        resolved_path = found[0]
                        break

    if not resolved_path and os.path.exists(target):
        resolved_path = target

    # Execute resolved binary
    if resolved_path:
        try:
            if os.name == 'nt':
                os.startfile(resolved_path)
            else:
                subprocess.Popen([resolved_path])
            return f"Successfully launched application '{application}' from '{resolved_path}'."
        except Exception as e:
            try:
                subprocess.Popen(f'"{resolved_path}"', shell=True)
                return f"Successfully launched application '{application}' via shell."
            except Exception as ex:
                raise RuntimeError(f"Failed to launch resolved binary '{resolved_path}': {ex}")

    # Fallback to direct shell execution ONLY if command name is simple
    try:
        subprocess.Popen(target, shell=True)
        return f"Submitted launch request for application '{application}' (target '{target}')."
    except Exception as e:
        raise RuntimeError(f"Could not locate or open application '{application}'. Executable binary not found on system: {e}")

@registry.register(
    name="close_application",
    description="Close or terminate a running application process by name.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "application": {"type": "string", "description": "Application process name to terminate (e.g. notepad.exe, chrome.exe, firefox.exe)"}
        },
        "required": ["application"]
    }
)
def close_application(application: str) -> str:
    app_name = application.lower().strip()
    proc_map = {
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "antigravity ide": "Antigravity IDE.exe",
        "antigravity": "Antigravity IDE.exe",
        "agy": "Antigravity IDE.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "terminal": "WindowsTerminal.exe"
    }
    application_exe = proc_map.get(app_name, app_name)
    if not application_exe.endswith(".exe") and not "." in application_exe:
        application_exe = f"{application_exe}.exe"

    try:
        res = subprocess.run(f'taskkill /F /IM "{application_exe}"', shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return f"Successfully closed process '{application_exe}'"
        else:
            return f"Attempted taskkill: {res.stdout or res.stderr}"
    except Exception as e:
        raise RuntimeError(f"Failed to close application '{application}': {e}")
