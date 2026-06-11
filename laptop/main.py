import time
import threading
from config import STATE_SAFE, STATE_WARNING, STATE_ALARM
from mqtt_handler import MqttHandler
from decision_engine import DecisionEngine
from vision_engine import VisionEngine
from logger import Logger
from dashboard.app import start_dashboard

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
            "buzzer_muted": False
        }

    def start(self):
        print("[App] Starting Smart Fire & Smoke Detector...")

        if not self.mqtt.connect():
            print("[App] MQTT connection failed. Continuing without ESP32.")

        if not self.vision.start():
            print("[App] Camera failed. Continuing without vision.")

        try:
            self.logger = Logger()
            print(f"[App] Logging to {self.logger.filepath}")
        except Exception as e:
            print(f"[App] Logger init failed: {e}")

        dashboard_thread = threading.Thread(target=start_dashboard, args=(self,), daemon=True)
        dashboard_thread.start()
        print(f"[App] Dashboard at http://localhost:5000")

        self._running = True
        self._main_loop()

    def _main_loop(self):
        while self._running:
            try:
                self.vision.update()
                sensor = self.mqtt.get_data()
                detections = self.vision.get_detections()
                frame_jpeg = self.vision.get_frame_jpeg()

                state = self.decision.evaluate(sensor, detections)
                led, buzzer = self.decision.get_led_buzzer()

                if self.buzzer_muted:
                    buzzer = 0

                self.shared_data["buzzer_muted"] = self.buzzer_muted

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
                    print(f"[App] Sent L:{led} B:{buzzer} — {state_name}")

                if self.logger:
                    self.logger.log(sensor, detections, state)

                time.sleep(0.1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[App] Error: {e}")
                time.sleep(1)

        self._cleanup()

    def toggle_buzzer(self):
        self.buzzer_muted = not self.buzzer_muted
        state = "MUTED" if self.buzzer_muted else "ACTIVE"
        print(f"[App] Buzzer {state}")
        if self.logger:
            self.logger.log_buzzer_toggle(self.buzzer_muted)

    def _cleanup(self):
        print("[App] Shutting down...")
        self.vision.stop()
        self.mqtt.close()
        if self.logger:
            self.logger.close()

if __name__ == "__main__":
    app = SmartDetectorApp()
    app.start()
