import argparse
import sys
import threading
import time

from .client import BaileysClient
from .exceptions import BridgeError


def _wait(event: threading.Event, timeout: float, label: str) -> bool:
    if event.wait(timeout):
        return True
    print(f"[warnect] timeout waiting for {label}", file=sys.stderr)
    return False


def cmd_qr(args: argparse.Namespace) -> int:
    ready = threading.Event()
    client = BaileysClient(auth_dir=args.auth_dir, log_level=args.log_level)

    def on_qr(qr: str) -> None:
        print("QR:", qr)
        print("Scan QR di WhatsApp > Perangkat Tertaut.", file=sys.stderr)

    client.on("qr", on_qr)
    client.on("ready", lambda _data: ready.set())
    client.on("connection", lambda data: print("connection:", data))
    client.start()
    ok = _wait(ready, args.timeout, "connection")
    client.stop()
    return 0 if ok else 1


def cmd_pair(args: argparse.Namespace) -> int:
    ready = threading.Event()
    client = BaileysClient(auth_dir=args.auth_dir, log_level=args.log_level)
    client.on("ready", lambda _data: ready.set())
    client.on("connection", lambda data: print("connection:", data))
    client.start()
    code = client.request_pairing_code(args.number)
    print("Pairing code:", code.get("code") if isinstance(code, dict) else code)
    ok = _wait(ready, args.timeout, "pairing")
    client.stop()
    return 0 if ok else 1


def cmd_send(args: argparse.Namespace) -> int:
    ready = threading.Event()
    client = BaileysClient(auth_dir=args.auth_dir, log_level=args.log_level)
    client.on("ready", lambda _data: ready.set())
    client.start()
    if not _wait(ready, args.timeout, "connection"):
        client.stop()
        return 1
    try:
        client.send_text(args.to, args.text)
        print("sent")
    except BridgeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        client.stop()
        return 1
    client.stop()
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    client = BaileysClient(auth_dir=args.auth_dir, log_level=args.log_level)
    client.on("qr", lambda qr: print("QR:", qr))
    client.on("ready", lambda data: print("ready:", data))
    client.on("connection", lambda data: print("connection:", data))
    client.on("reconnect", lambda data: print("reconnect:", data))
    client.on("error", lambda data: print("error:", data))
    client.on("message", lambda msg: print("message:", msg.get("chat"), msg.get("text")))
    client.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="warnect", description="warnect WhatsApp client")
    parser.add_argument("--auth-dir", default="auth")
    parser.add_argument("--log-level", default="info", choices=["error", "warn", "info", "debug"])
    parser.add_argument("--timeout", type=float, default=60.0)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("qr", help="print QR and wait for connection").set_defaults(func=cmd_qr)

    pair = sub.add_parser("pair", help="request pairing code")
    pair.add_argument("--number", required=True)
    pair.set_defaults(func=cmd_pair)

    send = sub.add_parser("send", help="send a text message")
    send.add_argument("--to", required=True, help="target JID")
    send.add_argument("--text", required=True)
    send.set_defaults(func=cmd_send)

    sub.add_parser("run", help="run and print events").set_defaults(func=cmd_run)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
