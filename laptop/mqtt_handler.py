import threading
import re
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_SENSOR, MQTT_TOPIC_CONTROL, MQTT_CLIENT_ID

SENSOR_REGEX = re.compile(r"T:([\d\.\-]+)\s+H:([\d\.\-]+)\s+G:(\d+)")

class MqttHandler:
    def __init__(self):
        self.lock = threading.Lock()
        self._data = {"temperature": 0.0, "humidity": 0.0, "gas": 0}
        self._connected = False
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"[MQTT] Connected to {MQTT_BROKER}")
            client.subscribe(MQTT_TOPIC_SENSOR)
            print(f"[MQTT] Subscribed to {MQTT_TOPIC_SENSOR}")
        else:
            print(f"[MQTT] Connection failed, rc={rc}")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="ignore").strip()
        match = SENSOR_REGEX.search(payload)
        if match:
            t_str = match.group(1)
            h_str = match.group(2)
            g_str = match.group(3)
            with self.lock:
                if t_str != "--" and h_str != "--":
                    self._data["temperature"] = float(t_str)
                    self._data["humidity"] = float(h_str)
                self._data["gas"] = int(g_str)

    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            return False

    def get_data(self):
        with self.lock:
            return dict(self._data)

    def send_command(self, led, buzzer):
        payload = f"L:{led} B:{buzzer}"
        result = self.client.publish(MQTT_TOPIC_CONTROL, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[MQTT] Published: {payload}")
        else:
            print(f"[MQTT] Publish failed, rc={result.rc}")

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
