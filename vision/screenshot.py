import os
import time

def capture_screen(save_path: str = None) -> str:
    if not save_path:
        os.makedirs("screenshots", exist_ok=True)
        save_path = os.path.join("screenshots", f"screen_{int(time.time())}.png")

    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
    except Exception as e:
        # Fallback dummy file creation if GUI screen capture library is missing
        with open(save_path, "w") as f:
            f.write(f"Screenshot capture stub (error: {e})")
    
    return os.path.abspath(save_path)
