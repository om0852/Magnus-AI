import os
import time
from typing import Dict, Any, Optional
from storage.models import RiskLevel
from tools.registry import registry

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

@registry.register(
    name="read_screen_text",
    description="Perform OCR on desktop screenshot to extract visible screen text.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Optional screenshot path"}
        },
        "required": []
    }
)
def read_screen_text(image_path: str = None) -> str:
    user_home = os.path.expanduser("~")
    shots_dir = os.path.join(user_home, "Pictures")
    os.makedirs(shots_dir, exist_ok=True)

    if not image_path:
        # Take quick screenshot
        try:
            import pyautogui
            image_path = os.path.join(shots_dir, f"ocr_shot_{int(time.time())}.png")
            shot = pyautogui.screenshot()
            shot.save(image_path)
        except Exception:
            return "Unable to capture screenshot for screen vision text analysis."

    # Try pytesseract if available, else PIL image metadata summary
    try:
        import pytesseract
        text = pytesseract.image_to_string(Image.open(image_path))
        return f"[OCR Screen Text Extracted from '{image_path}']:\n{text[:1500]}"
    except Exception:
        if HAS_PIL and os.path.exists(image_path):
            img = Image.open(image_path)
            return f"[Screen Vision Image Analysis]: Captured screenshot '{image_path}' ({img.width}x{img.height} pixels, format: {img.format})."
        return f"Captured screen snapshot at '{image_path}'."

@registry.register(
    name="analyze_image",
    description="Analyze local image file dimensions, format, and metadata.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Image file path to inspect"}
        },
        "required": ["path"]
    }
)
def analyze_image(path: str) -> str:
    if not os.path.exists(path):
        return f"Image file '{path}' not found."

    if HAS_PIL:
        try:
            img = Image.open(path)
            size_kb = round(os.path.getsize(path) / 1024, 1)
            return f"[Image Analysis Results]: File '{os.path.basename(path)}' | Resolution: {img.width}x{img.height} | Format: {img.format} | Size: {size_kb} KB"
        except Exception as e:
            return f"Failed to analyze image '{path}': {e}"
    return f"Image file '{path}' exists on disk ({os.path.getsize(path)} bytes)."

@registry.register(
    name="media_playback",
    description="Control media playback key events (play, pause, next track, previous track, mute).",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "Playback action: 'playpause', 'next', 'prev', 'mute'"}
        },
        "required": ["action"]
    }
)
def media_playback(action: str = "playpause") -> str:
    act_lower = action.lower().strip()
    try:
        import pyautogui
        key_map = {
            "playpause": "playpause",
            "play": "playpause",
            "pause": "playpause",
            "next": "nexttrack",
            "prev": "prevtrack",
            "previous": "prevtrack",
            "mute": "volumemute"
        }
        target_key = key_map.get(act_lower, "playpause")
        pyautogui.press(target_key)
        return f"Sent Windows media playback key event '{target_key}'."
    except Exception as e:
        return f"Media playback key error: {e}"
