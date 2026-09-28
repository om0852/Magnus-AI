import webbrowser
import urllib.parse
import urllib.request
import re
import html
import uuid
import time
from typing import Dict, Any, Optional
from storage.models import RiskLevel, AuditLog
from tools.registry import registry

@registry.register(
    name="open_url",
    description="Open a web page URL in the default web browser.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The web URL to open (e.g., https://google.com)"}
        },
        "required": ["url"]
    }
)
def open_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened web URL '{url}' in default browser."

@registry.register(
    name="browser_search",
    description="Search the web or specific site (e.g. youtube, google, github, wikipedia) for a query.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search terms"},
            "site": {"type": "string", "description": "Target site (e.g. youtube, google, github, wikipedia)"}
        },
        "required": ["query"]
    }
)
def browser_search(query: str, site: str = "google") -> str:
    encoded_query = urllib.parse.quote(query)
    site_lower = site.lower() if site else "google"
    
    if "youtube" in site_lower:
        target_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    elif "github" in site_lower:
        target_url = f"https://github.com/search?q={encoded_query}"
    elif "wikipedia" in site_lower:
        target_url = f"https://en.wikipedia.org/wiki/Special:Search?search={encoded_query}"
    else:
        target_url = f"https://www.google.com/search?q={encoded_query}"

    webbrowser.open(target_url)
    return f"Performed search for '{query}' on {site_lower}: {target_url}"

@registry.register(
    name="read_web_documentation",
    description="Fetch, extract, and summarize web documentation, API references, or articles from a URL.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Documentation or article web URL to fetch and read"}
        },
        "required": ["url"]
    }
)
def read_web_documentation(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MagnasAI/2.0 DocumentationReader"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            raw_html = response.read().decode("utf-8", errors="replace")

        # Strip scripts and style tags
        clean = re.sub(r"<(script|style).*?>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        # Extract text content
        text = re.sub(r"<[^>]+>", " ", clean)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()

        snippet = text[:3000] if len(text) > 3000 else text
        return f"[Documentation Extracted from {url}]\nContent Summary:\n{snippet}\n..."
    except Exception as e:
        # Fallback: Open URL in browser
        webbrowser.open(url)
        return f"Opened web documentation URL '{url}' in browser (direct fetch notice: {e})."

@registry.register(
    name="automate_platform_login",
    description="Automate platform login or account registration form entry on a target website.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "platform_url": {"type": "string", "description": "Target login or sign-up portal URL"},
            "action_type": {"type": "string", "description": "Action type: 'login' or 'create_account'"},
            "username": {"type": "string", "description": "Username or email"},
            "password": {"type": "string", "description": "Password or credential string"}
        },
        "required": ["platform_url"]
    }
)
def automate_platform_login(platform_url: str, action_type: str = "login", username: str = "", password: str = "") -> str:
    if not platform_url.startswith("http://") and not platform_url.startswith("https://"):
        platform_url = "https://" + platform_url

    # Open portal in browser
    webbrowser.open(platform_url)
    time.sleep(1.5)

    try:
        import pyautogui
        # Focus input and simulate credential fill safely
        pyautogui.write(username, interval=0.02)
        pyautogui.press('tab')
        if password:
            pyautogui.write(password, interval=0.02)
            pyautogui.press('enter')
        return f"Automated {action_type} sequence on portal '{platform_url}' for user '{username}'."
    except Exception:
        return f"Navigated to {action_type} portal '{platform_url}'. Manual confirmation enabled."
