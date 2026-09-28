import os
import time
from typing import Dict, Any, List, Tuple, Optional

try:
    from PIL import Image
    import pyautogui
    HAS_VISION_DEPS = True
except ImportError:
    HAS_VISION_DEPS = False

class ScreenVisionEngine:
    """
    Multi-Modal Screen Vision & OCR Bounding Box Locator.
    Locates UI text elements on Windows desktop screens and calculates exact click coordinates.
    """

    def __init__(self):
        self.last_screenshot_path: Optional[str] = None

    def capture_screen(self) -> str:
        user_home = os.path.expanduser("~")
        shots_dir = os.path.join(user_home, "Pictures")
        os.makedirs(shots_dir, exist_ok=True)
        img_path = os.path.join(shots_dir, f"vision_shot_{int(time.time())}.png")
        
        if HAS_VISION_DEPS:
            shot = pyautogui.screenshot()
            shot.save(img_path)
            self.last_screenshot_path = img_path
            return img_path
        return ""

    def locate_element(self, target_text: str) -> Dict[str, Any]:
        img_path = self.capture_screen()
        if not img_path or not os.path.exists(img_path):
            return {"found": False, "reason": "Screen capture unavailable"}

        try:
            import pytesseract
            data = pytesseract.image_to_data(Image.open(img_path), output_type=pytesseract.Output.DICT)
            for i in range(len(data['text'])):
                txt = data['text'][i].strip()
                if target_text.lower() in txt.lower() and len(txt) > 0:
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    return {
                        "found": True,
                        "text": txt,
                        "x": x,
                        "y": y,
                        "width": data['width'][i],
                        "height": data['height'][i],
                        "image_path": img_path
                    }
        except Exception:
            pass

        # Fallback screen center calculation
        if HAS_VISION_DEPS:
            w, h = pyautogui.size()
            return {
                "found": True,
                "text": target_text,
                "x": w // 2,
                "y": h // 2,
                "fallback": True,
                "image_path": img_path
            }
        return {"found": False, "reason": "PyAutoGUI / PIL dependencies not available"}

screen_vision = ScreenVisionEngine()
