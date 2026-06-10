import os

SERIAL_PORT = "COM4"
SERIAL_BAUD = 115200

CAMERA_ID = 0
YOLO_FRAME_INTERVAL = 5
YOLO_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best.pt")

THRESHOLDS = {
    "temp_warning": 40.0,
    "temp_alarm": 50.0,
    "hum_warning": 20.0,
    "hum_alarm": 10.0,
    "gas_warning": 500,
    "gas_alarm": 800,
    "yolo_fire_warning": 0.6,
    "yolo_fire_alarm": 0.7,
    "yolo_smoke_warning": 0.6,
    "yolo_smoke_alarm": 0.75
}

STATE_SAFE = 0
STATE_WARNING = 1
STATE_ALARM = 2

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000
