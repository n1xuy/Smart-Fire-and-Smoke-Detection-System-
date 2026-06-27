# Smart Fire & Smoke Detector (Prototype)

An edge AI prototype that detects fire and smoke using sensor data and computer vision. Built as an academic assignment.

## Components

- ESP32 DOIT DEVKIT V1
- DHT11 (temperature & humidity)
- MQ5 Gas Sensor
- Traffic Light Module (Red, Yellow, Green)
- Buzzer
- Laptop Camera
- Laptop (Edge AI host)

## How It Works

The ESP32 reads temperature, humidity, and gas levels then publishes the data over MQTT to the laptop. The laptop runs YOLOv8 on the camera feed to detect fire and smoke visually. A decision engine combines both inputs and commands the ESP32 to light up the traffic light and buzzer accordingly.

Communication uses MQTT over WiFi. By default the ESP32 acts as its own WiFi access point — no external router needed.

## Three Alert States

| State | Green | Yellow | Red | Buzzer |
|-------|-------|--------|-----|--------|
| Safe | ON | OFF | OFF | OFF |
| Warning | OFF | ON | OFF | Intermittent |
| Alarm | OFF | OFF | ON | Continuous |

## How to Use

### 1. Set laptop WiFi to static IP

Before connecting to the ESP32, set your laptop's WiFi adapter:

| Setting | Value |
|---------|-------|
| IP address | `192.168.4.100` |
| Subnet mask | `255.255.255.0` |
| Default gateway | `192.168.4.1` |

### 2. Install Mosquitto MQTT broker

If not already installed, download from https://mosquitto.org/download/ and install. Ensure the Mosquitto service is running (check Windows Services or task manager).

### 3. Upload ESP32 firmware

- Open `firmware/smart_detector.ino` in **Arduino IDE**
- Install required libraries (Library Manager):
  - **DHT sensor library** by Adafruit
  - **PubSubClient** by Nick O'Leary
- Select board: `DOIT ESP32 DEVKIT V1`, Port: e.g. `COM4`
- Click Upload
- Open Serial Monitor (115200 baud) to verify AP starts

### 4. Install Python dependencies

```bash
cd edge-ai
pip install -r requirements.txt
```

### 5. Connect laptop to ESP32

- In laptop WiFi settings, find and connect to `SmokeDetector_AP`
- Password: `detector123`

### 6. Run the laptop app

```bash
cd edge-ai
python main.py
```

### 7. Open dashboard

Go to `http://localhost:5000` in a browser.

## Wiring

| Component | ESP32 GPIO |
|-----------|-----------|
| DHT11 | GPIO 4 |
| Buzzer | GPIO 5 |
| Red LED | GPIO 21 |
| Yellow LED | GPIO 22 |
| Green LED | GPIO 23 |
| MQ5 (Analog) | GPIO 34 |

## Changing Communication Mode

The firmware includes two commented alternatives:

- **USB Serial**: Connect directly via USB cable (no WiFi needed)

To switch, open `firmware/smart_detector.ino`, comment/uncomment the relevant sections, and re-upload.

## Notes

- The YOLO model is not included. Place a trained fire/smoke model at `edge-ai/models/best.pt` or the path in `edge-ai/config.py`.
- The MQ5 sensor requires a ~30s warm-up after power-on.
- This is a prototype for academic purposes, not a production safety system.
