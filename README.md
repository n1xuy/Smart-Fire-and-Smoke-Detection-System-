# Smart Fire & Smoke Detector (Prototype)

An edge AI prototype that detects fire and smoke using sensor data and computer vision. Built as an academic assignment.

## Components

- ESP32 DOIT DEVKIT V1
- DHT11 (temperature & humidity)
- MQ2 Gas Sensor
- Traffic Light Module (Red, Yellow, Green)
- Buzzer
- Laptop Camera
- Laptop (Edge AI host)

## How It Works

The ESP32 reads temperature, humidity, and gas levels then sends the data over USB Serial to the laptop. The laptop runs YOLOv8 on the camera feed to detect fire and smoke visually. A decision engine combines both inputs and commands the ESP32 to light up the traffic light and buzzer accordingly.

## Three Alert States

| State | Green | Yellow | Red | Buzzer |
|-------|-------|--------|-----|--------|
| Safe | ON | OFF | OFF | OFF |
| Warning | OFF | ON | OFF | Intermittent |
| Alarm | OFF | OFF | ON | Continuous |

## How to Use

### 1. Upload ESP32 firmware
- Open `firmware/smart_detector.ino` in **Arduino IDE**
- Install the **DHT sensor library** by Adafruit (Library Manager)
- Select board: `DOIT ESP32 DEVKIT V1`, Port: e.g. `COM4`
- Click Upload

### 2. Install Python dependencies
```bash
cd laptop
pip install -r requirements.txt
```

### 3. Run the laptop app
```bash
cd laptop
python main.py
```

### 4. Open dashboard
Go to `http://localhost:5000` in a browser.

The dashboard shows the camera feed with YOLO detections, live sensor readings, the traffic light state, and a rolling chart.

## Wiring

| Component | ESP32 GPIO |
|-----------|-----------|
| DHT11 | GPIO 4 |
| Buzzer | GPIO 5 |
| Red LED | GPIO 21 |
| Yellow LED | GPIO 22 |
| Green LED | GPIO 23 |
| MQ2 (Analog) | GPIO 34 |

## Notes

- The YOLO model (YOLOv8) is not included by default. Place a trained fire/smoke model at `laptop/models/best.pt` or the path specified in `laptop/config.py`.
- The MQ2 sensor requires a ~30s warm-up after power-on for stable readings.
- This is a prototype for academic purposes, not a production safety system.
