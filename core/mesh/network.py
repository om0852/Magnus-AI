import os
import json
import time
from typing import Dict, Any, List, Optional

class MeshNetworkManager:
    """
    Cross-Device Mesh Network Manager for Magnas AI.
    Synchronizes tasks, system status, and remote execution across PCs, Laptops, & VMs.
    """

    def __init__(self, node_name: str = "Local-Laptop-Node"):
        self.node_name = node_name
        self.node_id = f"node_{os.uname().nodename if hasattr(os, 'uname') else 'win_node'}"
        self.nodes: Dict[str, Dict[str, Any]] = {
            self.node_id: {
                "node_id": self.node_id,
                "node_name": self.node_name,
                "role": "PRIMARY_LEADER",
                "status": "ONLINE",
                "last_heartbeat": time.time()
            }
        }

    def register_node(self, node_id: str, name: str, host: str, role: str = "WORKER_VM") -> Dict[str, Any]:
        node_info = {
            "node_id": node_id,
            "node_name": name,
            "host": host,
            "role": role,
            "status": "ONLINE",
            "last_heartbeat": time.time()
        }
        self.nodes[node_id] = node_info
        return node_info

    def list_active_nodes(self) -> List[Dict[str, Any]]:
        return list(self.nodes.values())

mesh_manager = MeshNetworkManager()
