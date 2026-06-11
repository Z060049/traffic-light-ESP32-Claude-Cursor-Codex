# ESP32 firmware setup

One-time: install Arduino IDE, add ESP32 board support, and upload the sketch in [`firmware/esp32-traffic-light/`](../firmware/esp32-traffic-light/).

## 1. Install Arduino IDE

Download from [arduino.cc/en/software](https://www.arduino.cc/en/software). Either Arduino IDE 2.x or the legacy 1.8.x works; this guide uses 2.x.

## 2. Add the ESP32 board package

1. Open Arduino IDE.
2. `Arduino IDE` -> `Settings` (or `Preferences` on older versions).
3. **Additional boards manager URLs**, add:

   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```

4. `Tools` -> `Board` -> `Boards Manager`.
5. Search `esp32`. Install **`esp32` by Espressif Systems**, version **3.0 or newer**.

> Why 3.x: the firmware uses `analogWrite()`, which only landed in the Arduino-ESP32 core in 3.0. On 2.x you'll get a compile error and need to switch to `ledcAttach`/`ledcWrite`.

## 3. Open the sketch

`File` -> `Open` -> select [`firmware/esp32-traffic-light/esp32-traffic-light.ino`](../firmware/esp32-traffic-light/esp32-traffic-light.ino) from this repo.

## 4. Select board and port

- `Tools` -> `Board` -> `esp32` -> **`ESP32 Dev Module`**.
- Plug the ESP32 into your Mac.
- `Tools` -> `Port` -> pick the entry that looks like `/dev/cu.wchusbserial...` (CH340 chip) or `/dev/cu.SLAB_USBtoUART` (CP210x). The exact suffix changes — see [`troubleshooting.md`](troubleshooting.md).

## 5. Upload

Click the upload button (right-arrow icon).

If it fails:

- Close Arduino's **Serial Monitor** if it's open.
- Quit Cursor and Claude Code if either is running with the light's hooks enabled (they'll be holding the serial port).
- Hold the ESP32's `BOOT` button while the Arduino IDE shows "Connecting..." in the console.
- Try a different USB port or a known-good USB **data** cable. ([`docs/hardware.md`](hardware.md) has the cable rant.)

## 6. Verify

`Tools` -> `Serial Monitor`, set baud to **115200**.

Type `yellow` and press Enter — the yellow LED should start breathing. Try `green`, `red`, `off`, and `ping` (which should reply `ai-status-light`).

If that works, you're done with the firmware side. Close Serial Monitor (it holds the port and would block the `light` CLI), then run [`install.sh`](../install.sh) from the repo root.
