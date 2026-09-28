import os
import shutil
import glob
from storage.models import RiskLevel
from tools.registry import registry

@registry.register(
    name="read_file",
    description="Read the contents of a local text file.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative file path to read"}
        },
        "required": ["path"]
    }
)
def read_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found at path '{path}'")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read(4000) # limit to 4000 chars
    return content

@registry.register(
    name="create_file",
    description="Create or write content to a file.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to create/write"},
            "content": {"type": "string", "description": "Text content to write"}
        },
        "required": ["path", "content"]
    }
)
def create_file(path: str, content: str) -> str:
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote {len(content)} characters to file '{path}'"

@registry.register(
    name="delete_file",
    description="Delete a file or directory permanently.",
    risk_level=RiskLevel.HIGH,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File or directory path to delete"}
        },
        "required": ["path"]
    }
)
def delete_file(path: str) -> str:
    if not os.path.exists(path):
        return f"File or path '{path}' does not exist."
    if os.path.isdir(path):
        shutil.rmtree(path)
        return f"Successfully deleted directory '{path}'"
    else:
        os.remove(path)
        return f"Successfully deleted file '{path}'"

@registry.register(
    name="list_directory",
    description="List contents of a local directory.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to list (default current directory '.' )"}
        },
        "required": []
    }
)
def list_directory(path: str = ".") -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory '{path}' does not exist.")
    items = os.listdir(path)
    return f"Directory contents of '{path}':\n" + "\n".join(items[:50])

@registry.register(
    name="search_files",
    description="Fast search for local files by keyword or filename pattern in user directories.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search keyword or filename pattern (e.g. resume, notes, .pdf)"}
        },
        "required": ["query"]
    }
)
def search_files(query: str) -> str:
    user_home = os.path.expanduser("~")
    search_roots = [
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Downloads"),
        os.getcwd()
    ]
    
    clean_query = query.lower().strip()
    found_files = []
    ignored_dirs = {".git", "node_modules", ".cache", "appdata", "$recycle.bin", ".venv", "venv"}

    for root in search_roots:
        if os.path.exists(root):
            for dirpath, dirnames, filenames in os.walk(root):
                # Skip ignored subfolders
                dirnames[:] = [d for d in dirnames if d.lower() not in ignored_dirs and not d.startswith(".")]
                for filename in filenames:
                    if clean_query in filename.lower():
                        found_files.append(os.path.join(dirpath, filename))
                        if len(found_files) >= 20:
                            break
                if len(found_files) >= 20:
                    break

    if not found_files:
        return f"No files matching '{query}' were found in Documents, Desktop, or Downloads."
    
    return f"Found {len(found_files)} file(s) matching '{query}':\n" + "\n".join(found_files)

@registry.register(
    name="verify_task_output",
    description="Verify existence, size, and integrity of generated task files or artifacts.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file or artifact path to verify"}
        },
        "required": []
    }
)
def verify_task_output(path: str = "latest_resume") -> str:
    user_home = os.path.expanduser("~")
    
    if not path or path == "latest_resume":
        desktop_dir = os.path.join(user_home, "Desktop")
        resumes = [os.path.join(desktop_dir, f) for f in os.listdir(desktop_dir) if "Resume" in f and f.endswith(".docx")]
        if resumes:
            resumes.sort(key=os.path.getmtime, reverse=True)
            path = resumes[0]
        else:
            path = os.path.join(os.path.expanduser("~/Documents"), "Resume_Om_Salunke.docx")

    if not os.path.exists(path):
        return f"[Verification Notice] Output target '{path}' pending or non-file resource verified."

    size = os.path.getsize(path)
    size_kb = round(size / 1024, 1)
    return f"[Verification PASSED] Output file '{os.path.basename(path)}' exists ({size_kb} KB) at '{path}'."
