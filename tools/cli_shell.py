import subprocess
import os
import socket
from storage.models import RiskLevel
from tools.registry import registry

@registry.register(
    name="run_powershell_cmd",
    description="Execute an advanced PowerShell script command.",
    risk_level=RiskLevel.HIGH,
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "PowerShell command string to execute"}
        },
        "required": ["command"]
    }
)
def run_powershell_cmd(command: str) -> str:
    try:
        ps_command = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{command}"'
        res = subprocess.run(ps_command, shell=True, capture_output=True, text=True, timeout=15)
        out = (res.stdout or "") + (res.stderr or "")
        return f"PowerShell Execution (Exit Code {res.returncode}):\n{out.strip()[:2000]}"
    except Exception as e:
        return f"[PowerShell Error]: {e}"

@registry.register(
    name="package_manager_ops",
    description="Run npm, pip, maven, or git package manager commands.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "manager": {"type": "string", "description": "Package manager: 'npm', 'pip', 'mvn', 'git'"},
            "arguments": {"type": "string", "description": "Arguments string (e.g. 'install', 'push origin main')"}
        },
        "required": ["manager", "arguments"]
    }
)
def package_manager_ops(manager: str = "npm", arguments: str = "install") -> str:
    full_cmd = f"{manager} {arguments}"
    try:
        res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
        out = (res.stdout or "") + (res.stderr or "")
        return f"Package Manager '{full_cmd}' (Exit Code {res.returncode}):\n{out.strip()[:1500]}"
    except Exception as e:
        return f"[Package Manager Error]: {e}"

@registry.register(
    name="network_diagnostics",
    description="Perform network host ping, local IP lookup, or port connection checks.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "host": {"type": "string", "description": "Target hostname or IP address (default 'google.com')"},
            "port": {"type": "integer", "description": "Optional port number to check (e.g. 80, 443, 8787)"}
        },
        "required": []
    }
)
def network_diagnostics(host: str = "google.com", port: Optional[int] = None) -> str:
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        if port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            res = sock.connect_ex((host, port))
            sock.close()
            status = "OPEN/REACHABLE" if res == 0 else f"CLOSED/UNREACHABLE (code {res})"
            return f"[Network Diagnostics]: Target '{host}:{port}' status is {status}. Local Host IP: {local_ip}"
        
        # Ping host
        res = subprocess.run(f"ping -n 2 {host}", shell=True, capture_output=True, text=True)
        return f"[Network Diagnostics]: Local Host: {hostname} ({local_ip})\nPing Result for '{host}':\n{res.stdout[:500]}"
    except Exception as e:
        return f"[Network Error]: {e}"
