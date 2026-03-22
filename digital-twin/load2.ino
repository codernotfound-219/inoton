#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- HARDWARE DEFINITIONS ---
// Node 2 only monitors its local load and control its local relay
#define LOAD_VOLTAGE 35
#define LOAD_CURRENT 32

// EDIT: Relay GPIO pin for Load 2
// GPIO25 is usually OK on ESP32, but wiring often differs between boards.
// Set this to the pin wired to IN1/IN2 on your relay module.
#define LOAD2_RELAY  25

#define REF_VOLTAGE 3.3
#define ADC_RESOLUTION 4096.0
#define R1 30000.0
#define R2 7500.0

const float SENSITIVITY = 0.066;
const float ZERO_POINT = 2.5;

// --- RELAY ELECTRICAL BEHAVIOR ---
static const bool RELAY_ACTIVE_LOW = true; 

// --- Device Identity ---
const char* device_id = "load2"; // Unique ID for this node

// --- Local State ---
bool loadActive = false;

// --- NETWORK CONFIGURATION ---
const char* ssid = "WIFI_SSID";
const char* password = "WIFI_PASSWORD";
const char* mqtt_server = "MQTT_BROKER_IP"; 

// --- MQTT TOPICS ---
const char* topic_telemetry = "microgrid/telemetry";
const char* topic_control = "microgrid/control/relays";
const char* topic_ack = "microgrid/control/ack";

// --- TIMING ---
unsigned long last_telemetry_time = 0;
const unsigned long telemetry_interval = 2000; 

WiFiClient espClient;
PubSubClient client(espClient);

// Helper to write to relay based on module type
void relayWriteLoad2(bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(LOAD2_RELAY, on ? LOW : HIGH);
  } else {
    digitalWrite(LOAD2_RELAY, on ? HIGH : LOW);
  }
}

void setup() {
  Serial.begin(115200);
  analogSetAttenuation(ADC_11db);

  pinMode(LOAD2_RELAY, OUTPUT);
  // Default ON so the relay module LED is expected to be ON at boot.
  // If you prefer safe-off, change to false.
  relayWriteLoad2(true);
  loadActive = true;

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
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  
  if (!err) {
    const int v = doc["v"] | 0;
    const char* cmdId = doc["command_id"] | "";
    const char* target = doc["target"] | "all";
    const char* type = doc["type"] | "";

    Serial.printf("Command Received [%s] id=%s type=%s target=%s\n", topic, cmdId, type, target);

    // Filter: only process if targeted at 'all' or specifically 'load2'
    if (v == 1) {
      if (strcmp(target, "all") != 0 && strcmp(target, device_id) != 0) {
        return;
      }

      bool hasRelay2 = false;
      bool appliedRelay2 = false;

      if (strcmp(type, "set_relays") == 0) {
        JsonObject data = doc["data"].as<JsonObject>();
        if (!data.isNull() && data.containsKey("relay2")) {
          hasRelay2 = true;
          appliedRelay2 = (bool)data["relay2"];
          relayWriteLoad2(appliedRelay2);
          loadActive = appliedRelay2;
          Serial.printf(">>> JSON CMD: set_relays relay2=%s\n", appliedRelay2 ? "ON" : "OFF");
        }
      } else if (strcmp(type, "shed_load") == 0) {
        const char* which = doc["data"]["which"] | "";
        if (strcmp(which, "load2") == 0) {
          hasRelay2 = true;
          appliedRelay2 = false;
          relayWriteLoad2(false);
          loadActive = false;
          Serial.println(">>> JSON CMD: shed_load load2 (OPEN)");
        }
      }

      if (hasRelay2) {
        StaticJsonDocument<256> ack;
        ack["v"] = 1;
        ack["command_id"] = cmdId;
        ack["device_id"] = device_id;
        ack["status"] = "applied";
        JsonObject applied = ack.createNestedObject("applied");
        applied["relay2"] = appliedRelay2;
        
        char out[256];
        size_t n = serializeJson(ack, out);
        out[n] = '\0';
        client.publish(topic_ack, out);
      }
    }
  }
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

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();

  // Load 2 doesn't use local bus hysteresis by default 
  // It waits for commands from the Digital Twin / Node 1

  if (now - last_telemetry_time >= telemetry_interval) {
    last_telemetry_time = now;
    
    float lV = readVoltage(LOAD_VOLTAGE);
    float lI = readCurrent(LOAD_CURRENT);

    // If relay is physically OFF, force current to zero to clean up noise
    if (!loadActive) lI = 0.00;

    sendTelemetry(lV, lI);
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

void sendTelemetry(float lV, float lI) {
  StaticJsonDocument<256> doc;

  // We send local data. Note: solar_w and current_a are omitted or set to 0
  // because load2 doesn't have bus-level sensors.
  doc["device_id"] = device_id;
  doc["load_w"] = lV * lI;
  doc["load_v"] = lV;
  doc["load_i"] = lI;
  doc["relay_status"] = loadActive;

  char buffer[256];
  serializeJson(doc, buffer);
  client.publish(topic_telemetry, buffer);

  Serial.printf("Telemetry (Load2): %.2fV | %.2fA | Relay: %s\n", lV, lI, loadActive ? "ON" : "OFF");
}