// AI Status Light - ESP32 firmware
//
// Listens on the USB serial port at 115200 baud and drives a 3-color
// (red / yellow / green) traffic-light LED module.
//
// Commands (newline-terminated):
//   red       solid red
//   yellow    breathing yellow (host should send this when AI starts working)
//   green     solid green; auto-turns off after GREEN_TIMEOUT_MS
//   off       all LEDs off
//   ping      replies with "ai-status-light" so the host can identify this board
//
// Requires Arduino-ESP32 core 3.x for analogWrite() support. If you are on
// core 2.x you will need to switch to the ledcAttach / ledcWrite API.

#define RED_PIN 16
#define YELLOW_PIN 17
#define GREEN_PIN 18

// Set to 0 if your traffic-light module is active-low (common-anode style:
// LEDs share +V and turn ON when the GPIO is pulled LOW). Most cheap modules
// are active-high, so this is the default.
#define ACTIVE_HIGH 1

#if ACTIVE_HIGH
  #define DIGITAL_ON  HIGH
  #define DIGITAL_OFF LOW
  inline int pwmValue(int brightness) { return brightness; }
#else
  #define DIGITAL_ON  LOW
  #define DIGITAL_OFF HIGH
  inline int pwmValue(int brightness) { return 255 - brightness; }
#endif

// How long green stays on before auto-turning off, in milliseconds.
const unsigned long GREEN_TIMEOUT_MS = 20000;

// One full breathe cycle (bright -> off -> bright), in milliseconds.
// Smaller = faster pulse. 1200 is a calm, factory-floor cadence.
const unsigned long YELLOW_BREATHE_PERIOD_MS = 1200;

// 0..255. Lower = dimmer. Green LEDs tend to be very bright at full duty.
const int GREEN_BRIGHTNESS = 60;

String currentState = "off";
unsigned long greenStartTime = 0;
unsigned long yellowBreathStartTime = 0;

void allOff() {
  digitalWrite(RED_PIN, DIGITAL_OFF);
  analogWrite(YELLOW_PIN, pwmValue(0));
  analogWrite(GREEN_PIN, pwmValue(0));
  currentState = "off";
}

void setRed() {
  digitalWrite(RED_PIN, DIGITAL_ON);
  analogWrite(YELLOW_PIN, pwmValue(0));
  analogWrite(GREEN_PIN, pwmValue(0));
  currentState = "red";
}

void setYellowBreathing() {
  digitalWrite(RED_PIN, DIGITAL_OFF);
  analogWrite(GREEN_PIN, pwmValue(0));
  currentState = "yellow";
  yellowBreathStartTime = millis();
}

void setGreen() {
  digitalWrite(RED_PIN, DIGITAL_OFF);
  analogWrite(YELLOW_PIN, pwmValue(0));
  analogWrite(GREEN_PIN, pwmValue(GREEN_BRIGHTNESS));
  currentState = "green";
  greenStartTime = millis();
}

void updateYellowBreathing() {
  unsigned long now = millis();
  unsigned long elapsed = (now - yellowBreathStartTime) % YELLOW_BREATHE_PERIOD_MS;
  float phase = (float)elapsed / (float)YELLOW_BREATHE_PERIOD_MS;

  int brightness;
  if (phase < 0.5f) {
    brightness = 255 - (int)(phase * 2.0f * 255);
  } else {
    brightness = (int)((phase - 0.5f) * 2.0f * 255);
  }

  analogWrite(YELLOW_PIN, pwmValue(brightness));
}

void setup() {
  Serial.begin(115200);

  pinMode(RED_PIN, OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);

  allOff();

  // Boot banner. Only visible if the host opens the port with DTR/RTS enabled
  // (which resets the chip). The CLI uses DTR/RTS=false to avoid the reset, so
  // it relies on the "ping" command below for handshake instead.
  Serial.println("ai-status-light ready");
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
    } else if (cmd == "ping") {
      Serial.println("ai-status-light");
      return;
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
