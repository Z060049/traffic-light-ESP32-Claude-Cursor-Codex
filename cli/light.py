#!/usr/bin/env python3
"""AI Status Light CLI.

Send a status (yellow / green / red) to the desk traffic light over USB
serial, or run setup to wire up Cursor and Claude Code hooks.

Usage:
  light thinking | working | done | success | error | fail | idle
  light red | yellow | green | off
  light setup [--cursor] [--claude] [--alias] [--all]
  light doctor
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None


# --- constants ---------------------------------------------------------------

BAUD = 115200
SERIAL_TIMEOUT = 1.0
PROBE_TIMEOUT = 0.5

REPO_DIR = Path(__file__).resolve().parent.parent
LIGHT_PY = REPO_DIR / "cli" / "light.py"
FROM_CLAUDE_HOOK_PY = REPO_DIR / "cli" / "from_claude_hook.py"

CONFIG_DIR = Path.home() / ".config" / "ai-status-light"
PORT_CACHE = CONFIG_DIR / "port"

LOG_DIR = Path.home() / ".local" / "share" / "ai-status-light"
LOG_FILE = LOG_DIR / "light.log"

CURSOR_HOOKS_PATH = Path.home() / ".cursor" / "hooks.json"
CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

# String embedded in installed hook commands and the shell alias so we can
# detect prior installs and avoid duplicates.
MARKER = "ai-status-light"

COMMAND_MAP: dict[str, str] = {
    "thinking": "yellow",
    "working":  "yellow",
    "done":     "green",
    "success":  "green",
    "error":    "red",
    "fail":     "red",
    "idle":     "off",
    "red":      "red",
    "yellow":   "yellow",
    "green":    "green",
    "off":      "off",
}

# USB-serial chips most commonly found on cheap ESP32 dev boards. We use these
# to disambiguate when the user has multiple USB-serial devices plugged in.
KNOWN_VIDS: dict[int, str] = {
    0x1A86: "CH340/CH341",
    0x10C4: "CP210x (Silicon Labs)",
    0x0403: "FTDI",
    0x303A: "Espressif (native USB)",
}


# --- logging -----------------------------------------------------------------

def log(msg: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with LOG_FILE.open("a") as f:
            f.write(f"{ts} {msg}\n")
    except OSError:
        pass


# --- port detection ----------------------------------------------------------

def read_cached_port() -> str | None:
    try:
        port = PORT_CACHE.read_text().strip()
        return port or None
    except FileNotFoundError:
        return None


def write_cached_port(port: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PORT_CACHE.write_text(port + "\n")


def clear_cached_port() -> None:
    try:
        PORT_CACHE.unlink()
    except FileNotFoundError:
        pass


def candidate_ports() -> list[tuple[str, int]]:
    """Return [(device, score)] sorted by score descending.

    Score 100 = USB-serial chip we recognize as common on ESP32 boards.
    Score  50 = device path matches usb-serial naming conventions.
    Score   0 = unknown.
    """
    if list_ports is None:
        return []

    out: list[tuple[str, int]] = []
    for p in list_ports.comports():
        dev = p.device
        if p.vid in KNOWN_VIDS:
            out.append((dev, 100))
        elif any(s in dev for s in (
            "wchusbserial", "usbserial", "usbmodem", "ttyUSB", "ttyACM",
        )):
            out.append((dev, 50))
        else:
            out.append((dev, 0))

    out.sort(key=lambda x: -x[1])
    return out


def probe_port(device: str, timeout: float = PROBE_TIMEOUT) -> bool:
    """Open the port (without resetting the chip) and send 'ping'.
    Return True if the firmware responds with the magic string.
    """
    if serial is None:
        return False
    try:
        ser = serial.Serial()
        ser.port = device
        ser.baudrate = BAUD
        ser.dtr = False
        ser.rts = False
        ser.timeout = timeout
        ser.open()
        try:
            ser.reset_input_buffer()
            ser.write(b"ping\n")
            ser.flush()
            deadline = time.time() + timeout
            while time.time() < deadline:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line and MARKER in line:
                    return True
            return False
        finally:
            ser.close()
    except (OSError, serial.SerialException):
        return False


def detect_port() -> str | None:
    """Find an ESP32 by scanning USB-serial devices.

    Strategy:
      1. Get all candidates, sorted by VID/path score.
      2. Probe each with a 'ping' handshake; first that responds wins.
      3. If none respond, fall back to the highest-scoring candidate (the
         board may not have firmware uploaded yet, or another process is
         using the port).
    """
    candidates = candidate_ports()
    if not candidates:
        return None

    for dev, _ in candidates:
        if probe_port(dev):
            write_cached_port(dev)
            log(f"detected port via handshake: {dev}")
            return dev

    dev = candidates[0][0]
    write_cached_port(dev)
    log(f"detected port (no handshake response): {dev}")
    return dev


def find_port() -> str | None:
    """Return a port path, using the cache when valid and re-detecting on miss."""
    cached = read_cached_port()
    if cached and Path(cached).exists():
        return cached
    if cached:
        log(f"cached port {cached} no longer exists; re-detecting")
        clear_cached_port()
    return detect_port()


# --- send a single command ---------------------------------------------------

def _open_no_reset(port: str) -> "serial.Serial":
    """Open the serial port without toggling DTR/RTS, which would reset
    the ESP32 and force us to wait ~2 seconds before each send.
    """
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = BAUD
    ser.dtr = False
    ser.rts = False
    ser.timeout = SERIAL_TIMEOUT
    ser.open()
    return ser


def _try_send(port: str, color: str) -> bool:
    try:
        ser = _open_no_reset(port)
        try:
            ser.write((color + "\n").encode())
            ser.flush()
        finally:
            ser.close()
        return True
    except (OSError, serial.SerialException) as e:
        log(f"send to {port} failed: {e}")
        return False


def send_command(color: str) -> bool:
    if serial is None:
        print("pyserial is not installed. Run: pip3 install pyserial",
              file=sys.stderr)
        return False

    port = find_port()
    if port is None:
        msg = "no ESP32 serial port found. Plug in the board, or run: light doctor"
        print(msg, file=sys.stderr)
        log(msg)
        return False

    if _try_send(port, color):
        log(f"sent {color} to {port}")
        return True

    # Port may have moved (e.g. board re-enumerated). Invalidate cache and
    # try once more with a fresh scan.
    clear_cached_port()
    port2 = detect_port()
    if not port2 or port2 == port:
        return False
    if _try_send(port2, color):
        log(f"sent {color} to {port2} (after re-detect)")
        return True
    return False


# --- status command ----------------------------------------------------------

def cmd_status(input_cmd: str) -> int:
    color = COMMAND_MAP[input_cmd]
    return 0 if send_command(color) else 1


# --- shared json/file helpers ------------------------------------------------

def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = path.parent / f"{path.name}.bak.{ts}"
    shutil.copy2(path, bak)
    return bak


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text() or "{}")
    except json.JSONDecodeError as e:
        print(f"warning: {path} is not valid JSON ({e}); skipping", file=sys.stderr)
        return None


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def has_marker(node: Any) -> bool:
    if isinstance(node, str):
        return MARKER in node
    if isinstance(node, dict):
        return any(has_marker(v) for v in node.values())
    if isinstance(node, list):
        return any(has_marker(v) for v in node)
    return False


# --- hook commands -----------------------------------------------------------

def hook_command(status: str) -> str:
    """Shell command we install into hook configs. The trailing
    `# ai-status-light` is a POSIX-shell comment that lets us recognise
    our own entries on re-runs without affecting execution.
    """
    return f'/usr/bin/env python3 "{LIGHT_PY}" {status}  # {MARKER}'


def claude_posttool_command() -> str:
    return f'/usr/bin/env python3 "{FROM_CLAUDE_HOOK_PY}"  # {MARKER}'


# --- cursor hooks ------------------------------------------------------------

def install_cursor_hooks() -> None:
    path = CURSOR_HOOKS_PATH
    config = load_json(path, {"version": 1, "hooks": {}})
    if config is None:
        return
    if not isinstance(config, dict):
        print(f"  cursor: {path} is not a JSON object; skipping")
        return

    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print(f"  cursor: {path} has malformed 'hooks'; skipping")
        return

    backup = backup_file(path)

    plan = [
        ("beforeSubmitPrompt", hook_command("thinking")),
        ("stop",               hook_command("done")),
    ]

    changed = False
    for event, cmd in plan:
        entries = hooks.setdefault(event, [])
        if not isinstance(entries, list):
            print(f"  cursor: {event} is not a list; skipping")
            continue
        if any(has_marker(e) for e in entries):
            print(f"  cursor: {event} already has {MARKER} hook (skipped)")
            continue
        entries.append({"command": cmd})
        print(f"  cursor: added {event}")
        changed = True

    if not changed:
        if backup:
            backup.unlink()
        return

    save_json(path, config)
    print(f"  cursor: wrote {path}")
    if backup:
        print(f"  cursor: backup at {backup}")


# --- claude code hooks -------------------------------------------------------

def _claude_event_entry(matcher: str, command: str) -> dict:
    return {
        "matcher": matcher,
        "hooks": [{"type": "command", "command": command}],
    }


def install_claude_hooks() -> None:
    path = CLAUDE_SETTINGS_PATH
    config = load_json(path, {})
    if config is None:
        return
    if not isinstance(config, dict):
        print(f"  claude: {path} is not a JSON object; skipping")
        return

    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print(f"  claude: {path} has malformed 'hooks'; skipping")
        return

    backup = backup_file(path)

    plan = [
        ("PreToolUse",  hook_command("thinking")),
        ("Stop",        hook_command("done")),
        ("PostToolUse", claude_posttool_command()),
    ]

    changed = False
    for event, cmd in plan:
        entries = hooks.setdefault(event, [])
        if not isinstance(entries, list):
            print(f"  claude: {event} is not a list; skipping")
            continue
        if any(has_marker(e) for e in entries):
            print(f"  claude: {event} already has {MARKER} hook (skipped)")
            continue
        entries.append(_claude_event_entry("", cmd))
        print(f"  claude: added {event}")
        changed = True

    if not changed:
        if backup:
            backup.unlink()
        return

    save_json(path, config)
    print(f"  claude: wrote {path}")
    if backup:
        print(f"  claude: backup at {backup}")


# --- shell alias -------------------------------------------------------------

def shell_rc_path() -> Path:
    shell = os.environ.get("SHELL", "")
    home = Path.home()
    if "zsh" in shell:
        return home / ".zshrc"
    if "bash" in shell:
        return home / ".bashrc"
    return home / ".profile"


def install_alias() -> None:
    rc = shell_rc_path()
    rc.parent.mkdir(parents=True, exist_ok=True)
    existing = rc.read_text() if rc.exists() else ""
    if MARKER in existing and "alias light=" in existing:
        print(f"  alias: already in {rc} (skipped)")
        return

    block = (
        f"\n# {MARKER}\n"
        f"alias light='/usr/bin/env python3 \"{LIGHT_PY}\"'\n"
    )
    with rc.open("a") as f:
        f.write(block)
    print(f"  alias: appended to {rc}")
    print(f"  alias: open a new terminal, or run `source {rc}`, to use `light`")


# --- setup -------------------------------------------------------------------

def cmd_setup(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="light setup", add_help=True)
    ap.add_argument("--cursor", action="store_true", help="install Cursor hooks")
    ap.add_argument("--claude", action="store_true", help="install Claude Code hooks")
    ap.add_argument("--alias",  action="store_true", help="install shell alias")
    ap.add_argument("--all",    action="store_true", help="all of the above (default)")
    args = ap.parse_args(argv)

    do_cursor = args.cursor or args.all
    do_claude = args.claude or args.all
    do_alias  = args.alias  or args.all
    if not (do_cursor or do_claude or do_alias):
        do_cursor = do_claude = do_alias = True

    print("AI Status Light setup")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  logs:  {LOG_DIR}")

    if serial is None:
        print("  port:  pyserial is not installed yet; run pip3 install pyserial")
    else:
        port = find_port()
        if port:
            print(f"  port:  {port}")
        else:
            print("  port:  not found yet (plug in the ESP32, then run `light doctor`)")

    if do_cursor:
        install_cursor_hooks()
    if do_claude:
        install_claude_hooks()
    if do_alias:
        install_alias()

    print()
    print("Done. Try:  light thinking   then   light done")
    return 0


# --- doctor ------------------------------------------------------------------

def _summarize_hooks(path: Path, label: str) -> None:
    if not path.exists():
        print(f"{label}: {path} (does not exist)")
        return
    try:
        cfg = json.loads(path.read_text() or "{}")
    except json.JSONDecodeError as e:
        print(f"{label}: {path} (invalid JSON: {e})")
        return
    events = list((cfg.get("hooks") or {}).keys()) if isinstance(cfg, dict) else []
    installed = "yes" if has_marker(cfg) else "no"
    print(f"{label}: {path}")
    print(f"  events:    {events}")
    print(f"  installed: {installed}")


def cmd_doctor(argv: list[str]) -> int:
    print("AI Status Light doctor")
    print()

    print(f"repo:         {REPO_DIR}")
    print(f"light.py:     {LIGHT_PY}")

    print()
    cached = read_cached_port()
    print(f"cached port:  {cached or '(none)'}")
    if serial is None:
        print("serial:       pyserial not installed (pip3 install pyserial)")
    else:
        port = find_port()
        if not port:
            print("detected:     (none)")
            print("              candidates:")
            for dev, score in candidate_ports():
                print(f"                {dev}  (score {score})")
        else:
            ok = probe_port(port)
            print(f"detected:     {port}  (handshake: {'ok' if ok else 'no response'})")

    print()
    _summarize_hooks(CURSOR_HOOKS_PATH, "cursor hooks")
    print()
    _summarize_hooks(CLAUDE_SETTINGS_PATH, "claude hooks")

    print()
    rc = shell_rc_path()
    if rc.exists() and MARKER in rc.read_text():
        print(f"alias:        installed in {rc}")
    elif rc.exists():
        print(f"alias:        not in {rc}")
    else:
        print(f"alias:        {rc} does not exist")

    print()
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().splitlines()[-10:]
        print(f"last {len(lines)} log lines ({LOG_FILE}):")
        for ln in lines:
            print(f"  {ln}")
    else:
        print(f"log:          {LOG_FILE} (no log yet)")

    return 0


# --- main --------------------------------------------------------------------

USAGE = """\
ai-status-light

Status:
  light thinking | working | done | success | error | fail | idle
  light red | yellow | green | off

Setup:
  light setup [--cursor] [--claude] [--alias] [--all]
  light doctor
"""


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0 if args else 1

    cmd = args[0]
    if cmd in COMMAND_MAP:
        return cmd_status(cmd)
    if cmd == "setup":
        return cmd_setup(args[1:])
    if cmd == "doctor":
        return cmd_doctor(args[1:])

    print(f"unknown command: {cmd}\n", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
