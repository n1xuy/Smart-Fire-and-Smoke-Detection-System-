import os

WIFI_SSID = "ssid"
WIFI_PASS = "password"

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "smoke_detector/esp32/sensor"
MQTT_TOPIC_CONTROL = "smoke_detector/esp32/control"
MQTT_CLIENT_ID = "laptop_ai_host"

CAMERA_ID = 0
YOLO_FRAME_INTERVAL = 5
YOLO_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best.pt")

THRESHOLDS = {
    "temp_warning": 40.0,
    "temp_alarm": 50.0,
    "hum_warning": 20.0,
    "hum_alarm": 10.0,
    # MQ-5 thresholds — may need recalibration (different sensitivity curve than MQ-2)
    "gas_warning": 1500,
    "gas_alarm": 1600,
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
