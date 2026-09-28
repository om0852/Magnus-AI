from storage.models import RiskLevel
from tools.registry import registry

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

@registry.register(
    name="type_text",
    description="Simulate typing text using keyboard.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text string to type"}
        },
        "required": ["text"]
    }
)
def type_text(text: str) -> str:
    if HAS_PYAUTOGUI:
        pyautogui.write(text, interval=0.02)
        return f"Typed text ({len(text)} chars)"
    else:
        return f"[Simulated Type Text]: {text}"

@registry.register(
    name="press_key",
    description="Press a specific key or key combination (e.g. enter, space, ctrl+c, alt+tab).",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key name or hotkey combo separated by '+' (e.g., enter, ctrl+c, alt+tab)"}
        },
        "required": ["key"]
    }
)
def press_key(key: str) -> str:
    keys = [k.strip().lower() for k in key.split("+")]
    if HAS_PYAUTOGUI:
        if len(keys) > 1:
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(keys[0])
        return f"Pressed key/hotkey: {' + '.join(keys)}"
    else:
        return f"[Simulated Key Press]: {' + '.join(keys)}"

@registry.register(
    name="click_mouse",
    description="Click at screen coordinates (x, y) or current mouse position.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "Optional X screen coordinate"},
            "y": {"type": "integer", "description": "Optional Y screen coordinate"},
            "clicks": {"type": "integer", "description": "Number of clicks (1 or 2)"},
            "button": {"type": "string", "description": "Mouse button: 'left', 'right', 'middle'"}
        },
        "required": []
    }
)
def click_mouse(x: int = None, y: int = None, clicks: int = 1, button: str = "left") -> str:
    if HAS_PYAUTOGUI:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        else:
            pyautogui.click(clicks=clicks, button=button)
        return f"Clicked {button} button {clicks} time(s)"
    else:
        return f"[Simulated Mouse Click]: {button} at ({x}, {y})"

@registry.register(
    name="scroll_mouse",
    description="Scroll mouse wheel up or down.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "amount": {"type": "integer", "description": "Positive for scroll up, negative for scroll down"}
        },
        "required": ["amount"]
    }
)
def scroll_mouse(amount: int) -> str:
    if HAS_PYAUTOGUI:
        pyautogui.scroll(amount)
        return f"Scrolled mouse wheel by {amount} units."
    else:
        return f"[Simulated Scroll]: {amount} units"
