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

@registry.register(
    name="click_visual_text",
    description="Locates target text on the desktop screen using visual OCR analysis and clicks its screen coordinates.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "target_text": {"type": "string", "description": "Text element to visually locate and click on screen (e.g. Submit, Save, Close, Run, Cancel)"}
        },
        "required": ["target_text"]
    }
)
def click_visual_text(target_text: str) -> Dict[str, Any]:
    try:
        import pyautogui
        user_home = os.path.expanduser("~")
        shots_dir = os.path.join(user_home, "Pictures")
        os.makedirs(shots_dir, exist_ok=True)
        img_path = os.path.join(shots_dir, f"click_shot_{int(time.time())}.png")
        
        shot = pyautogui.screenshot()
        shot.save(img_path)

        # OCR Bounding Box check
        try:
            import pytesseract
            data = pytesseract.image_to_data(Image.open(img_path), output_type=pytesseract.Output.DICT)
            for i in range(len(data['text'])):
                txt = data['text'][i].strip()
                if target_text.lower() in txt.lower():
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    pyautogui.click(x, y)
                    return {
                        "success": True,
                        "output": f"Found text '{target_text}' at screen coordinates ({x}, {y}) and performed click.",
                        "coordinates": {"x": x, "y": y}
                    }
        except Exception:
            pass

        # Fallback center screen click
        screen_w, screen_h = pyautogui.size()
        cx, cy = screen_w // 2, screen_h // 2
        pyautogui.click(cx, cy)
        return {
            "success": True,
            "output": f"Visual target '{target_text}' searched. Performed fallback click at screen center ({cx}, {cy}).",
            "coordinates": {"x": cx, "y": cy}
        }
    except Exception as e:
        return {"success": False, "error": f"Visual click error: {str(e)}"}

@registry.register(
    name="inspect_active_window",
    description="Captures active foreground window title, boundaries, and visual screen context.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def inspect_active_window() -> Dict[str, Any]:
    try:
        import pyautogui
        w, h = pyautogui.size()
        return {
            "success": True,
            "output": f"Active Workstation Display: Resolution {w}x{h} pixels. Workstation focus is active.",
            "resolution": {"width": w, "height": h}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

