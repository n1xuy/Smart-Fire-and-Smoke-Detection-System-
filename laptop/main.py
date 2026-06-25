import time
import threading
from datetime import datetime
from config import STATE_SAFE, STATE_WARNING, STATE_ALARM
from mqtt_handler import MqttHandler
from decision_engine import DecisionEngine
from vision_engine import VisionEngine
from logger import Logger
from dashboard.app import start_dashboard

MAX_EVENTS = 50
PING_INTERVAL = 5

class SmartDetectorApp:
    def __init__(self):
        self.mqtt = MqttHandler()
        self.decision = DecisionEngine()
        self.vision = VisionEngine()
        self.logger = None
        self._running = False
        self.buzzer_muted = False
        self._last_cmd_led = None
        self._last_cmd_buzzer = None
        self._events = []
        self._last_ping = 0

        self.shared_data = {
            "sensor": {},
            "detections": [],
            "state": STATE_SAFE,
            "state_name": "SAFE",
            "led": "G",
            "buzzer": 0,
            "frame_jpeg": None,
            "trigger_reasons": [],
            "warmup_remaining": 600,
            "buzzer_muted": False,
            "latency_ms": None,
            "events": []
        }

    def add_event(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self._events.append({"time": now, "msg": msg})
        if len(self._events) > MAX_EVENTS:
            self._events.pop(0)

    def start(self):
        self.add_event("System started")
        print("[App] Starting Smart Fire & Smoke Detector...")

        if not self.mqtt.connect():
            self.add_event("MQTT connection failed")
            print("[App] MQTT connection failed. Continuing without ESP32.")
        else:
            self.add_event("MQTT connected")

        if not self.vision.start():
            self.add_event("Camera failed")
            print("[App] Camera failed. Continuing without vision.")
        else:
            self.add_event("Camera started")

        try:
            self.logger = Logger()
            self.add_event(f"Logging to {self.logger.filepath}")
            print(f"[App] Logging to {self.logger.filepath}")
        except Exception as e:
            self.add_event(f"Logger init failed: {e}")
            print(f"[App] Logger init failed: {e}")

        dashboard_thread = threading.Thread(target=start_dashboard, args=(self,), daemon=True)
        dashboard_thread.start()
        print(f"[App] Dashboard at http://localhost:5000")

        self._running = True
        self._main_loop()

    def _main_loop(self):
        while self._running:
            try:
                now = time.time()

                if now - self._last_ping >= PING_INTERVAL:
                    self.mqtt.send_ping()
                    self._last_ping = now

                self.vision.update()
                sensor = self.mqtt.get_data()
                detections = self.vision.get_detections()
                frame_jpeg = self.vision.get_frame_jpeg()

                state = self.decision.evaluate(sensor, detections)
                led, buzzer = self.decision.get_led_buzzer()

                if self.buzzer_muted:
                    buzzer = 0

                self.shared_data["buzzer_muted"] = self.buzzer_muted

                latency = sensor.get("latency_ms")
                self.shared_data["latency_ms"] = latency
                self.shared_data["sensor"] = sensor
                self.shared_data["detections"] = detections
                self.shared_data["state"] = state
                self.shared_data["state_name"] = self.decision.get_state_name(state)
                self.shared_data["trigger_reasons"] = self.decision.trigger_reasons
                self.shared_data["warmup_remaining"] = self.decision.warmup_remaining()
                self.shared_data["led"] = led
                self.shared_data["buzzer"] = buzzer
                self.shared_data["frame_jpeg"] = frame_jpeg

                if led != self._last_cmd_led or buzzer != self._last_cmd_buzzer:
                    self.mqtt.send_command(led, buzzer)
                    self._last_cmd_led = led
                    self._last_cmd_buzzer = buzzer
                    state_name = self.decision.get_state_name(state)
                    reasons = self.decision.trigger_reasons
                    if reasons:
                        for r in reasons:
                            self.add_event(f"{state_name}: {r}")
                    else:
                        self.add_event(f"State → {state_name}")
                    print(f"[App] Sent L:{led} B:{buzzer} — {state_name}")

                self.shared_data["events"] = list(self._events)

                if self.logger:
                    self.logger.log(sensor, detections, state)

                time.sleep(0.033)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.add_event(f"Error: {e}")
                print(f"[App] Error: {e}")
                time.sleep(1)

        self._cleanup()

    def toggle_buzzer(self):
        self.buzzer_muted = not self.buzzer_muted
        state = "MUTED" if self.buzzer_muted else "ACTIVE"
        self.add_event(f"Buzzer {state}")
        print(f"[App] Buzzer {state}")
        if self.logger:
            self.logger.log_buzzer_toggle(self.buzzer_muted)

    def _cleanup(self):
        self.add_event("System shutting down")
        print("[App] Shutting down...")
        self.vision.stop()
        self.mqtt.close()
        if self.logger:
            self.logger.close()

if __name__ == "__main__":
    app = SmartDetectorApp()
    app.start()
