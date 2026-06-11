# Cursor integration

The installer writes two hook entries into `~/.cursor/hooks.json`:

| Cursor event | Light |
|---|---|
| `beforeSubmitPrompt` | yellow (breathing) |
| `stop`               | green |

That's it. Every time you submit a prompt, the light flips to yellow; when Cursor's response stream ends, it flips to green and auto-turns-off after 20 seconds (configurable in the firmware).

## Why no red?

Cursor doesn't expose a "tool call failed" hook event the way Claude Code does. For now, red is reserved for Claude Code's `PostToolUse` failures. You can still trigger red manually:

```bash
light error
```

If/when Cursor adds a failure event, dropping it into `install_cursor_hooks()` in [`cli/light.py`](../cli/light.py) is a one-line change.

## Verifying it's wired up

```bash
light doctor
```

Look for the `cursor hooks` section. It should show:

```
cursor hooks: /Users/<you>/.cursor/hooks.json
  events:    ['beforeSubmitPrompt', 'stop']
  installed: yes
```

If `installed: no` but the file exists, your `~/.cursor/hooks.json` already had hooks but ours weren't merged in — re-run `light setup --cursor` and check the printed log.

## Manually editing

If you'd rather copy-paste than auto-merge, the example file is at [`hooks/cursor/hooks.json.example`](../hooks/cursor/hooks.json.example). Merge the contents into `~/.cursor/hooks.json` by hand and update the `light.py` path to match where you cloned the repo.

## Debugging

Tail the `light.py` log:

```bash
tail -f ~/.local/share/ai-status-light/light.log
```

You should see one entry per Cursor turn:

```
2026-06-10T... sent yellow to /dev/cu.wchusbserial1120
2026-06-10T... sent green to /dev/cu.wchusbserial1120
```

If the hook fires but nothing reaches the log, the hook is calling something other than our CLI — open `~/.cursor/hooks.json` and check the `command` strings.
