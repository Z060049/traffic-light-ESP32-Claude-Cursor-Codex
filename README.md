# AI Status Light

A physical traffic-light status indicator for AI coding agents like Claude Code and Cursor.

- **Yellow (breathing)** — AI is working
- **Green** — task completed
- **Red** — tool call failed

It turns invisible AI agent activity into a glance-able desk signal. Instead of staring at a terminal wondering whether your agent is still thinking, you just look up.

> _Demo GIF goes here once you record one — drop it in `images/demo.gif` and link it._

---

## What's in this repo

```
firmware/      Arduino firmware for the ESP32
cli/           Python CLI (`light`) and the Claude Code PostToolUse hook
hooks/         Example hook configs for Cursor and Claude Code
docs/          Setup, wiring, troubleshooting
install.sh     One-shot installer (pip + light setup --all)
```

---

## Quick start

You'll need an ESP32, a 3-color traffic light LED module, and a USB **data** cable. See [`docs/hardware.md`](docs/hardware.md) for exact parts and links.

**1. Wire it up.** GND, R, Y, G. Full pin map in [`docs/wiring.md`](docs/wiring.md) — TL;DR:

| Module pin | ESP32 pin |
|---|---|
| `GND` | `GND` |
| `R`   | `GPIO16` |
| `Y`   | `GPIO17` |
| `G`   | `GPIO18` |

**2. Upload the firmware.** One-time, via Arduino IDE. Walkthrough in [`docs/setup-esp32.md`](docs/setup-esp32.md).

**3. Clone this repo and run the installer.**

```bash
git clone https://github.com/<your-username>/ai-status-light.git ~/Projects/ai-status-light
cd ~/Projects/ai-status-light
./install.sh
```

The installer:

- installs `pyserial`
- detects your ESP32's serial port (and remembers it, so it survives the port-renaming you get on macOS)
- merges hook entries into `~/.cursor/hooks.json` and `~/.claude/settings.json` (with timestamped backups, idempotent on re-runs)
- appends a `light` shell alias to your `~/.zshrc` or `~/.bashrc`

**4. Smoke test.**

```bash
light thinking   # yellow breathing
light done       # green
light error      # red
light off        # all off
```

Open a new Cursor or Claude Code session — the light should now follow it.

---

## How it works

```mermaid
flowchart LR
    Agent[Claude Code or Cursor] -->|hook fires| HookCmd[python3 cli/light.py thinking]
    HookCmd -->|USB serial| ESP32
    ESP32 -->|drives PWM| LED[traffic-light LED module]
```

**On Cursor:**
- `beforeSubmitPrompt` -> yellow
- `stop` -> green

**On Claude Code:**
- `PreToolUse` -> yellow
- `Stop` -> green
- `PostToolUse` -> red **only on tool failure** (handled by [`cli/from_claude_hook.py`](cli/from_claude_hook.py); no-op on success so the light doesn't flap mid-turn)

The Python CLI:
- auto-detects the ESP32 by USB VID (CH340 / CP210x / FTDI / Espressif native)
- caches the port at `~/.config/ai-status-light/port`
- opens the port with DTR/RTS disabled, so opening it doesn't reset the chip — keeps each call ~50 ms instead of ~2 s
- logs to `~/.local/share/ai-status-light/light.log`

---

## Commands

```bash
light thinking | working | done | success | error | fail | idle
light red | yellow | green | off
light setup [--cursor] [--claude] [--alias] [--all]
light doctor
```

`light doctor` is your first stop when something doesn't work — it reports the detected port, hook config status, alias presence, and the last log lines.

---

## Documentation

- [`docs/hardware.md`](docs/hardware.md) — what to buy
- [`docs/wiring.md`](docs/wiring.md) — pin map and diagram
- [`docs/setup-esp32.md`](docs/setup-esp32.md) — Arduino IDE walkthrough
- [`docs/setup-mac.md`](docs/setup-mac.md) — clone-and-run on macOS
- [`docs/cursor.md`](docs/cursor.md) — Cursor hook details
- [`docs/claude-code.md`](docs/claude-code.md) — Claude Code hook details
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — port issues, USB cables, hooks not firing

---

## Roadmap

- **V1 (now)** — DIY USB-serial build, hooks for Cursor and Claude Code.
- **V2** — Cleaner CLI as a `pip install`-able package; serial daemon to remove the "only one process can hold the port" edge case.
- **V3** — 3D-printed enclosure (STLs in `enclosure/`).
- **V4** — Wi-Fi version: ESP32 listens on a local HTTP endpoint; hooks `curl` instead of writing to serial. Optional battery.

---

## License

[MIT](LICENSE).
