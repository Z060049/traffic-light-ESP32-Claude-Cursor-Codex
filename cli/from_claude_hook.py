#!/usr/bin/env python3
"""PostToolUse hook entry point for Claude Code.

Claude Code pipes a JSON object to stdin on every PostToolUse event with
fields like `tool_name`, `tool_input`, and `tool_response`. We only flip
the light to red on tool failure -- on success we deliberately do nothing,
so the eventual `Stop` hook (which fires once Claude finishes its turn)
can turn the light green without the light flapping mid-turn.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIGHT_PY = os.path.join(HERE, "light.py")


def tool_failed(data: dict) -> bool:
    """Best-effort failure detection across Claude Code's tool result shapes.

    The exact JSON shape of `tool_response` varies by tool. Common signals:
      - `is_error: true`         (Bash and several others)
      - `success: false`         (some structured tools)
      - non-empty `error` string (some structured tools)
    """
    tr = data.get("tool_response")
    if isinstance(tr, dict):
        if tr.get("is_error") is True:
            return True
        if tr.get("success") is False:
            return True
        if tr.get("error"):
            return True
    return False


def main() -> int:
    if sys.stdin.isatty():
        return 0
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0

    if tool_failed(data):
        try:
            subprocess.run(
                [sys.executable, LIGHT_PY, "red"],
                check=False,
                timeout=5,
            )
        except (subprocess.SubprocessError, OSError):
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
