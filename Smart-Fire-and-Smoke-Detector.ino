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

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER = "broker.emqx.io";
const int MQTT_PORT = 1883;
const char* TOPIC_SENSOR = "smoke_detector/esp32/sensor";
const char* TOPIC_CONTROL = "smoke_detector/esp32/control";

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

unsigned long lastSensorSend = 0;
const unsigned long SENSOR_INTERVAL = 500;

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
  digitalWrite(BUZZER, LOW);

  connectWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(callback);
}

void loop() {
  if (!mqtt.connected()) {
    connectMQTT();
  }
  mqtt.loop();

  unsigned long now = millis();
  if (now - lastSensorSend >= SENSOR_INTERVAL) {
    lastSensorSend = now;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int g = analogRead(MQ5PIN);

    String payload;
    if (isnan(t) || isnan(h)) {
      payload = "T:-- H:-- G:" + String(g);
    } else {
      payload = "T:" + String(t, 2) + " H:" + String(h, 2) + " G:" + String(g);
    }

    mqtt.publish(TOPIC_SENSOR, payload.c_str());
    Serial.println("[MQTT] Published: " + payload);
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
}

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
      case 'G': digitalWrite(GREEN_LED, HIGH); break;
      case 'Y': digitalWrite(YELLOW_LED, HIGH); break;
      case 'R': digitalWrite(RED_LED, HIGH); break;
    }
  }

  if (buzIdx >= 0) {
    int buzVal = msg.substring(buzIdx + 2).toInt();
    if (buzVal == 1) {
      digitalWrite(BUZZER, HIGH);
    } else if (buzVal == 2) {
      digitalWrite(BUZZER, (millis() / 500) % 2);
    } else {
      digitalWrite(BUZZER, LOW);
    }
  }
}
