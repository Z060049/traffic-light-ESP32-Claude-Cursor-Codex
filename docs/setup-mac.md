# macOS setup

This is the host-side install. Do the [ESP32 firmware setup](setup-esp32.md) first.

## 1. Clone the repo

```bash
git clone https://github.com/<your-username>/ai-status-light.git ~/Projects/ai-status-light
cd ~/Projects/ai-status-light
```

You can clone anywhere; the installer uses the repo's actual path when it writes the hook commands and shell alias, so the location is portable.

## 2. Run the installer

```bash
./install.sh
```

It will:

1. `pip install --user pyserial`.
2. Detect your ESP32 by USB VID and remember the port at `~/.config/ai-status-light/port`.
3. Merge hook entries into `~/.cursor/hooks.json` and `~/.claude/settings.json`. Pre-existing files are backed up to `*.bak.<UTC-timestamp>` next to the original. The merge is idempotent — re-running the installer is safe.
4. Append a `light` shell alias to your `~/.zshrc` or `~/.bashrc` (chosen from `$SHELL`).
5. Create `~/.local/share/ai-status-light/` for the log file.

## 3. Smoke test

Open a new terminal (so the shell alias loads) and run:

```bash
light thinking
light done
light error
light off
```

If the light reacts, host-side setup is done.

## 4. Per-editor setup

- **Cursor:** see [`cursor.md`](cursor.md).
- **Claude Code:** see [`claude-code.md`](claude-code.md).

## What the installer changed

| Path | What |
|---|---|
| `~/.config/ai-status-light/port` | cached serial port path |
| `~/.cursor/hooks.json`           | added `beforeSubmitPrompt` and `stop` hooks |
| `~/.claude/settings.json`        | added `PreToolUse`, `Stop`, `PostToolUse` hooks |
| `~/.zshrc` (or `.bashrc`)        | added `alias light=...` |
| `~/.local/share/ai-status-light/light.log` | the CLI's own log file |

To uninstall, remove those entries. The `# ai-status-light` marker is on every line we wrote, so a quick `grep` will find them.

## Linux

The same `install.sh` should work on Linux. The serial detection looks for `/dev/ttyUSB*` and `/dev/ttyACM*` in addition to the macOS device names. You may need to add yourself to the `dialout` group:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in.
