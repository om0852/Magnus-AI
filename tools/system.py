import subprocess
import os
import time
from storage.models import RiskLevel
from tools.registry import registry
from vision.screenshot import capture_screen

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

@registry.register(
    name="change_volume",
    description="Adjust system audio volume by percentage or direction (increase/decrease/mute).",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "amount": {"type": "integer", "description": "Percentage amount (e.g. 10, 20)"},
            "direction": {"type": "string", "description": "Direction: 'increase', 'decrease', or 'mute'"}
        },
        "required": []
    }
)
def change_volume(amount: int = 10, direction: str = "increase") -> str:
    if os.name == 'nt':
        import ctypes
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF
        try:
            if direction == "mute":
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                return "Toggled system volume mute via Windows System API."

            vk = VK_VOLUME_UP if direction in ["increase", "up"] else VK_VOLUME_DOWN
            # In Windows, each VK_VOLUME step is ~2% volume adjustment.
            presses = max(1, int(amount / 2))
            for _ in range(presses):
                ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
                time.sleep(0.01)
            return f"{direction.capitalize()}d system volume by ~{amount}% ({presses} hardware volume key signals sent successfully)."
        except Exception as e:
            pass

    if HAS_PYAUTOGUI:
        key = "volumeup" if direction in ["increase", "up"] else "volumedown"
        if direction == "mute":
            pyautogui.press("volumemute")
            return "Toggled system volume mute"

        presses = max(1, int(amount / 5))
        for _ in range(presses):
            pyautogui.press(key)
        return f"{direction.capitalize()}d volume by ~{amount}% ({presses} presses of {key})"
    else:
        return f"[Simulated Volume Change]: {direction} by {amount}%"

@registry.register(
    name="take_screenshot",
    description="Capture a screenshot of the main monitor screen and save it to file.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "save_path": {"type": "string", "description": "Optional file path to save screenshot"}
        },
        "required": []
    }
)
def take_screenshot(save_path: str = None) -> str:
    path = capture_screen(save_path)
    return f"Screenshot captured and saved to '{path}'"

@registry.register(
    name="execute_command",
    description="Execute a system shell command or terminal script.",
    risk_level=RiskLevel.HIGH,
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"}
        },
        "required": ["command"]
    }
)
def execute_command(command: str) -> str:
    res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    out = (res.stdout or "") + (res.stderr or "")
    return f"Exit Code {res.returncode}:\n{out[:2000]}"
