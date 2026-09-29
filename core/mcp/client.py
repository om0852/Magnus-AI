import os
import sys
import json
import glob
import subprocess
from typing import Dict, Any, List, Optional

class MCPClientManager:
    """
    MCP (Model Context Protocol) Client & Integration Manager for Magnas AI.
    Loads MCP server configurations from global Gemini/Antigravity mcp_config.json and
    schema definitions from C:\\Users\\salun\\.gemini\\antigravity-ide\\mcp\\<server_name>\\.
    """

    def __init__(self, config_path: str = r"C:\Users\salun\.gemini\config\mcp_config.json"):
        self.config_path = os.path.abspath(config_path)
        self.mcp_schema_root = r"C:\Users\salun\.gemini\antigravity-ide\mcp"
        self.servers_config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("mcpServers", {})
        except Exception as e:
            print(f"[MCPClientManager Error] Failed to load mcp_config.json: {e}")
            return {}

    def list_mcp_servers(self) -> List[Dict[str, Any]]:
        self.servers_config = self._load_config()
        result = []
        for name, cfg in self.servers_config.items():
            schema_dir = os.path.join(self.mcp_schema_root, name)
            tool_count = len(glob.glob(os.path.join(schema_dir, "*.json"))) if os.path.exists(schema_dir) else 0
            result.append({
                "server_name": name,
                "command": cfg.get("command", ""),
                "args": cfg.get("args", []),
                "schema_tools_count": tool_count
            })
        return result

    def list_mcp_tools(self, server_name: str) -> List[Dict[str, Any]]:
        schema_dir = os.path.join(self.mcp_schema_root, server_name)
        if not os.path.exists(schema_dir):
            return []

        tools = []
        for fpath in glob.glob(os.path.join(schema_dir, "*.json")):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    tool_data = json.load(f)
                    tools.append(tool_data)
            except Exception:
                pass
        return sorted(tools, key=lambda t: t.get("name", ""))

    def call_mcp_tool(self, server_name: str, tool_name: str, arguments: dict = None) -> Dict[str, Any]:
        self.servers_config = self._load_config()
        if server_name not in self.servers_config:
            return {"success": False, "error": f"MCP Server '{server_name}' not configured in mcp_config.json."}

        server_cfg = self.servers_config[server_name]
        cmd = server_cfg.get("command", "")
        args = server_cfg.get("args", [])
        env = {**os.environ, **server_cfg.get("env", {})}

        # Construct JSON-RPC 2.0 stdio request payload
        jsonrpc_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        full_cmd = [cmd] + args
        try:
            req_str = json.dumps(jsonrpc_req) + "\n"
            proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            try:
                stdout, stderr = proc.communicate(input=req_str, timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()

            if stdout:
                lines = [l.strip() for l in stdout.splitlines() if l.strip()]
                for line in reversed(lines):
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            resp = json.loads(line)
                            if "result" in resp:
                                return {"success": True, "output": resp["result"], "raw": resp}
                            elif "error" in resp:
                                return {"success": False, "error": resp["error"]}
                        except Exception:
                            pass

            return {
                "success": True,
                "output": f"Executed MCP tool '{tool_name}' on server '{server_name}'.",
                "stdout": stdout[:1000] if stdout else "",
                "stderr": stderr[:500] if stderr else ""
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"MCP Server '{server_name}' execution timed out after 10 seconds."}
        except Exception as e:
            return {"success": False, "error": f"Failed to execute MCP tool '{tool_name}': {e}"}

mcp_client = MCPClientManager()
