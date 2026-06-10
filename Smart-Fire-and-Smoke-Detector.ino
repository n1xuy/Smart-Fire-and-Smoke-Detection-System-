#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ2PIN 34
#define RED_LED 21
#define YELLOW_LED 22
#define GREEN_LED 23
#define BUZZER 5

DHT dht(DHTPIN, DHTTYPE);

unsigned long lastSensorSend = 0;
unsigned long lastCommandRx = 0;
const unsigned long SENSOR_INTERVAL = 500;
const unsigned long FALLBACK_TIMEOUT = 5000;

char currentLED = 'G';
int currentBuzzer = 0;

float tempWarning = 40.0;
float tempAlarm = 50.0;
float humWarning = 20.0;
float humAlarm = 10.0;
int gasWarning = 500;
int gasAlarm = 800;

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

  lastCommandRx = millis();
}

void loop() {
  unsigned long now = millis();

  if (now - lastSensorSend >= SENSOR_INTERVAL) {
    lastSensorSend = now;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int g = analogRead(MQ2PIN);

    if (isnan(t) || isnan(h)) {
      Serial.println("T:-- H:-- G:" + String(g));
    } else {
      Serial.print("T:" + String(t, 2) + " H:" + String(h, 2) + " G:" + String(g));
      int fallbackAlert = evaluateFallback(t, h, g);
      if (fallbackAlert >= 0) {
        Serial.print(" A:" + String(fallbackAlert));
      }
      Serial.println();
    }
  }

  if (now - lastCommandRx >= FALLBACK_TIMEOUT) {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int g = analogRead(MQ2PIN);
    int state = evaluateFallback(t, h, g);
    if (state >= 0) {
      applyState(state);
    }
  }

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    parseCommand(line);
    lastCommandRx = millis();
  }
}

int evaluateFallback(float t, float h, int g) {
  if (isnan(t) || isnan(h)) return -1;

  int alarms = 0;
  int warnings = 0;

  if (t >= tempAlarm || g >= gasAlarm || h <= humAlarm) alarms++;
  else if (t >= tempWarning || g >= gasWarning || h <= humWarning) warnings++;

  if (alarms > 0) return 2;
  if (warnings > 0) return 1;
  return 0;
}

void applyState(int state) {
  switch (state) {
    case 0:
      digitalWrite(GREEN_LED, HIGH);
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(RED_LED, LOW);
      digitalWrite(BUZZER, LOW);
      break;
    case 1:
      digitalWrite(GREEN_LED, LOW);
      digitalWrite(YELLOW_LED, HIGH);
      digitalWrite(RED_LED, LOW);
      digitalWrite(BUZZER, (millis() / 500) % 2);
      break;
    case 2:
      digitalWrite(GREEN_LED, LOW);
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(RED_LED, HIGH);
      digitalWrite(BUZZER, HIGH);
      break;
  }
}

void parseCommand(String cmd) {
  int ledIdx = cmd.indexOf("L:");
  int buzIdx = cmd.indexOf("B:");

  if (ledIdx >= 0) {
    char ledVal = cmd.charAt(ledIdx + 2);
    currentLED = ledVal;
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
    int buzVal = cmd.substring(buzIdx + 2).toInt();
    currentBuzzer = buzVal;
    if (buzVal == 1) {
      digitalWrite(BUZZER, HIGH);
    } else if (buzVal == 2) {
      digitalWrite(BUZZER, (millis() / 500) % 2);
    } else {
      digitalWrite(BUZZER, LOW);
    }
  }
}
