# Hardware

This is the exact hardware used for the V1 prototype. Anything in the same class will work — the firmware doesn't care what brand the ESP32 is, as long as the USB-serial chip is one of the common ones (CH340, CP210x, FTDI, or Espressif native USB).

## Required

### 1. ESP32 development board

- Any "ESP32 DevKit"-style board with USB-C (or micro-USB).
- USB-serial chip: **CH340** (most common on cheap dev boards) or **CP210x**.
- ~$8-12.

> _TODO: replace this line with the exact product link you bought from._
> Search terms that work: `ESP32 dev board CH340 USB-C`.

### 2. Mini traffic-light LED module

A small PCB with three LEDs (red / yellow / green) and a 4-pin header (`R`, `Y`, `G`, `GND`). Common on Amazon and AliExpress under names like "Mini Traffic Light Module" or "Arduino Traffic Light LED Module".

- 4-pin header in the order R / Y / G / GND (or similar — check the silkscreen).
- 5V or 3.3V tolerant.
- ~$3-6.

> _TODO: replace this line with the exact product link you bought from._
> Search terms that work: `mini traffic light LED module Arduino`.

### 3. USB **data** cable

This one is critical. A charge-only cable will power the ESP32 (the LED on the board lights up) but **the serial port will never appear** in `/dev/cu.*`.

- USB-A to USB-C (most reliable).
- USB-C to USB-C **sometimes** does not work with cheap ESP32 boards because the C-to-C side requires CC resistor handling that the board may not implement.
- If your Mac only has USB-C, use USB-A-to-USB-C plus a USB-A-to-USB-C adapter.

### 4. Jumper wires

Four female-to-female jumper wires. (Or female-to-male if you're using a breadboard.)

## Optional

- **Breadboard** — for tidy wiring and faster iteration.
- **3M Dual Lock / Velcro / double-sided tape** — to stick the build to your monitor or desk.
- **3D-printed enclosure** — V3 of this project. STLs to come.
- **Heat-shrink tubing** — clean up jumper wires once the layout is final.

## What about non-ESP32 boards?

The firmware is written for ESP32 (Arduino-ESP32 core 3.x, which gives you `analogWrite`). Porting to an Arduino Nano or Pico is straightforward — the only ESP32-specific bit is the PWM API. You'd lose the future Wi-Fi roadmap (V4), though.
