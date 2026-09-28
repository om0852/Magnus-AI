import json
import random
import os
from typing import List, Dict, Any

INTENTS = [
    "OPEN_APP",
    "CLOSE_APP",
    "SEARCH_WEB",
    "OPEN_WEBSITE",
    "CREATE_FILE",
    "READ_FILE",
    "DELETE_FILE",
    "CHANGE_VOLUME",
    "TAKE_SCREENSHOT",
    "TYPE_TEXT",
    "PRESS_KEY",
    "CLICK_MOUSE",
    "SCROLL_MOUSE",
    "EXECUTE_COMMAND",
    "DESIGN_RESUME",
    "UNKNOWN"
]

APPS = [
    "chrome", "google chrome", "firefox", "mozilla firefox",
    "antigravity ide", "antigravity", "chatgpt", "chat gpt",
    "file explorer", "explorer", "my computer",
    "task manager", "settings", "cmd", "command prompt",
    "powershell", "terminal", "notepad", "calculator", "calc",
    "paint", "snipping tool", "discord", "spotify", "vscode", "vs code"
]

SITES = [
    "chatgpt", "youtube", "google", "github", "wikipedia", "stack overflow",
    "reddit", "twitter", "amazon", "bing", "duckduckgo", "huggingface"
]

QUERIES = [
    "react performance optimization", "python async design patterns",
    "windows command line cheat sheet", "magnas computer control platform",
    "latest nodejs lts download", "how to train custom transformer models",
    "fastapi web framework tutorial", "sqlite async python tutorial",
    "pytorch vs ONNX CPU inference benchmarks", "best dark mode CSS themes"
]

KEYS = [
    "enter", "space", "ctrl+c", "ctrl+v", "ctrl+z", "alt+tab", "backspace",
    "tab", "escape", "ctrl+a", "ctrl+s", "delete", "f5"
]

FILE_EXTS = [".txt", ".json", ".py", ".md", ".log", ".tmp", ".csv", ".yaml"]

def generate_dataset(num_samples: int = 10000) -> List[Dict[str, Any]]:
    dataset = []
    
    for _ in range(num_samples):
        intent = random.choice(INTENTS)
        entities = {}
        
        if intent == "DESIGN_RESUME":
            name = random.choice(["Om Salunke", "Alex Rivera", "Jordan Smith"])
            job_title = random.choice(["FULL STACK JAVA DEVELOPER", "Software Development Engineer (SDE)", "Full Stack Developer", "AI Engineer", "Python Backend Developer"])
            templates = [
                f"design my resume in word",
                f"design my resume for {job_title}",
                f"create a professional resume in word",
                f"generate resume for {name} as {job_title}",
                f"make a resume document in word",
                f"build my resume in microsoft word",
                f"create resume for {job_title} in word",
                f"generate sde resume for me for role {job_title}",
                f"generate resume for {job_title}",
                f"generate resume",
                f"create new resume",
                f"generate sde resume",
                f"design sde resume in word",
                f"make new resume for role {job_title}"
            ]
            text = random.choice(templates)
            entities = {"name": name, "title": job_title}

        elif intent == "OPEN_APP":
            app = random.choice(APPS)
            templates = [
                f"open {app}",
                f"launch {app} please",
                f"can you open {app}",
                f"start {app} application",
                f"bring up {app}",
                f"run {app}",
                f"switch to {app}"
            ]
            text = random.choice(templates)
            entities = {"application": app}

        elif intent == "CLOSE_APP":
            app = random.choice(APPS)
            templates = [
                f"close {app}",
                f"exit {app} right now",
                f"terminate {app}",
                f"kill {app} process"
            ]
            text = random.choice(templates)
            entities = {"application": app}

        elif intent == "SEARCH_WEB":
            query = random.choice(QUERIES)
            site = random.choice(SITES)
            templates = [
                f"search {site} for {query}",
                f"search for {query} on {site}",
                f"look up {query} on {site}"
            ]
            text = random.choice(templates)
            entities = {"query": query, "site": site}

        elif intent == "OPEN_WEBSITE":
            site_name = random.choice(SITES).replace(" ", "")
            url = f"https://{site_name}.com" if site_name != "chatgpt" else "https://chatgpt.com"
            templates = [
                f"open {url}",
                f"go to {url}",
                f"navigate to {url}"
            ]
            text = random.choice(templates)
            entities = {"url": url}

        elif intent == "CREATE_FILE":
            name = f"doc_{random.randint(1, 500)}{random.choice(FILE_EXTS)}"
            content = "sample content"
            templates = [
                f"create file {name} with content {content}",
                f"write file {name}"
            ]
            text = random.choice(templates)
            entities = {"path": name, "content": content}

        elif intent == "READ_FILE":
            name = f"notes_{random.randint(1, 500)}{random.choice(FILE_EXTS)}"
            templates = [
                f"read file {name}",
                f"show contents of {name}"
            ]
            text = random.choice(templates)
            entities = {"path": name}

        elif intent == "DELETE_FILE":
            name = f"temp_{random.randint(1, 500)}{random.choice(FILE_EXTS)}"
            templates = [
                f"delete file {name}",
                f"remove file {name}"
            ]
            text = random.choice(templates)
            entities = {"path": name}

        elif intent == "CHANGE_VOLUME":
            amount = random.choice([10, 20, 50])
            direction = random.choice(["increase", "decrease", "mute"])
            templates = [
                f"{direction} volume by {amount} percent",
                f"turn {direction} volume"
            ]
            text = random.choice(templates)
            norm_dir = "increase" if "increase" in direction or "up" in direction else ("decrease" if "decrease" in direction or "down" in direction else "mute")
            entities = {"amount": amount, "direction": norm_dir}

        elif intent == "TAKE_SCREENSHOT":
            templates = ["take screenshot", "capture screen"]
            text = random.choice(templates)
            entities = {}

        elif intent == "TYPE_TEXT":
            msg = "hello world"
            templates = [f"type {msg}", f"write text {msg}"]
            text = random.choice(templates)
            entities = {"text": msg}

        elif intent == "PRESS_KEY":
            key = random.choice(KEYS)
            templates = [f"press {key}", f"hit {key} key"]
            text = random.choice(templates)
            entities = {"key": key}

        elif intent == "CLICK_MOUSE":
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            templates = [f"click mouse at {x} {y}"]
            text = random.choice(templates)
            entities = {"x": x, "y": y}

        elif intent == "SCROLL_MOUSE":
            templates = ["scroll mouse by 200"]
            text = random.choice(templates)
            entities = {"amount": 200}

        elif intent == "EXECUTE_COMMAND":
            templates = ["run command dir"]
            text = random.choice(templates)
            entities = {"command": "dir"}

        else: # UNKNOWN
            templates = ["what is the weather in Tokyo", "random gibberish text"]
            text = random.choice(templates)
            intent = "UNKNOWN"

        dataset.append({
            "text": text,
            "intent": intent,
            "entities": entities
        })

    return dataset

def save_dataset(filepath: str, num_samples: int = 10000):
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    ds = generate_dataset(num_samples)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(ds, f, indent=2)

if __name__ == "__main__":
    save_dataset("nlp/training/datasets/commands_dataset.json", 10000)
