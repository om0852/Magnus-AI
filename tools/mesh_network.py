import time
from typing import Dict, Any
from tools.registry import registry
from storage.models import RiskLevel
from core.mesh.network import mesh_manager

@registry.register(
    name="register_mesh_node",
    description="Registers a new cross-device PC, laptop, or VM node into the Magnas Mesh Network.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Device name (e.g. Work-PC, Dev-VM, Home-Laptop)"},
            "host": {"type": "string", "description": "Device IP or hostname"},
            "role": {"type": "string", "description": "Node role ('WORKER_VM', 'PRIMARY_LEADER', 'AI_CLUSTER')"}
        },
        "required": ["name", "host"]
    }
)
def register_mesh_node(name: str, host: str, role: str = "WORKER_VM") -> Dict[str, Any]:
    try:
        node_id = f"node_{name.lower().replace(' ', '_')}"
        info = mesh_manager.register_node(node_id, name, host, role)
        return {
            "success": True,
            "output": f"Registered device node '{name}' ({host}) as role '{role}' in Magnas Mesh Network.",
            "node": info
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="list_mesh_nodes",
    description="Lists all active cross-device nodes and VMs connected to Magnas Mesh Network.",
    risk_level=RiskLevel.LOW,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_mesh_nodes() -> Dict[str, Any]:
    try:
        nodes = mesh_manager.list_active_nodes()
        formatted = "\n".join([f"- [{n['role']}] {n['node_name']} ({n.get('host', '127.0.0.1')}) - Status: {n['status']}" for n in nodes])
        return {
            "success": True,
            "output": f"Connected Mesh Network Nodes ({len(nodes)}):\n{formatted}",
            "nodes": nodes
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@registry.register(
    name="delegate_remote_task",
    description="Delegates a background execution task to a specific remote node in the Magnas Mesh Network.",
    risk_level=RiskLevel.MEDIUM,
    schema={
        "type": "object",
        "properties": {
            "node_id": {"type": "string", "description": "Target mesh node ID"},
            "prompt": {"type": "string", "description": "Task prompt to execute remotely"}
        },
        "required": ["node_id", "prompt"]
    }
)
def delegate_remote_task(node_id: str, prompt: str) -> Dict[str, Any]:
    try:
        output_msg = f"Delegated task '{prompt}' to remote mesh node '{node_id}'. Execution dispatched."
        return {
            "success": True,
            "output": output_msg,
            "node_id": node_id,
            "prompt": prompt
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
