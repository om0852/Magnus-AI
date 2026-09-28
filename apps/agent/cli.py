import sys
import argparse
import json
import urllib.request
import urllib.error
from nlp.training.train import train_model
from nlp.training.export_onnx import export_to_onnx

BASE_URL = "http://127.0.0.1:8787"

def _http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "MagnasCLI/1.0"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def _http_post(url: str, data: dict = None) -> dict:
    json_bytes = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=json_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "MagnasCLI/1.0"},
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Magnas Local AI Computer-Control CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # magnas start
    subparsers.add_parser("start", help="Start the Magnas Daemon service")

    # magnas status
    subparsers.add_parser("status", help="Check status of Magnas Daemon")

    # magnas run "<prompt>"
    run_parser = subparsers.add_parser("run", help="Run a natural language computer command")
    run_parser.add_argument("prompt", type=str, help="Command prompt (e.g. 'open chrome')")

    # magnas approve <ticket_id>
    appr_parser = subparsers.add_parser("approve", help="Approve a pending human intervention ticket")
    appr_parser.add_argument("ticket_id", type=str, help="Ticket ID to approve")

    # magnas reject <ticket_id>
    rej_parser = subparsers.add_parser("reject", help="Reject a pending human intervention ticket")
    rej_parser.add_argument("ticket_id", type=str, help="Ticket ID to reject")

    # magnas train
    subparsers.add_parser("train", help="Train specialized NLP Transformer model & export ONNX")

    args = parser.parse_args()

    if args.command == "start":
        from apps.agent.daemon import MagnasDaemon
        daemon = MagnasDaemon()
        daemon.run()

    elif args.command == "status":
        try:
            data = _http_get(f"{BASE_URL}/api/status")
            print("Magnas System Status:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Failed to connect to Magnas daemon at {BASE_URL}: {e}")

    elif args.command == "run":
        try:
            data = _http_post(f"{BASE_URL}/api/tasks", data={"prompt": args.prompt})
            print("Task submitted successfully:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Failed to execute command: {e}")

    elif args.command == "approve":
        try:
            data = _http_post(f"{BASE_URL}/api/approvals/{args.ticket_id}/approve")
            print("Ticket approved:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Approval failed: {e}")

    elif args.command == "reject":
        try:
            data = _http_post(f"{BASE_URL}/api/approvals/{args.ticket_id}/reject")
            print("Ticket rejected:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Rejection failed: {e}")

    elif args.command == "train":
        print("Starting Magnas NLP Training Pipeline...")
        train_model()
        export_to_onnx()
        print("Training & ONNX Export completed successfully!")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
