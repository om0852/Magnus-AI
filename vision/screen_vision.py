import os
import time
import ctypes
from typing import Dict, Any, List, Tuple, Optional

try:
    from PIL import Image
    import pyautogui
    HAS_VISION_DEPS = True
except ImportError:
    HAS_VISION_DEPS = False

class ScreenVisionEngine:
    """
    Multi-Modal Screen Vision, Active Window UI Inspector & OCR Engine for Magnas AI.
    Inspects Windows active focused windows, process metadata, and screen text bounding boxes.
    """

    def __init__(self):
        self.last_screenshot_path: Optional[str] = None

    def capture_screen(self) -> str:
        user_home = os.path.expanduser("~")
        shots_dir = os.path.join(user_home, "Pictures")
        os.makedirs(shots_dir, exist_ok=True)
        img_path = os.path.join(shots_dir, f"vision_shot_{int(time.time())}.png")

        if HAS_VISION_DEPS:
            try:
                shot = pyautogui.screenshot()
                shot.save(img_path)
                self.last_screenshot_path = img_path
                return img_path
            except Exception:
                try:
                    from PIL import ImageGrab
                    shot = ImageGrab.grab(all_screens=False)
                    shot.save(img_path)
                    self.last_screenshot_path = img_path
                    return img_path
                except Exception:
                    pass
        return ""

    def inspect_active_window(self) -> Dict[str, Any]:
        """Inspects the currently focused window title, process ID, bounds, and screen position."""
        if os.name == 'nt':
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                title_buf = ctypes.create_unicode_buffer(512)
                ctypes.windll.user32.GetWindowTextW(hwnd, title_buf, 512)
                window_title = title_buf.value or "Desktop / System Window"

                rect = (0, 0, 0, 0)
                class RECT(ctypes.Structure):
                    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
                r = RECT()
                if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r)):
                    rect = (r.left, r.top, r.right - r.left, r.bottom - r.top)

                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                return {
                    "active": True,
                    "title": window_title,
                    "hwnd": int(hwnd),
                    "process_id": int(pid.value),
                    "position": {"x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3]}
                }
            except Exception as e:
                return {"active": False, "error": str(e)}

        return {"active": True, "title": "Active System Workspace", "position": {"x": 0, "y": 0, "width": 1920, "height": 1080}}

    def read_screen_text(self) -> Dict[str, Any]:
        """Captures active screen and extracts visible text using OCR analysis."""
        img_path = self.capture_screen()
        if not img_path or not os.path.exists(img_path):
            return {"success": False, "error": "Screen capture failed."}

        try:
            import pytesseract
            text = pytesseract.image_to_string(Image.open(img_path)).strip()
            return {
                "success": True,
                "text": text if text else "[Screen captured, but no distinct OCR text detected]",
                "image_path": img_path
            }
        except Exception:
            pass

        # Vision summary fallback
        window_info = self.inspect_active_window()
        return {
            "success": True,
            "text": f"Active Window: '{window_info.get('title')}' at position {window_info.get('position')}",
            "image_path": img_path,
            "window": window_info
        }

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
