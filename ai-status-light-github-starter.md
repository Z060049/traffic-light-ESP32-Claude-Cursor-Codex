# AI Status Light

A physical traffic-light status indicator for AI coding agents such as Claude Code and Cursor.

**Yellow** = AI is working  
**Green** = task completed  
**Red** = task failed  

The goal is simple: make AI coding feel physical. Instead of staring at a terminal and wondering whether your agent is still working, you get a small desk traffic light that shows agent status in real time.

---

## 1. Project Overview

This project combines:

- An ESP32 development board
- A small red/yellow/green traffic light LED module
- Arduino firmware running on the ESP32
- A Python CLI command, for example `light thinking` or `light done`
- Cursor hooks
- Claude Code hooks
- Optional 3D printed enclosure

Current prototype flow:

```text
Claude Code / Cursor starts work
↓
Hook runs local Python script
↓
Python sends serial command to ESP32
↓
ESP32 controls traffic light
↓
Yellow / Green / Red status is shown physically
```

---

## 2. Current Behavior

| Status | Meaning | Light |
|---|---|---|
| `thinking` | AI is working | Yellow blinking / breathing |
| `done` | Task completed | Green |
| `success` | Task completed | Green |
| `error` | Task failed | Red |
| `idle` | No active task | Off |

Current behavior:

- Yellow uses a blinking/breathing effect.
- Green turns on when the task is done.
- Green can auto-turn-off after a timeout.
- Red is reserved for failed tool calls, permission errors, or command failures.

---

## 3. Recommended Repo Name

Recommended GitHub repo name:

```text
ai-status-light
```

Other possible names:

```text
claude-code-traffic-light
agent-status-light
cursor-claude-status-light
desk-agent-light
```

`ai-status-light` is the best general name because the project can support Claude Code, Cursor, terminal workflows, and future AI coding agents.

---

## 4. Recommended GitHub Repo Structure

```text
ai-status-light/
├── README.md
├── LICENSE
├── .gitignore
│
├── firmware/
│   └── esp32-traffic-light/
│       └── esp32-traffic-light.ino
│
├── cli/
│   ├── light.py
│   ├── requirements.txt
│   └── install.sh
│
├── hooks/
│   ├── cursor/
│   │   └── hooks.json.example
│   └── claude-code/
│       └── settings.json.example
│
├── docs/
│   ├── hardware.md
│   ├── wiring.md
│   ├── setup-mac.md
│   ├── cursor.md
│   ├── claude-code.md
│   └── troubleshooting.md
│
├── images/
│   ├── prototype.jpg
│   ├── wiring-diagram.png
│   └── demo.gif
│
└── enclosure/
    ├── README.md
    └── placeholder.md
```

Later, after the 3D enclosure is designed:

```text
enclosure/
├── base.stl
├── bottom-lid.stl
├── pole.stl
├── traffic-light-shell.stl
├── traffic-light-back-cover.stl
└── ai-status-light.scad
```

---

## 5. Hardware

### Required Parts

- ESP32 development board
- Mini traffic light LED module with pins:
  - `R`
  - `Y`
  - `G`
  - `GND`
- Jumper wires
- USB data cable
- Computer running macOS, Linux, or Windows
- Arduino IDE

### Optional Parts

- Breadboard
- Longer USB data cable
- Small enclosure
- 3D printed case
- Heat shrink tubing
- Cable sleeve
- Double-sided tape / Velcro / 3M Dual Lock

---

## 6. Important USB Cable Note

A USB cable can power the ESP32 but still fail to expose the serial port.

Common failure mode:

```text
ESP32 lights up
but no /dev/cu.wchusbserial* appears
```

This usually means one of the following:

- The USB cable is charge-only.
- The USB-C to USB-C cable does not work with the ESP32 board.
- The ESP32 board’s USB-C implementation does not handle C-to-C correctly.
- The serial driver is missing or not activated.
- The port changed after reconnecting the board.

If the serial port does not appear, try:

```text
ESP32 USB-C
↓
USB-A to USB-C data cable
↓
USB-A to USB-C adapter
↓
Mac
```

In this project, the port changed multiple times:

```text
/dev/cu.wchusbserial1110
/dev/cu.wchusbserial10
/dev/cu.wchusbserial1120
```

This is why the Python script should auto-detect the serial port instead of hard-coding it.

---

## 7. Wiring

Traffic light module to ESP32:

| Traffic Light Pin | ESP32 Pin |
|---|---|
| `GND` | `GND` |
| `R` | `GPIO16` |
| `Y` | `GPIO17` |
| `G` | `GPIO18` |

Basic wiring:

```text
Traffic Light Module       ESP32
--------------------       -----
GND ---------------------- GND
R   ---------------------- GPIO16
Y   ---------------------- GPIO17
G   ---------------------- GPIO18
```

Note: if your LED module is active-low instead of active-high, you may need to invert `HIGH` and `LOW` in the firmware.

---

## 8. ESP32 Firmware

Create this file:

```text
firmware/esp32-traffic-light/esp32-traffic-light.ino
```

Arduino firmware:

```cpp
#define RED_PIN 16
#define YELLOW_PIN 17
#define GREEN_PIN 18

// Green stays on for 20 seconds, then turns off automatically.
const unsigned long GREEN_TIMEOUT_MS = 20000;

// Yellow breathing cycle duration.
// 1200 = bright -> off -> bright takes 1.2 seconds.
const unsigned long YELLOW_BREATHE_PERIOD_MS = 1200;

// Brightness values: 0 = off, 255 = full brightness.
const int GREEN_BRIGHTNESS = 60;

String currentState = "off";

unsigned long greenStartTime = 0;
unsigned long yellowBreathStartTime = 0;

void allOff() {
  digitalWrite(RED_PIN, LOW);
  analogWrite(YELLOW_PIN, 0);
  analogWrite(GREEN_PIN, 0);

  currentState = "off";
}

void setRed() {
  digitalWrite(RED_PIN, HIGH);
  analogWrite(YELLOW_PIN, 0);
  analogWrite(GREEN_PIN, 0);

  currentState = "red";
}

void setYellowBreathing() {
  digitalWrite(RED_PIN, LOW);
  analogWrite(GREEN_PIN, 0);

  currentState = "yellow";
  yellowBreathStartTime = millis();
}

void setGreen() {
  digitalWrite(RED_PIN, LOW);
  analogWrite(YELLOW_PIN, 0);
  analogWrite(GREEN_PIN, GREEN_BRIGHTNESS);

  currentState = "green";
  greenStartTime = millis();
}

void updateYellowBreathing() {
  unsigned long now = millis();
  unsigned long elapsed = (now - yellowBreathStartTime) % YELLOW_BREATHE_PERIOD_MS;

  float phase = (float)elapsed / (float)YELLOW_BREATHE_PERIOD_MS;

  int brightness;

  if (phase < 0.5) {
    // First half: bright -> off
    brightness = 255 - (int)(phase * 2.0 * 255);
  } else {
    // Second half: off -> bright
    brightness = (int)((phase - 0.5) * 2.0 * 255);
  }

  analogWrite(YELLOW_PIN, brightness);
}

void setup() {
  Serial.begin(115200);

  pinMode(RED_PIN, OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);

  allOff();

  Serial.println("Traffic Light Ready");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "red") {
      setRed();
    } else if (cmd == "yellow") {
      setYellowBreathing();
    } else if (cmd == "green") {
      setGreen();
    } else if (cmd == "off") {
      allOff();
    }

    Serial.print("Received: ");
    Serial.println(cmd);
  }

  if (currentState == "yellow") {
    updateYellowBreathing();
  }

  if (currentState == "green") {
    unsigned long elapsed = millis() - greenStartTime;

    if (elapsed >= GREEN_TIMEOUT_MS) {
      allOff();
      Serial.println("Green timeout -> off");
    }
  }
}
```

---

## 9. Arduino IDE Setup

### Install Board Package

In Arduino IDE:

```text
Boards Manager
↓
Search: esp32
↓
Install: esp32 by Espressif Systems
```

Use:

```text
Board: ESP32 Dev Module
```

Select the correct serial port, for example:

```text
/dev/cu.wchusbserial1120
```

The port may change after reconnecting the board.

### Upload

Upload the firmware to the ESP32.

If upload fails, close anything using the serial port:

- Arduino Serial Monitor
- Cursor
- Claude Code
- Any terminal command running `light`

If upload still fails, try holding the ESP32 `BOOT` button while Arduino IDE is connecting.

---

## 10. Python CLI

Create:

```text
cli/light.py
```

Python script:

```python
import glob
import serial
import sys
import time

BAUD = 115200

COMMAND_MAP = {
    "thinking": "yellow",
    "done": "green",
    "success": "green",
    "error": "red",
    "idle": "off",

    "red": "red",
    "yellow": "yellow",
    "green": "green",
    "off": "off",
}

def find_esp32_port():
    patterns = [
        "/dev/cu.wchusbserial*",
        "/dev/cu.usbserial*",
        "/dev/cu.usbmodem*",
        "/dev/ttyUSB*",
        "/dev/ttyACM*",
    ]

    ports = []

    for pattern in patterns:
        ports.extend(glob.glob(pattern))

    if not ports:
        print("No ESP32 serial port found.")
        print("Try running:")
        print("  ls /dev/cu.*")
        print("  ls /dev/tty*")
        sys.exit(1)

    return ports[0]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 light.py thinking|done|error|idle")
        print("Direct commands: red|yellow|green|off")
        sys.exit(1)

    input_cmd = sys.argv[1].lower()

    if input_cmd not in COMMAND_MAP:
        print("Invalid command.")
        print("Use: thinking, done, success, error, idle")
        print("Or: red, yellow, green, off")
        sys.exit(1)

    esp32_cmd = COMMAND_MAP[input_cmd]
    port = find_esp32_port()

    with serial.Serial(port, BAUD, timeout=1) as ser:
        time.sleep(2)
        ser.write((esp32_cmd + "\n").encode("utf-8"))
        print(f"Port: {port}")
        print(f"Input: {input_cmd}")
        print(f"Sent to ESP32: {esp32_cmd}")

if __name__ == "__main__":
    main()
```

---

## 11. Python Requirements

Create:

```text
cli/requirements.txt
```

Contents:

```text
pyserial
```

Install:

```bash
pip3 install -r cli/requirements.txt
```

Or directly:

```bash
pip3 install pyserial
```

---

## 12. Shell Alias

For local development, add this alias to `~/.zshrc`:

```bash
alias light="python3 /Users/test/Project/traffic-light/light.py"
```

For a GitHub repo, users should adapt the path:

```bash
alias light="python3 ~/Projects/ai-status-light/cli/light.py"
```

Reload:

```bash
source ~/.zshrc
```

Test:

```bash
light thinking
light done
light error
light idle
```

---

## 13. Cursor Hook Example

Create:

```text
hooks/cursor/hooks.json.example
```

Example:

```json
{
  "version": 1,
  "hooks": {
    "beforeSubmitPrompt": [
      {
        "command": "/bin/zsh -lc '/usr/bin/python3 ~/Projects/ai-status-light/cli/light.py thinking >> ~/Projects/ai-status-light/logs/cursor-light.log 2>&1'"
      }
    ],
    "stop": [
      {
        "command": "/bin/zsh -lc '/usr/bin/python3 ~/Projects/ai-status-light/cli/light.py done >> ~/Projects/ai-status-light/logs/cursor-light.log 2>&1'"
      }
    ]
  }
}
```

User setup path:

```text
~/.cursor/hooks.json
```

Important: users may already have Cursor hooks. Do not blindly overwrite their config. They should merge the hook entries.

Debug:

```bash
tail -f ~/Projects/ai-status-light/logs/cursor-light.log
```

---

## 14. Claude Code Hook Example

Create:

```text
hooks/claude-code/settings.json.example
```

Example:

```json
{
  "theme": "auto",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 ~/Projects/ai-status-light/cli/light.py thinking >> ~/Projects/ai-status-light/logs/claude-light.log 2>&1"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 ~/Projects/ai-status-light/cli/light.py done >> ~/Projects/ai-status-light/logs/claude-light.log 2>&1"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 ~/Projects/ai-status-light/cli/light.py error >> ~/Projects/ai-status-light/logs/claude-light.log 2>&1"
          }
        ]
      }
    ],
    "PermissionDenied": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 ~/Projects/ai-status-light/cli/light.py error >> ~/Projects/ai-status-light/logs/claude-light.log 2>&1"
          }
        ]
      }
    ]
  }
}
```

User setup path:

```text
~/.claude/settings.json
```

Important: users may already have Claude Code settings. Do not blindly overwrite their file. They should merge the `hooks` section into their existing config.

Inside Claude Code, run:

```text
/hooks
```

Expected result:

```text
PreToolUse (1)
PostToolUse (1)
PostToolUseFailure (1)
PermissionDenied (1)
```

If the number is `(0)`, Claude Code did not load the hook.

Debug:

```bash
tail -f ~/Projects/ai-status-light/logs/claude-light.log
```

Then in Claude Code, ask it to use a tool:

```text
list files in this folder
```

Expected behavior:

```text
Yellow = Claude Code starts tool use
Green = tool completed
Red = tool failed or permission denied
```

Note: Claude Code hooks trigger when Claude uses tools. They do not necessarily trigger immediately when the user types a prompt.

---

## 15. Logs Directory

Recommended:

```bash
mkdir -p logs
```

Add to `.gitignore`:

```text
logs/
*.log
```

---

## 16. Troubleshooting

### Problem: `No such file or directory: /dev/cu.wchusbserial1110`

Cause:

The serial port changed.

Fix:

Use the auto-detecting `light.py`. Do not hard-code the port.

Check current port:

```bash
ls /dev/cu.*
```

Example current port:

```text
/dev/cu.wchusbserial1120
```

### Problem: ESP32 lights up but no serial port appears

Likely causes:

- Charge-only USB cable
- Bad USB-C to USB-C compatibility
- Missing CH340 / CH34x driver
- Driver not approved in macOS settings
- Wrong USB adapter

Try:

```text
USB-A to USB-C data cable
```

### Problem: Arduino IDE cannot upload

Likely causes:

- Arduino IDE selected old port
- Serial Monitor is open
- Cursor or Claude Code is using the serial port
- Python script is using the serial port
- Board needs manual boot mode

Fix:

- Select current port in Arduino IDE.
- Quit Cursor and Claude Code.
- Close Serial Monitor.
- Try upload again.
- Hold `BOOT` during upload if needed.

### Problem: `light thinking` works, but Cursor does not trigger light

Check:

```bash
cat ~/.cursor/hooks.json
```

Use a log command to confirm hook execution.

### Problem: `light thinking` works, but Claude Code does not trigger light

Inside Claude Code:

```text
/hooks
```

Check that the hooks show `(1)`.

Also check the log:

```bash
tail -f ~/Projects/ai-status-light/logs/claude-light.log
```

Then ask Claude Code to use a tool:

```text
list files in this folder
```

### Problem: Yellow breathing is too slow

Change:

```cpp
const unsigned long YELLOW_BREATHE_PERIOD_MS = 3000;
```

To:

```cpp
const unsigned long YELLOW_BREATHE_PERIOD_MS = 1200;
```

Faster values:

```cpp
const unsigned long YELLOW_BREATHE_PERIOD_MS = 1000;
const unsigned long YELLOW_BREATHE_PERIOD_MS = 700;
```

Recommended value:

```cpp
1200
```

### Problem: Green is too bright

Change:

```cpp
const int GREEN_BRIGHTNESS = 60;
```

Lower value:

```cpp
const int GREEN_BRIGHTNESS = 30;
```

Higher value:

```cpp
const int GREEN_BRIGHTNESS = 100;
```

---

## 17. Enclosure Direction

The first enclosure should be practical, not perfect.

Recommended design:

```text
1. Thin orange rounded base enclosure
2. Black traffic light enclosure
3. Hollow black pole / wire channel
4. USB cable exits from the back of the base
5. ESP32 hidden inside the base
6. Traffic light PCB mounted inside the black shell
```

Current preferred product design:

```text
Base: thin, rounded, orange
Traffic light enclosure: black
Pole: black
USB: exits from back
Style: cute desktop gadget
```

### Why 3D Printing Makes Sense

Online project boxes are hard to find in the exact shape, size, color, and cutout style needed.

3D printing is better because:

- Base can be thinner.
- USB cable notch can be custom.
- ESP32 can fit exactly.
- Wires can be hidden.
- Traffic light shell can be black and product-like.
- The final object can look cute instead of industrial.

### 3D Print Shop Brief

Send this to a 3D print shop:

```text
I want to 3D print a small cute desktop enclosure for an ESP32 traffic-light status device.

The device has:
- one ESP32 development board
- one small red/yellow/green traffic light PCB module
- four jumper wires between ESP32 and traffic light
- one USB-C cable for power/data

I want:
- a thin rounded rectangular base that hides the ESP32 and extra wires
- base color: matte orange
- a removable bottom lid
- a back cable notch for the USB-C cable
- a hollow vertical pole to route the four wires
- a black rounded traffic light shell that holds my existing traffic light module upright
- cute product-like appearance, not industrial
- the base should still be openable later for maintenance

Approx base size:
100mm W x 65mm D x 25-35mm H

Please design the first version as a functional fit-check prototype.
```

### Measurements Needed for 3D Design

Before generating STL / OpenSCAD:

```text
1. ESP32 length / width / height
2. Traffic light PCB length / width / thickness
3. LED diameter
4. LED center-to-center distance
5. Pin header location
6. USB-C cable head width / height / depth
7. USB cable thickness
8. Desired pole height
9. Desired base height
10. Clearance needed for jumper wires
```

---

## 18. Product Roadmap

### V1: DIY Build Guide

Goal:

```text
Someone with the same hardware can copy the repo and make it work.
```

Include:

- Arduino firmware
- Python CLI
- Cursor hook example
- Claude Code hook example
- Mac setup guide
- Wiring guide
- Troubleshooting guide
- Prototype photos

### V2: Cleaner CLI

Possible commands:

```bash
ai-light thinking
ai-light done
ai-light error
ai-light idle
ai-light setup cursor
ai-light setup claude
ai-light doctor
```

Potential package:

```bash
pip install ai-status-light
```

### V3: 3D Printable Product

Include:

- STL files
- OpenSCAD or CAD source
- Assembly guide
- Screws / magnets / lid mechanism
- Product photos
- Short demo video

### V4: Wireless Version

Possible future design:

- ESP32 with Wi-Fi
- Local HTTP endpoint
- Claude Code / Cursor hooks call HTTP instead of serial
- Optional battery
- USB-C power only

Recommended path:

```text
V1 USB serial
↓
V2 USB serial with enclosure
↓
V3 Wi-Fi with USB power
↓
V4 battery version
```

Battery + Wi-Fi should come later because ESP32 Wi-Fi consumes power and adds reliability complexity.

---

## 19. README Opening Draft

Use this as the top section of the GitHub README:

```markdown
# AI Status Light

A physical traffic-light status indicator for AI coding agents.

Yellow means your AI agent is working.  
Green means the task is done.  
Red means something failed.

This project started as a small desk gadget for Claude Code and Cursor. It uses an ESP32, a mini traffic light LED module, Arduino firmware, a Python CLI, and editor hooks to turn invisible AI agent activity into a physical signal on your desk.

It makes AI coding feel like running a tiny factory.

## Supported Integrations

- Claude Code
- Cursor
- Terminal commands

## Status

This project is currently a DIY prototype. You need to buy your own hardware and upload the firmware to an ESP32.
```

---

## 20. 10-Second YouTube Short Script

```text
I built a traffic light for Claude Code.

When Claude is working, it blinks yellow.

When the task is done, it turns green.

AI coding now feels like running a tiny factory on my desk.
```

Alternative:

```text
I made a traffic light for my AI coding agent.

Yellow: working.

Green: done.

Red: failed.

AI coding feels like a tiny factory now.
```

---

## 21. Initial Git Commands

```bash
mkdir ai-status-light
cd ai-status-light

mkdir -p firmware/esp32-traffic-light
mkdir -p cli
mkdir -p hooks/cursor
mkdir -p hooks/claude-code
mkdir -p docs
mkdir -p images
mkdir -p enclosure
mkdir -p logs

touch README.md
touch LICENSE
touch .gitignore
```

Recommended `.gitignore`:

```text
logs/
*.log
__pycache__/
*.pyc
.DS_Store
.env
.venv/
```

Initial commit:

```bash
git init
git add .
git commit -m "Initial AI status light project"
```

---

## 22. Key Lessons From Prototype

These should influence the repo docs:

1. Do not hard-code serial ports.
2. Auto-detect ESP32 serial ports.
3. USB data cable matters.
4. USB-C to USB-C may not work on some ESP32 boards.
5. Arduino IDE must manually select the current port.
6. Only one app can use serial at once.
7. Cursor hooks and Claude Code hooks should write logs for debugging.
8. Claude Code hooks trigger on tool usage, not necessarily on prompt submit.
9. First enclosure should be a functional fit-check prototype.
10. The project is strong because it is useful, visual, simple, and cute.

---

## 23. Suggested GitHub Description

Short description:

```text
A physical traffic-light status indicator for Claude Code, Cursor, and AI coding agents.
```

Longer description:

```text
AI Status Light turns invisible AI agent activity into a physical desk signal. It uses an ESP32 traffic light module, Arduino firmware, a Python CLI, and hooks for Claude Code and Cursor. Yellow means working, green means done, red means failed.
```

Topics:

```text
claude-code
cursor
esp32
arduino
ai-agent
developer-tools
hardware
python
serial
status-light
```

---

## 24. License

Recommended license:

```text
MIT License
```

This keeps it easy for other people to use, fork, and modify.

---

## 25. Next Step

The next step is to create the actual repo files:

```text
README.md
firmware/esp32-traffic-light/esp32-traffic-light.ino
cli/light.py
cli/requirements.txt
hooks/cursor/hooks.json.example
hooks/claude-code/settings.json.example
docs/hardware.md
docs/wiring.md
docs/troubleshooting.md
```

Start with the README and working code first. Add enclosure files later after the 3D print prototype is designed.
