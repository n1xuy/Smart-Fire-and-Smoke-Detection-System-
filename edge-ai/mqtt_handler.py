import threading
import re
import time
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_SENSOR, MQTT_TOPIC_CONTROL, MQTT_TOPIC_PONG, MQTT_CLIENT_ID

SENSOR_REGEX = re.compile(r"T:([\d\.\-]+)\s+H:([\d\.\-]+)\s+G:(\d+)")

class MqttHandler:
    def __init__(self):
        self.lock = threading.Lock()
        self._data = {"temperature": None, "humidity": None, "gas": None, "latency_ms": None}
        self._connected = False
        self.last_seen = 0.0
        self._pending_ping = None
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"[MQTT] Connected to {MQTT_BROKER}")
            client.subscribe(MQTT_TOPIC_SENSOR)
            client.subscribe(MQTT_TOPIC_PONG)
            print(f"[MQTT] Subscribed to {MQTT_TOPIC_SENSOR} and {MQTT_TOPIC_PONG}")
        else:
            print(f"[MQTT] Connection failed, rc={rc}")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="ignore").strip()

        if msg.topic == MQTT_TOPIC_PONG:
            try:
                sent = float(payload)
                rtt = (time.time() - sent) * 1000
                with self.lock:
                    self._data["latency_ms"] = round(rtt / 2, 1)
                print(f"[MQTT] Pong — RTT: {rtt:.1f}ms, Latency: {rtt/2:.1f}ms")
            except ValueError:
                pass
            return

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
                self.last_seen = time.time()

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

    def send_ping(self):
        now = time.time()
        payload = f"P:{now}"
        result = self.client.publish(MQTT_TOPIC_CONTROL, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self._pending_ping = now
            print(f"[MQTT] Ping sent via control topic: {now}")

    def esp32_connected(self, timeout=10):
        if self.last_seen == 0:
            return False
        return time.time() - self.last_seen < timeout

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
