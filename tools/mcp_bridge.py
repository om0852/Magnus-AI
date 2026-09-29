from typing import Dict, Any, List
from tools.registry import registry
from storage.models import RiskLevel
from core.mcp.client import mcp_client

@registry.register(
    name="list_mcp_servers",
    description="Lists all MCP (Model Context Protocol) servers configured in global Gemini/Antigravity config (xtradevpilot, StitchMCP, codebase-trainer).",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_mcp_servers() -> Dict[str, Any]:
    try:
        servers = mcp_client.list_mcp_servers()
        formatted = "\n".join([f"- [{s['server_name']}] Cmd: {s['command']} {' '.join(s['args'])} | Schemas: {s['schema_tools_count']} tools" for s in servers])
        return {"success": True, "output": f"Configured MCP Servers ({len(servers)}):\n{formatted}", "servers": servers}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="list_mcp_tools",
    description="Lists all tools available under a specific MCP server (e.g. 'xtradevpilot', 'StitchMCP', 'codebase-trainer').",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "server_name": {"type": "string", "description": "MCP server name (e.g. xtradevpilot, StitchMCP, codebase-trainer)"}
        },
        "required": ["server_name"]
    }
)
def list_mcp_tools(server_name: str) -> Dict[str, Any]:
    try:
        tools = mcp_client.list_mcp_tools(server_name)
        if tools:
            formatted = "\n".join([f"- {t.get('name')}: {t.get('description', '')[:100]}" for t in tools])
            return {"success": True, "output": f"MCP Tools for '{server_name}' ({len(tools)}):\n{formatted}", "tools": tools}
        return {"success": True, "output": f"No MCP tool schemas found for server '{server_name}'.", "tools": []}
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="call_mcp_tool",
    description="Executes any tool on an MCP server (e.g. xtradevpilot, StitchMCP, codebase-trainer) with arguments payload.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "server_name": {"type": "string", "description": "MCP server name (e.g. xtradevpilot)"},
            "tool_name": {"type": "string", "description": "Tool name to invoke (e.g. list_tabs, navigate, open_tab, get_dom_snapshot)"},
            "arguments": {"type": "object", "description": "Arguments payload object"}
        },
        "required": ["server_name", "tool_name"]
    }
)
def call_mcp_tool(server_name: str, tool_name: str, arguments: dict = None) -> Dict[str, Any]:
    try:
        res = mcp_client.call_mcp_tool(server_name, tool_name, arguments or {})
        return res
    except Exception as e:
        return {"success": False, "error": str(e)}

# Auto-register dynamic tool aliases for xtradevpilot MCP tools
def _register_dynamic_mcp_tools():
    try:
        xtradev_tools = mcp_client.list_mcp_tools("xtradevpilot")
        for t in xtradev_tools:
            name = f"xtradevpilot_{t.get('name')}"
            desc = f"[xtradevpilot MCP] {t.get('description', '')}"
            schema = t.get("parameters", {"type": "object", "properties": {}})

            # Closure for dynamic execution
            def make_handler(tool_n):
                def handler(**kwargs):
                    return mcp_client.call_mcp_tool("xtradevpilot", tool_n, kwargs)
                return handler

            registry.register(
                name=name,
                description=desc,
                risk_level=RiskLevel.MEDIUM,
                schema=schema
            )(make_handler(t.get("name")))
    except Exception as e:
        print(f"[MCP Bridge Warning] Dynamic xtradevpilot registration: {e}")

_register_dynamic_mcp_tools()
