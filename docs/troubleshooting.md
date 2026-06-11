# Troubleshooting

First step for anything: run `light doctor`. It tells you the detected port, hook config status, alias presence, and the last log lines, all in one place.

---

## "no ESP32 serial port found"

You unplugged the board, or the OS hasn't enumerated it. Check:

```bash
ls /dev/cu.*           # macOS
ls /dev/ttyUSB* /dev/ttyACM*   # Linux
```

If nothing shows up, jump to **"ESP32 lights up but no port appears"** below.

If something shows up but `light doctor` says it's not detected, the port's USB VID isn't in our known list. Edit `KNOWN_VIDS` in [`cli/light.py`](../cli/light.py) and add yours. (Plug in the board, run `python3 -c "from serial.tools import list_ports; [print(hex(p.vid), p.device, p.description) for p in list_ports.comports() if p.vid]"`.)

---

## ESP32 lights up but no `/dev/cu.*` port appears

The most common reasons, in order:

1. **Charge-only USB cable.** It powers the ESP32 (LED comes on) but doesn't carry data. Try a known data cable.
2. **USB-C to USB-C compatibility.** Cheap ESP32 boards often skip the CC-pin resistor work needed for C-to-C. Use USB-A to USB-C plus an adapter if needed.
3. **Missing CH340 / CH34x driver.** Most modern macOS versions have it built in, but some need [the official driver from WCH](https://www.wch-ic.com/downloads/CH34XSER_MAC_ZIP.html). After installing, reboot.
4. **macOS hasn't approved the driver.** `System Settings` -> `Privacy & Security`, look for a blocked driver and click "Allow".

---

## The port keeps changing names

This is normal for CH340-based boards on macOS — the suffix changes after every reconnect (`wchusbserial1110`, `wchusbserial10`, `wchusbserial1120`, ...).

The CLI handles this automatically: it caches the port at `~/.config/ai-status-light/port`, but re-detects on the next call if the cached path no longer exists. You don't have to do anything.

If you want to force a fresh scan:

```bash
rm ~/.config/ai-status-light/port
light doctor
```

---

## "Resource busy" or `SerialException`

Something else is holding the serial port. Common culprits:

- **Arduino IDE Serial Monitor** — close it.
- **A previous `light` invocation hung** — `pkill -f light.py`.
- **Cursor and Claude Code firing simultaneously** — if both try to send at the exact same instant, one wins and the other fails. The CLI logs the failure and continues; the missed event is mostly harmless. (V2 will add a daemon to serialize access.)

---

## `light thinking` works but Cursor doesn't trigger the light

Inside Cursor, your hook config is at `~/.cursor/hooks.json`. Verify it has our entries:

```bash
cat ~/.cursor/hooks.json
```

Look for `# ai-status-light` in the `command` strings.

If it's missing, re-run `light setup --cursor`.

---

## `light thinking` works but Claude Code doesn't trigger the light

Inside Claude Code, run:

```
/hooks
```

You should see `PreToolUse (1)`, `PostToolUse (1)`, `Stop (1)`. If any are `(0)`, Claude Code didn't load that hook.

Re-run `light setup --claude`. Also tail the log while asking Claude to use a tool:

```bash
tail -f ~/.local/share/ai-status-light/light.log
```

Note: Claude Code hooks fire on **tool use**, not on prompt submit. If Claude responds without using any tools, none of the hooks fire — that's expected.

---

## Yellow breathing is too slow / too fast

Edit `firmware/esp32-traffic-light/esp32-traffic-light.ino`:

```cpp
const unsigned long YELLOW_BREATHE_PERIOD_MS = 1200;
```

Smaller = faster. Try `700` for snappy, `1800` for calm.

Re-upload via Arduino IDE.

---

## Green is too bright

Same file:

```cpp
const int GREEN_BRIGHTNESS = 60;
```

`30` is fairly dim, `100`+ is bright. Re-upload.

---

## Green won't turn off

By default green auto-turns-off after 20 seconds. If you want it to stay on:

```cpp
const unsigned long GREEN_TIMEOUT_MS = 20000;
```

Set to `0` to disable the timeout, or a larger value to extend it. Re-upload.

---

## Arduino IDE can't upload

- Selected wrong port -> `Tools` -> `Port`, pick the current one.
- Serial Monitor open -> close it.
- `light` CLI or hook is using the port -> quit Cursor and Claude Code, or run `pkill -f light.py`.
- Board needs manual boot mode -> hold the `BOOT` button while clicking upload, release once "Connecting..." appears.

---

## Active-low LED module (lights are inverted)

If your module turns LEDs on when the GPIO goes LOW, flip `ACTIVE_HIGH` in the firmware:

```cpp
#define ACTIVE_HIGH 0
```

Re-upload.
