import subprocess
import os
import sys
import glob
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
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "mozilla firefox": "firefox.exe",
        "antigravity ide": "antigravity.exe",
        "antigravity": "antigravity.exe",
        "agy": "antigravity.exe",
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

    # Strategy 1: Try Windows Shell `start` command (resolves App Paths, URIs, and PATH binaries)
    try:
        res = subprocess.run(f'start "" "{target}"', shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return f"Successfully opened application '{application}' (launched via Shell '{target}')"
    except Exception:
        pass

    # Strategy 2: Look for Discord / AppData / LocalAppData user installations
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")

    search_dirs = [
        os.path.join(local_appdata, app_lower),
        os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(program_files, app_lower),
        os.path.join(program_files_x86, app_lower)
    ]

    for sdir in search_dirs:
        if os.path.exists(sdir):
            matches = glob.glob(os.path.join(sdir, "**", f"*{app_lower}*.exe"), recursive=True)
            matches_lnk = glob.glob(os.path.join(sdir, "**", f"*{app_lower}*.lnk"), recursive=True)
            found = matches or matches_lnk
            if found:
                exe_path = found[0]
                subprocess.Popen(f'start "" "{exe_path}"', shell=True)
                return f"Successfully opened application '{application}' from path: '{exe_path}'"

    # Strategy 3: Try raw target fallback
    try:
        subprocess.Popen(target, shell=True)
        return f"Launched application '{application}' target '{target}'"
    except Exception as e:
        raise RuntimeError(f"Failed to locate or open application '{application}': {e}")

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
        "antigravity ide": "antigravity.exe",
        "antigravity": "antigravity.exe",
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
        res = subprocess.run(f"taskkill /F /IM {application_exe}", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return f"Successfully closed process '{application_exe}'"
        else:
            return f"Attempted taskkill: {res.stdout or res.stderr}"
    except Exception as e:
        raise RuntimeError(f"Failed to close application '{application}': {e}")
