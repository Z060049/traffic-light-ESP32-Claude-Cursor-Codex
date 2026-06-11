# Claude Code integration

The installer writes three hook entries into `~/.claude/settings.json`:

| Claude Code event | Light | Notes |
|---|---|---|
| `PreToolUse`   | yellow            | fires before every tool call |
| `Stop`         | green             | fires when Claude finishes its turn |
| `PostToolUse`  | red on failure, no-op on success | runs [`cli/from_claude_hook.py`](../cli/from_claude_hook.py) |

## Why `Stop` and not `PostToolUse` for green

A typical Claude Code turn might use 5+ tools in sequence. If `PostToolUse` flipped the light green every time, you'd see green/yellow/green/yellow flapping the entire turn.

`Stop` fires exactly once, at the end of Claude's response — that's the actual "done" moment. So:

- `PreToolUse` -> yellow (might already be yellow, no visible change — fine)
- `PostToolUse` -> usually no-op; only flips the light **red** if that specific tool failed
- `Stop` -> green at the end of the turn

Result: solid yellow during work, briefly red if a tool errored, green when the turn ends.

## Failure detection

Claude Code pipes a JSON object to `PostToolUse` hooks on stdin, with fields like:

```json
{
  "session_id": "...",
  "tool_name": "Bash",
  "tool_input": { ... },
  "tool_response": {
    "is_error": true,
    "stdout": "...",
    "stderr": "..."
  }
}
```

[`cli/from_claude_hook.py`](../cli/from_claude_hook.py) reads stdin, looks at `tool_response`, and runs `light red` if it sees `is_error: true`, `success: false`, or a non-empty `error` field. The exact shape of `tool_response` varies by tool; the wrapper falls through to no-op for shapes it can't classify.

If failure detection isn't catching the cases you care about, edit `tool_failed()` in `from_claude_hook.py`.

## Verifying it's wired up

Inside Claude Code, run:

```
/hooks
```

You should see something like:

```
PreToolUse  (1)
PostToolUse (1)
Stop        (1)
```

If any of those say `(0)`, Claude Code didn't load that hook. Re-run `light setup --claude`.

Also from the terminal:

```bash
light doctor
```

Look for the `claude hooks` section.

## Debugging

Tail the log:

```bash
tail -f ~/.local/share/ai-status-light/light.log
```

Then ask Claude Code to use a tool, e.g. "list the files in this folder." You should see:

```
... sent yellow to ...     <- PreToolUse
... sent green to ...      <- Stop
```

For an explicit failure test, ask Claude Code to run a command that will fail:

```
run "this-command-does-not-exist" using bash
```

You should see `sent red to ...` from the PostToolUse wrapper.

## Manually editing

Example file: [`hooks/claude-code/settings.json.example`](../hooks/claude-code/settings.json.example). Merge the `hooks` block into `~/.claude/settings.json` by hand.

## Note on event semantics

Claude Code's hook event names (the ones used here) are:
`PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`, `UserPromptSubmit`, `PreCompact`, `SessionStart`, `SessionEnd`. There is no `PostToolUseFailure` or `PermissionDenied` event — failure detection happens by inspecting the JSON in `PostToolUse`, which is exactly what `from_claude_hook.py` does.
