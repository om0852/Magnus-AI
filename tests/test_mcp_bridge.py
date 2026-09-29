import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.mcp.client import mcp_client
from tools.mcp_bridge import list_mcp_servers, list_mcp_tools, call_mcp_tool

class TestMCPBridge(unittest.TestCase):
    def test_list_servers(self):
        res = list_mcp_servers()
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["servers"]), 1)

    def test_list_xtradevpilot_tools(self):
        res = list_mcp_tools("xtradevpilot")
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["tools"]), 30)

    def test_call_xtradevpilot_tool(self):
        res = call_mcp_tool("xtradevpilot", "list_tabs", {})
        self.assertTrue(res["success"])

if __name__ == "__main__":
    unittest.main()
