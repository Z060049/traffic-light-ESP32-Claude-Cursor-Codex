# Wiring

Connect the traffic-light module to the ESP32 with four jumper wires.

| Module pin | ESP32 pin |
|---|---|
| `GND` | `GND`     |
| `R`   | `GPIO16`  |
| `Y`   | `GPIO17`  |
| `G`   | `GPIO18`  |

```
Traffic Light Module          ESP32
--------------------          -----
GND ------------------------- GND
R   ------------------------- GPIO16
Y   ------------------------- GPIO17
G   ------------------------- GPIO18
```

That's it. No resistors needed if the LED module has them built in (most do — there's usually a small SMD resistor next to each LED on the PCB).

## Active-high vs active-low

The default firmware assumes **active-high**: the GPIO is driven `HIGH` to turn an LED on. Most cheap modules are wired this way.

If your module is wired the other way (common-anode style: LEDs share `+V` and turn on when the GPIO is pulled `LOW`), open [`firmware/esp32-traffic-light/esp32-traffic-light.ino`](../firmware/esp32-traffic-light/esp32-traffic-light.ino) and flip:

```cpp
#define ACTIVE_HIGH 1
```

to:

```cpp
#define ACTIVE_HIGH 0
```

Then re-upload. The `LED_ON`/`LED_OFF` macros and the PWM duty inversion are handled for you.

## Different pin numbers?

If you want to use different GPIOs, change these three lines at the top of the firmware:

```cpp
#define RED_PIN 16
#define YELLOW_PIN 17
#define GREEN_PIN 18
```

Yellow and green need to be PWM-capable pins (most ESP32 GPIOs are). Red can be any GPIO.
