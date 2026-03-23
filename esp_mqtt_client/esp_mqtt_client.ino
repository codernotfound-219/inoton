#include <WiFi.h>
#include <PubSubClient.h>

// Local secrets (not committed). See wifi_secrets.h.example
#include "wifi_secrets.h"
#include <ArduinoJson.h>

// --- Network Configuration ---
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const char* mqtt_server = MQTT_SERVER;

// --- MQTT Topics ---
const char* topic_telemetry = "microgrid/telemetry";
const char* topic_control = "microgrid/control/relays";

// --- Timing ---
const unsigned long interval = 2000; // 2 Seconds
unsigned long last_run = 0;

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void setup_wifi() {
  Serial.print("\nConnecting to: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected. IP: " + WiFi.localIP().toString());
}

void callback(char* topic, byte* payload, unsigned int length) {
  // Convert payload to string for logic
  String message = "";
  for (int i = 0; i < length; i++) message += (char)payload[i];
  
  Serial.printf("Command Received [%s]: %s\n", topic, message.c_str());
  
  // Example Logic: Shutdown on Anomaly
  if (message == "OPEN_RELAY") {
    // digitalWrite(RELAY_PIN, LOW);
    Serial.println("🚨 EMERGENCY SHUTDOWN INITIATED");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect with a unique ID
    if (client.connect("ESP32_Microgrid_Node")) {
      Serial.println("connected");
      client.subscribe(topic_control); // Listen for backend commands
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  // 1. Maintain Connection
  if (!client.connected()) reconnect();
  
  // 2. Service MQTT background tasks (Keep-alive, Callbacks)
  client.loop();

  // 3. Non-blocking Telemetry Update
  unsigned long now = millis();
  if (now - last_run >= interval) {
    last_run = now;
    sendTelemetry();
  }
}

void sendTelemetry() {
  // Static allocation is faster and safer for microcontrollers
  StaticJsonDocument<256> doc;

  // READ SENSORS HERE
  // Example: doc["solar_w"] = analogRead(34) * (V_REF / 4095.0) * SCALING;
  doc["solar_w"] = 350.5 + (random(-5, 5)); 
  doc["soc"] = 78.2;
  doc["load_w"] = 110.0 + (random(-2, 2));

  char buffer[256];
  serializeJson(doc, buffer);
  
  if (client.publish(topic_telemetry, buffer)) {
    Serial.println("✅ Telemetry Sent: " + String(buffer));
  } else {
    Serial.println("❌ Failed to publish telemetry");
  }
}