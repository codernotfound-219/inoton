// --- PIN DEFINITIONS ---
const int relayCharge = 25;    
const int relayDischarge = 26; 
const int voltagePin = 32;     
const int currentPin = 34;     

#include <WiFi.h>
#include <PubSubClient.h>

// Local secrets (not committed). See wifi_secrets.h.example
#include "wifi_secrets.h"
#include <ArduinoJson.h>

// --- Device Identity ---
// There are 3 ESPs total now; this node is dedicated to battery SOC + charge/discharge relays.
// EDIT ONLY if you change naming across the system.
const char* device_id = "battery";

// --- NETWORK CONFIGURATION ---
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const char* mqtt_server = MQTT_SERVER;

// --- MQTT TOPICS ---
const char* topic_telemetry = "microgrid/telemetry";
const char* topic_control = "microgrid/control/relays";
const char* topic_ack = "microgrid/control/ack";

// --- TIMING (MQTT publish) ---
unsigned long last_telemetry_time = 0;
const unsigned long telemetry_interval = 2000; // 2 seconds

WiFiClient espClient;
PubSubClient client(espClient);

// --- Manual Control / Safety ---
// Enforced dead-time when switching between CHARGE and DISCHARGE to prevent shoot-through.
static const unsigned long RELAY_DEADTIME_MS = 300; // EDIT if your converters need more

enum BatteryMode {
  MODE_IDLE = 0,
  MODE_CHARGE = 1,
  MODE_DISCHARGE = 2,
};

// When manualOverride is true, the ESP ignores voltage-based auto mode selection.
bool manualOverride = false;
BatteryMode manualMode = MODE_IDLE;

static inline const char* modeToString(BatteryMode mode) {
  switch (mode) {
    case MODE_CHARGE: return "CHARGE";
    case MODE_DISCHARGE: return "DISCHARGE";
    default: return "IDLE";
  }
}

static inline BatteryMode modeFromString(const char* mode) {
  if (mode == nullptr) return MODE_IDLE;
  if (strcmp(mode, "CHARGE") == 0) return MODE_CHARGE;
  if (strcmp(mode, "DISCHARGE") == 0) return MODE_DISCHARGE;
  return MODE_IDLE;
}

static inline void setModeSafe(BatteryMode mode) {
  // Break-before-make: always open both relays first, wait dead-time, then close the selected one.
  allRelaysOff();
  delay(RELAY_DEADTIME_MS);

  if (mode == MODE_CHARGE) {
    digitalWrite(relayDischarge, HIGH);
    delay(150);
    digitalWrite(relayCharge, LOW);
  } else if (mode == MODE_DISCHARGE) {
    digitalWrite(relayCharge, HIGH);
    delay(150);
    digitalWrite(relayDischarge, LOW);
  } else {
    allRelaysOff();
  }
}

void publishAck(const char* cmdId) {
  StaticJsonDocument<256> ack;
  ack["v"] = 1;
  ack["command_id"] = cmdId;
  ack["device_id"] = device_id;
  ack["status"] = "applied";
  JsonObject applied = ack.createNestedObject("applied");
  applied["manual_override"] = manualOverride;
  applied["battery_mode"] = modeToString(manualOverride ? manualMode : MODE_IDLE);
  char out[256];
  size_t n = serializeJson(ack, out);
  out[n] = '\0';
  client.publish(topic_ack, out);
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    return;
  }

  const int v = doc["v"] | 0;
  const char* cmdId = doc["command_id"] | "";
  const char* target = doc["target"] | "all";
  const char* type = doc["type"] | "";

  if (v != 1) return;
  if (strcmp(target, "all") != 0 && strcmp(target, device_id) != 0) return;

  if (strcmp(type, "battery_mode") == 0) {
    const char* mode = doc["data"]["mode"] | ""; // CHARGE | DISCHARGE | IDLE | AUTO
    if (strcmp(mode, "AUTO") == 0) {
      manualOverride = false;
      manualMode = MODE_IDLE;
      Serial.println(">>> MANUAL OVERRIDE: OFF (AUTO)");
    } else {
      manualOverride = true;
      manualMode = modeFromString(mode);
      setModeSafe(manualMode);
      Serial.print(">>> MANUAL MODE (battery_mode): ");
      Serial.println(modeToString(manualMode));
    }
    publishAck(cmdId);
    return;
  }

  // Optional: allow boolean relay control as well
  // Interprets relay_charge / relay_discharge in set_relays payload.
  if (strcmp(type, "set_relays") == 0) {
    JsonObject data = doc["data"].as<JsonObject>();
    if (!data.isNull()) {
      bool hasCharge = data.containsKey("relay_charge");
      bool hasDischarge = data.containsKey("relay_discharge");
      if (hasCharge || hasDischarge) {
        bool chargeOn = hasCharge ? (bool)data["relay_charge"] : false;
        bool dischargeOn = hasDischarge ? (bool)data["relay_discharge"] : false;

        manualOverride = true;
        if (chargeOn && dischargeOn) {
          // Safety: never allow both
          manualMode = MODE_IDLE;
        } else if (chargeOn) {
          manualMode = MODE_CHARGE;
        } else if (dischargeOn) {
          manualMode = MODE_DISCHARGE;
        } else {
          manualMode = MODE_IDLE;
        }

        setModeSafe(manualMode);
        Serial.print(">>> MANUAL MODE (set_relays): ");
        Serial.println(modeToString(manualMode));
        publishAck(cmdId);
        return;
      }
    }
  }
}

// --- CALIBRATION ---
const float vDividerRatio = 4.16;   // Your updated ratio for 3.7V battery
const float sensorVCC = 3.3;       

// --- THRESHOLDS for 3.7V Li-ion ---
const float FULL_CHARGE  = 4.15;    
const float START_CHARGE = 3.50;   
const float LOW_CUTOFF   = 3.10;    

// --- ACS712 SETTINGS ---
const float sensitivity = 0.100;    // 100mV/A for 20A sensor
float vOffset = 1.65;               // This will be auto-calculated in setup()

// --- SOC (State of Charge) for 1S 3.7V Li-ion/LiPo ---
// EDIT/Calibrate these endpoints for your pack under light load.
static const float LIION_EMPTY_V = 3.0;
static const float LIION_FULL_V = 4.2;

static inline float clampf(float x, float lo, float hi) {
  if (x < lo) return lo;
  if (x > hi) return hi;
  return x;
}

static inline int socPercentFromLiIonVoltage(float v) {
  float vv = clampf(v, LIION_EMPTY_V, LIION_FULL_V);
  float soc = (vv - LIION_EMPTY_V) * 100.0f / (LIION_FULL_V - LIION_EMPTY_V);
  int pct = (int)(soc + 0.5f);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

void setup_wifi() {
  Serial.print("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected.");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = String("ESP32_Microgrid_") + device_id;
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe(topic_control);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void sendTelemetry(float vBat, float iBat) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = device_id;
  doc["soc"] = socPercentFromLiIonVoltage(vBat);
  // Optional extras (non-breaking): helps validate SOC and battery behavior
  doc["battery_v"] = vBat;
  doc["battery_a"] = iBat;

  char buffer[256];
  serializeJson(doc, buffer);
  client.publish(topic_telemetry, buffer);
}

void setup() {
  Serial.begin(115200);
  pinMode(relayCharge, OUTPUT);
  pinMode(relayDischarge, OUTPUT);
  
  allRelaysOff();
  delay(1000); // Wait for power to stabilize

  // --- AUTO-ZERO CALIBRATION ---
  Serial.println("Calibrating Current Sensor... Keep Relays OFF");
  float totalV = 0;
  for(int i = 0; i < 50; i++) {
    totalV += (analogRead(currentPin) / 4095.0) * sensorVCC;
    delay(10);
  }
  vOffset = totalV / 50.0; // Sets the "Zero" point to the current resting voltage
  
  Serial.print("Calibration Complete. Offset set to: "); Serial.println(vOffset);
  Serial.println("--- B1 Node: System Active ---");

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(mqtt_callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float vBat = getSmoothedVoltage();
  float iBat = getAmps();

  // --- LOGIC CONTROL ---
  if (!manualOverride) {
    if (vBat >= FULL_CHARGE) {
      Serial.println(">> STATUS: BATTERY FULL - IDLE");
      allRelaysOff();
    }
    else if (vBat < START_CHARGE && vBat > 1.0) {
      Serial.println(">> STATUS: CHARGING (Buck Active)");
      setMode("CHARGE");
    }
    else if (vBat >= START_CHARGE && vBat < FULL_CHARGE) {
      Serial.println(">> STATUS: DISCHARGING (Boost Active)");
      setMode("DISCHARGE");
    }
    else if (vBat < LOW_CUTOFF && vBat > 1.0) {
      Serial.println("!! CRITICAL: LOW BATTERY - CUTOFF !!");
      allRelaysOff();
    }
  } else {
    Serial.print(">> STATUS: MANUAL OVERRIDE ");
    Serial.println(modeToString(manualMode));
  }

  // --- OUTPUT ---
  Serial.print("V_Battery:"); Serial.print(vBat);
  Serial.print(" | I_Amps:"); Serial.println(iBat);

  // --- MQTT TELEMETRY (SOC) ---
  unsigned long now = millis();
  if (now - last_telemetry_time >= telemetry_interval) {
    last_telemetry_time = now;
    sendTelemetry(vBat, iBat);
  }
  
  delay(1000);
}

// --- HELPER FUNCTIONS ---

float getSmoothedVoltage() {
  float sum = 0;
  for(int i = 0; i < 20; i++) sum += analogRead(voltagePin);
  return (sum / 20.0 / 4095.0) * sensorVCC * vDividerRatio;
}

float getAmps() {
  float sum = 0;
  for(int i = 0; i < 20; i++) sum += analogRead(currentPin);
  float voltage = (sum / 20.0 / 4095.0) * sensorVCC;
  
  // If result is very small, force it to 0.0 to avoid "noise"
  float amps = (voltage - vOffset) / sensitivity;
  if (abs(amps) < 0.15) amps = 0.0; 
  return amps;
}

void allRelaysOff() {
  digitalWrite(relayCharge, HIGH);
  digitalWrite(relayDischarge, HIGH);
}

void setMode(String mode) {
  if (mode == "CHARGE") {
    digitalWrite(relayDischarge, HIGH); 
    delay(150);
    digitalWrite(relayCharge, LOW);
  } 
  else if (mode == "DISCHARGE") {
    digitalWrite(relayCharge, HIGH); 
    delay(150);
    digitalWrite(relayDischarge, LOW);
  }
}