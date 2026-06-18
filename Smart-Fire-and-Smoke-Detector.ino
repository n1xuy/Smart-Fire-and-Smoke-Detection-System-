// ===== Communication Mode Selector =====
// Uncomment ONLY ONE of the following modes. Comment out the rest.
#define MODE_AP       // MQTT over ESP32 access point (default)
// #define MODE_SERIAL  // USB Serial (no WiFi)

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ5PIN 34
#define RED_LED 21
#define YELLOW_LED 22
#define GREEN_LED 23
#define BUZZER 5

DHT dht(DHTPIN, DHTTYPE);

#ifdef MODE_AP
const char* AP_SSID = "SmokeDetector_AP";
const char* AP_PASS = "detector123";
const IPAddress AP_IP(192, 168, 4, 1);
const IPAddress AP_SUBNET(255, 255, 255, 0);
const char* MQTT_BROKER = "192.168.4.100";
#endif

const int MQTT_PORT = 1883;
const char* TOPIC_SENSOR = "smoke_detector/esp32/sensor";
const char* TOPIC_CONTROL = "smoke_detector/esp32/control";

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

unsigned long lastSensorSend = 0;
const unsigned long SENSOR_INTERVAL = 500;
int buzzerMode = 0;

void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(RED_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(BUZZER, HIGH);

  #ifdef MODE_AP
    setupAP();
  #endif

  #if !defined(MODE_SERIAL)
    mqtt.setServer(MQTT_BROKER, MQTT_PORT);
    mqtt.setCallback(callback);
  #endif
}

void loop() {
  #if !defined(MODE_SERIAL)
    if (!mqtt.connected()) {
      connectMQTT();
    }
    mqtt.loop();
  #endif

  handleBuzzer();

  unsigned long now = millis();
  if (now - lastSensorSend >= SENSOR_INTERVAL) {
    lastSensorSend = now;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int g = analogRead(MQ5PIN);

    Serial.print("[DHT11] Temp: "); Serial.print(t); Serial.println(" °C");
    Serial.print("[DHT11] Hum: "); Serial.print(h); Serial.println(" %");
    Serial.print("[MQ5] Raw: "); Serial.println(g);
    if (isnan(t) || isnan(h)) {
      Serial.println("[DHT11] ERROR - NaN (check wiring)");
    }

    String payload;
    if (isnan(t) || isnan(h)) {
      payload = "T:-- H:-- G:" + String(g);
    } else {
      payload = "T:" + String(t, 2) + " H:" + String(h, 2) + " G:" + String(g);
    }

    #if defined(MODE_SERIAL)
      Serial.println(payload);
    #else
      mqtt.publish(TOPIC_SENSOR, payload.c_str());
      Serial.println("[MQTT] Published: " + payload);
    #endif
  }

  #if defined(MODE_SERIAL)
    handleSerialCommand();
  #endif
}

void handleBuzzer() {
  if (buzzerMode == 1) {
    digitalWrite(BUZZER, LOW);
  } else if (buzzerMode == 2) {
    digitalWrite(BUZZER, (millis() % 3000) < 200 ? LOW : HIGH);
  } else {
    digitalWrite(BUZZER, HIGH);
  }
}

#ifdef MODE_SERIAL
void handleSerialCommand() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    int ledIdx = line.indexOf("L:");
    int buzIdx = line.indexOf("B:");
    if (ledIdx >= 0) {
      char ledVal = line.charAt(ledIdx + 2);
      digitalWrite(GREEN_LED, LOW);
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(RED_LED, LOW);
      switch (ledVal) {
        case 'G': digitalWrite(GREEN_LED, HIGH); Serial.println("[LED] Green ON"); break;
        case 'Y': digitalWrite(YELLOW_LED, HIGH); Serial.println("[LED] Yellow ON"); break;
        case 'R': digitalWrite(RED_LED, HIGH); Serial.println("[LED] Red ON"); break;
      }
    }
    if (buzIdx >= 0) {
      buzzerMode = line.substring(buzIdx + 2).toInt();
      if (buzzerMode == 1) Serial.println("[BUZZER] Continuous ON");
      else if (buzzerMode == 2) Serial.println("[BUZZER] Intermittent (200ms/3s)");
      else Serial.println("[BUZZER] OFF");
    }
  }
}
#endif

#ifdef MODE_AP
void setupAP() {
  Serial.print("Starting AP: ");
  Serial.println(AP_SSID);
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(AP_IP, AP_IP, AP_SUBNET);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
}
#endif

void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqtt.connect("ESP32_SmokeDetector")) {
      Serial.println("connected");
      mqtt.subscribe(TOPIC_CONTROL);
      Serial.println("Subscribed to " + String(TOPIC_CONTROL));
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(" retrying in 5s");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  msg.trim();
  Serial.println("[MQTT] Received: " + msg);

  int ledIdx = msg.indexOf("L:");
  int buzIdx = msg.indexOf("B:");

  if (ledIdx >= 0) {
    char ledVal = msg.charAt(ledIdx + 2);
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(RED_LED, LOW);
    switch (ledVal) {
      case 'G': digitalWrite(GREEN_LED, HIGH); Serial.println("[LED] Green ON"); break;
      case 'Y': digitalWrite(YELLOW_LED, HIGH); Serial.println("[LED] Yellow ON"); break;
      case 'R': digitalWrite(RED_LED, HIGH); Serial.println("[LED] Red ON"); break;
    }
  }

  if (buzIdx >= 0) {
    buzzerMode = msg.substring(buzIdx + 2).toInt();
    if (buzzerMode == 1) {
      Serial.println("[BUZZER] Continuous ON");
    } else if (buzzerMode == 2) {
      Serial.println("[BUZZER] Intermittent (200ms/3s)");
    } else {
      Serial.println("[BUZZER] OFF");
    }
  }
}
