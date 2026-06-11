#!/usr/bin/env bash
# AI Status Light installer
#
# Installs the Python dependency (pyserial), then runs `light setup --all`
# which:
#   * detects the ESP32 serial port
#   * merges hook entries into ~/.cursor/hooks.json and ~/.claude/settings.json
#     (with timestamped backups; idempotent on re-runs)
#   * appends a `light` shell alias to your shell rc
#   * creates ~/.local/share/ai-status-light/ for logs
#
# Re-running this script is safe.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pick a Python interpreter.
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "error: python3 not found. Install Python 3 first." >&2
  exit 1
fi

echo "[1/2] Installing Python dependency (pyserial)"
"$PY" -m pip install --user --quiet -r "$REPO_DIR/cli/requirements.txt"

echo "[2/2] Running setup"
"$PY" "$REPO_DIR/cli/light.py" setup --all

echo
echo "Installation complete."
echo "Open a new terminal (so the shell alias loads), then try:"
echo "  light thinking"
echo "  light done"
echo "  light error"
echo "  light off"
