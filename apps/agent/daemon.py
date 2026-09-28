import asyncio
import os
import json
import http.server
import socketserver
from storage.database import Database
from core.events.bus import EventBus, default_bus
from approval.manager import ApprovalManager
from core.policy.engine import PolicyEngine
from nlp.inference.engine import InferenceEngine
from core.planner.planner import TaskPlanner
from core.tasks.machine import TaskStateMachine
import apps.control_center.web_server as web_server

try:
    import uvicorn
    HAS_UVICORN = True
except ImportError:
    HAS_UVICORN = False

class FallbackHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        static_dir = os.path.join(os.path.dirname(__file__), "..", "control_center", "static")
        super().__init__(*args, directory=os.path.abspath(static_dir), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            pending = web_server.db_ref.list_pending_tickets() if web_server.db_ref else []
            tasks = web_server.db_ref.list_tasks(limit=10) if web_server.db_ref else []
            running = [t for t in tasks if t.status in ["EXECUTING", "WAITING_APPROVAL"]]
            resp = {
                "status": "ONLINE",
                "pending_approvals": len(pending),
                "running_tasks": len(running),
                "total_tools": 12
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        elif self.path.startswith("/api/tasks"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tasks = web_server.db_ref.list_tasks(limit=50) if web_server.db_ref else []
            self.wfile.write(json.dumps([t.to_dict() for t in tasks]).encode("utf-8"))
        elif self.path == "/api/approvals":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tickets = web_server.db_ref.list_pending_tickets() if web_server.db_ref else []
            self.wfile.write(json.dumps([t.to_dict() for t in tickets]).encode("utf-8"))
        elif self.path == "/api/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tools_list = web_server.registry.list_tools()
            self.wfile.write(json.dumps(tools_list).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/tasks":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            prompt = data.get("prompt", "")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            task = loop.run_until_complete(web_server.task_machine_ref.create_task(prompt))
            task = loop.run_until_complete(web_server.task_machine_ref.process_task(task.task_id))
            loop.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(task.to_dict()).encode("utf-8"))
        elif "/api/approvals/" in self.path and self.path.endswith("/approve"):
            parts = self.path.split("/")
            ticket_id = parts[3]
            ticket = web_server.approval_mgr_ref.approve_ticket(ticket_id)
            if ticket:
                task = web_server.db_ref.get_task(ticket.task_id)
                if task:
                    task.status = "APPROVED"
                    web_server.db_ref.save_task(task)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    task = loop.run_until_complete(web_server.task_machine_ref.process_task(task.task_id))
                    loop.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "ticket": ticket.to_dict()}).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

class MagnasDaemon:
    """Continuous background service running Magnas core engine & web server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8787, db_path: str = "magnas.db"):
        self.host = host
        self.port = port
        self.db = Database(db_path)
        self.event_bus = default_bus
        self.event_bus.db = self.db
        
        self.approval_mgr = ApprovalManager(self.db)
        self.policy_engine = PolicyEngine(self.approval_mgr)
        self.nlp_engine = InferenceEngine()
        self.planner = TaskPlanner()
        self.task_machine = TaskStateMachine(
            db=self.db,
            event_bus=self.event_bus,
            nlp_engine=self.nlp_engine,
            planner=self.planner,
            policy_engine=self.policy_engine
        )

        web_server.init_web_server(self.db, self.event_bus, self.approval_mgr, self.task_machine)

    def run(self):
        print(f"==================================================")
        print(f" MAGNAS DAEMON INITIALIZED")
        print(f" Server running at: http://{self.host}:{self.port}")
        print(f"==================================================")
        
        if web_server.HAS_FASTAPI and HAS_UVICORN:
            uvicorn.run(web_server.app, host=self.host, port=self.port, log_level="info")
        else:
            print("[Notice] Running with standard Python HTTP server fallback...")
            with socketserver.TCPServer((self.host, self.port), FallbackHTTPHandler) as httpd:
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("Stopping daemon...")

if __name__ == "__main__":
    daemon = MagnasDaemon()
    daemon.run()
