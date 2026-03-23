#include <WiFi.h>
#include <PubSubClient.h>

// Local secrets (not committed). See wifi_secrets.h.example
#include "wifi_secrets.h"
#include <ArduinoJson.h>

// --- HARDWARE DEFINITIONS ---
#define BUS_VOLTAGE 34
#define LOAD_VOLTAGE 35
#define LOAD_CURRENT 32
#define BUS_CURRENT 33

// EDIT: Relay GPIO pin(s)
// Original board uses a single relay for load1.
// If you move wiring, change this define.
#define LOAD1_RELAY 25

#define REF_VOLTAGE 3.3
#define ADC_RESOLUTION 4096.0
#define R1 30000.0
#define R2 7500.0

const float SENSITIVITY = 0.066;
const float ZERO_POINT = 2.5;

// --- RELAY ELECTRICAL BEHAVIOR ---
// EDIT: many relay modules are active-low (LOW = ON, HIGH = OFF)
static const bool RELAY_ACTIVE_LOW = true;

// --- Device Identity ---
// There are only 2 ESPs in this system:
// - "bus_load1": measures bus + controls load1 relay
// - "load2": second node for load2 (if/when you add a second relay + sensors)
// EDIT THIS PER BOARD.
const char* device_id = "bus_load1";

// --- HYSTERESIS SETTINGS ---
const float V_ON_THRESHOLD = 8.5;
const float V_OFF_THRESHOLD = 8.0;
bool loadActive = false;

// --- Manual Override ---
// When true, digital twin has direct control of the relay and local hysteresis is disabled.
bool manualOverride = false;

// --- NETWORK CONFIGURATION ---
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const char* mqtt_server = MQTT_SERVER;

// --- MQTT TOPICS ---
const char* topic_telemetry = "microgrid/telemetry";
const char* topic_control = "microgrid/control/relays";
const char* topic_ack = "microgrid/control/ack";

// --- TIMING ---
unsigned long last_telemetry_time = 0;
const unsigned long telemetry_interval = 2000; // 2 Seconds

WiFiClient espClient;
PubSubClient client(espClient);

static inline void relayWriteLoad1(bool on) {
  // on=true => load connected
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(LOAD1_RELAY, on ? LOW : HIGH);
  } else {
    digitalWrite(LOAD1_RELAY, on ? HIGH : LOW);
  }
}

void setup() {
  Serial.begin(115200);
  analogSetAttenuation(ADC_11db);

  pinMode(LOAD1_RELAY, OUTPUT);
  // Default OFF (Safe Mode)
  relayWriteLoad1(false);
  loadActive = false;

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(mqtt_callback);
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

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  // Integrate digital-twin control while preserving original behavior.
  // Supports:
  // 1) Legacy string commands: OPEN_RELAY / CLOSE_RELAY
  // 2) JSON commands (v=1) on microgrid/control/relays with ACK on microgrid/control/ack

  // --- First: try JSON ---
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (!err) {
    const int v = doc["v"] | 0;
    const char* cmdId = doc["command_id"] | "";
    const char* target = doc["target"] | "all";
    const char* type = doc["type"] | "";

    if (v == 1) {
      if (strcmp(target, "all") != 0 && strcmp(target, device_id) != 0) {
        return;
      }

      bool hasRelay1 = false;
      bool appliedRelay1 = false;

      if (strcmp(type, "set_relays") == 0) {
        JsonObject data = doc["data"].as<JsonObject>();
        if (!data.isNull() && data.containsKey("relay1")) {
          hasRelay1 = true;
          appliedRelay1 = (bool)data["relay1"];
          // Only bus_load1 physically controls relay1 in the 2-ESP setup
          if (strcmp(device_id, "bus_load1") == 0) {
            relayWriteLoad1(appliedRelay1);
            loadActive = appliedRelay1;
            manualOverride = true;
          }
          Serial.printf(">>> JSON COMMAND: set_relays relay1=%s\n", appliedRelay1 ? "ON" : "OFF");
        }
      } else if (strcmp(type, "load_mode") == 0) {
        // data.mode: AUTO | ON | OFF
        const char* mode = doc["data"]["mode"] | "";
        if (strcmp(mode, "AUTO") == 0) {
          manualOverride = false;
          Serial.println(">>> LOAD MODE: AUTO (local hysteresis enabled)");
        } else if (strcmp(mode, "ON") == 0) {
          manualOverride = true;
          hasRelay1 = true;
          appliedRelay1 = true;
          relayWriteLoad1(true);
          loadActive = true;
          Serial.println(">>> LOAD MODE: ON (manual override)");
        } else if (strcmp(mode, "OFF") == 0) {
          manualOverride = true;
          hasRelay1 = true;
          appliedRelay1 = false;
          relayWriteLoad1(false);
          loadActive = false;
          Serial.println(">>> LOAD MODE: OFF (manual override)");
        }
      } else if (strcmp(type, "shed_load") == 0) {
        const char* which = doc["data"]["which"] | ""; // load1 | load2
        if (strcmp(which, "load1") == 0) {
          hasRelay1 = true;
          appliedRelay1 = false;
          if (strcmp(device_id, "bus_load1") == 0) {
            relayWriteLoad1(false);
            loadActive = false;
            manualOverride = true;
          }
          Serial.println(">>> JSON COMMAND: shed_load load1 (OPEN)");
        }
      }

      // Publish ACK (even if this board didn't physically have that relay)
      StaticJsonDocument<256> ack;
      ack["v"] = 1;
      ack["command_id"] = cmdId;
      ack["device_id"] = device_id;
      ack["status"] = "applied";
      JsonObject applied = ack.createNestedObject("applied");
      if (hasRelay1) applied["relay1"] = appliedRelay1;
      char out[256];
      size_t n = serializeJson(ack, out);
      out[n] = '\0';
      client.publish(topic_ack, out);
      return;
    }
  }

  // --- Fallback: legacy string commands ---
  String message = "";
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];

  // Remote Override Logic
  if (message == "OPEN_RELAY") {
    relayWriteLoad1(false);
    loadActive = false;
    Serial.println(">>> REMOTE COMMAND: LOAD SHED (OPEN)");
  } else if (message == "CLOSE_RELAY" && !loadActive) {
    // Logic would go here if you allow remote override to turn it ON
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Unique client ID per ESP (prevents boards kicking each other off the broker)
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

void loop() {
  if (!client.connected()) reconnect();
  client.loop(); // Essential for receiving commands

  unsigned long now = millis();

  // 1. DATA ACQUISITION & HYSTERESIS (Run every loop for safety)
  float bus_v = readVoltage(BUS_VOLTAGE);
  float load_v = readVoltage(LOAD_VOLTAGE);
  float bus_i = readCurrent(BUS_CURRENT);
  float load_i = readCurrent(LOAD_CURRENT);

  // Local Hysteresis Logic (disabled when digital twin manual override is active)
  if (!manualOverride) {
    if (!loadActive && bus_v > V_ON_THRESHOLD) {
      relayWriteLoad1(true);
      loadActive = true;
    } else if (loadActive && bus_v < V_OFF_THRESHOLD) {
      relayWriteLoad1(false);
      loadActive = false;
    }
  }

  // Cleanup Load I based on state
  if (!loadActive) load_i = 0.00;

  // 2. TELEMETRY TRANSMISSION (Every 2 seconds)
  if (now - last_telemetry_time >= telemetry_interval) {
    last_telemetry_time = now;
    sendTelemetry(bus_v, load_v, bus_i, load_i);
  }
}

float readVoltage(int pin) {
  int val = analogRead(pin);
  float adc_v = ((float)val * REF_VOLTAGE) / ADC_RESOLUTION;
  return adc_v * (R1 + R2) / R2;
}

float readCurrent(int pin) {
  int val = analogRead(pin);
  float adc_v = ((float)val * REF_VOLTAGE) / ADC_RESOLUTION;
  float current = (adc_v - ZERO_POINT) / SENSITIVITY;
  current = abs(current);
  return (current < 0.15) ? 0.00 : current;
}

void sendTelemetry(float bV, float lV, float bI, float lI) {
  StaticJsonDocument<256> doc;

  // Keys mapped to Digital Twin state.py
  doc["solar_w"] = bV * bI; // Power calculation
  doc["load_w"] = lV * lI;
  doc["current_a"] = bI;
  doc["relay_status"] = loadActive;

  // Extra fields (non-breaking for backend): helps debugging & future load-shed logic
  doc["device_id"] = device_id;
  doc["bus_v"] = bV;

  char buffer[256];
  serializeJson(doc, buffer);
  client.publish(topic_telemetry, buffer);

  Serial.printf("Telemetry Sent: %.2fV | %.2fA | Load: %s\n", bV, bI, loadActive ? "ON" : "OFF");
}