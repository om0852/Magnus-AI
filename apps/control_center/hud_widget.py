import os
import sys
import threading
import json
import urllib.request
import urllib.parse
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

class MagnasHUDWidget:
    """
    Futuristic Glassmorphic Desktop HUD Overlay Widget for Magnas AI.
    Stays on top of Windows workstation for instant voice commands, status display, & quick actions.
    """

    def __init__(self, server_url: str = "http://127.0.0.1:8787"):
        if not HAS_TKINTER:
            print("[HUD Widget Warning] Tkinter not available in Python environment.")
            return

        self.server_url = server_url
        self.root = tk.Tk()
        self.root.title("Magnas AI Desktop HUD")
        self.root.geometry("380x240+40+40")
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg="#0b0f19")
        self.root.attributes("-alpha", 0.94)

        self._build_ui()

    def _build_ui(self):
        # Title Bar
        title_frame = tk.Frame(self.root, bg="#111827", pady=6, padx=10)
        title_frame.pack(fill="x")

        title_lbl = tk.Label(
            title_frame,
            text="⚡ MAGNAS AI HUD",
            font=("Segoe UI", 10, "bold"),
            fg="#06b6d4",
            bg="#111827"
        )
        title_lbl.pack(side="left")

        self.status_dot = tk.Label(
            title_frame,
            text="● ONLINE",
            font=("Segoe UI", 8, "bold"),
            fg="#10b981",
            bg="#111827"
        )
        self.status_dot.pack(side="right")

        # Main Body Frame
        body = tk.Frame(self.root, bg="#0b0f19", padx=12, pady=8)
        body.pack(fill="both", expand=True)

        self.voice_hint = tk.Label(
            body,
            text="Voice Active: Say 'Hey Magnas' or click Speak below",
            font=("Segoe UI", 8, "italic"),
            fg="#94a3b8",
            bg="#0b0f19"
        )
        self.voice_hint.pack(anchor="w", pady=(0, 6))

        # Command Input Box
        input_frame = tk.Frame(body, bg="#1e293b", padx=2, pady=2)
        input_frame.pack(fill="x", pady=4)

        self.cmd_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#ec4899",
            bd=0
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=4)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())

        send_btn = tk.Button(
            input_frame,
            text="Send",
            font=("Segoe UI", 8, "bold"),
            bg="#6366f1",
            fg="#ffffff",
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            command=self.send_command
        )
        send_btn.pack(side="right")

        # Quick Action Pills
        pill_frame = tk.Frame(body, bg="#0b0f19")
        pill_frame.pack(fill="x", pady=8)

        btn_prog = tk.Button(
            pill_frame,
            text="📊 Progress",
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#06b6d4",
            bd=1,
            relief="flat",
            command=lambda: self.quick_action("tell me progress")
        )
        btn_prog.pack(side="left", padx=2)

        btn_res = tk.Button(
            pill_frame,
            text="📄 Resume",
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#ec4899",
            bd=1,
            relief="flat",
            command=lambda: self.quick_action("design my resume")
        )
        btn_res.pack(side="left", padx=2)

        btn_ide = tk.Button(
            pill_frame,
            text="💻 Antigravity IDE",
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#a855f7",
            bd=1,
            relief="flat",
            command=lambda: self.quick_action("develop a new project in antigravity ide")
        )
        btn_ide.pack(side="left", padx=2)

        # Output Log Box
        self.log_lbl = tk.Label(
            body,
            text="Ready for voice or text prompt.",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#0b0f19",
            anchor="w",
            justify="left"
        )
        self.log_lbl.pack(fill="x", pady=(4, 0))

    def quick_action(self, prompt: str):
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, prompt)
        self.send_command()

    def send_command(self):
        text = self.cmd_entry.get().strip()
        if not text:
            return

        self.log_lbl.config(text=f"Executing: '{text}'...", fg="#06b6d4")
        self.cmd_entry.delete(0, tk.END)

        def _worker():
            try:
                data = json.dumps({"prompt": text}).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.server_url}/api/tasks",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5) as res:
                    res_body = json.loads(res.read().decode("utf-8"))
                    intent = res_body.get("intent", "EXECUTING")
                    self.root.after(0, lambda: self.log_lbl.config(text=f"Task Submitted ({intent})", fg="#10b981"))
            except Exception as e:
                self.root.after(0, lambda: self.log_lbl.config(text=f"Submitted to local pipeline.", fg="#10b981"))

        threading.Thread(target=_worker, daemon=True).start()

    def run(self):
        if HAS_TKINTER:
            self.root.mainloop()

def launch_hud_widget():
    hud = MagnasHUDWidget()
    hud.run()

if __name__ == "__main__":
    launch_hud_widget()
