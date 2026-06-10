import time
import threading
from config import STATE_SAFE, STATE_WARNING, STATE_ALARM
from serial_handler import SerialHandler
from decision_engine import DecisionEngine
from vision_engine import VisionEngine
from logger import Logger
from dashboard.app import start_dashboard

class SmartDetectorApp:
    def __init__(self):
        self.serial = SerialHandler()
        self.decision = DecisionEngine()
        self.vision = VisionEngine()
        self.logger = None
        self._running = False

        self.shared_data = {
            "sensor": {},
            "detections": [],
            "state": STATE_SAFE,
            "state_name": "SAFE",
            "led": "G",
            "buzzer": 0,
            "frame_jpeg": None
        }

    def start(self):
        print("[App] Starting Smart Fire & Smoke Detector...")

        if not self.serial.connect():
            print("[App] Serial connection failed. Continuing without ESP32.")

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
                sensor = self.serial.get_data()
                detections = self.vision.get_detections()
                frame_jpeg = self.vision.get_frame_jpeg()

                state = self.decision.evaluate(sensor, detections)
                led, buzzer = self.decision.get_led_buzzer()

                self.shared_data["sensor"] = sensor
                self.shared_data["detections"] = detections
                self.shared_data["state"] = state
                self.shared_data["state_name"] = self.decision.get_state_name(state)
                self.shared_data["led"] = led
                self.shared_data["buzzer"] = buzzer
                self.shared_data["frame_jpeg"] = frame_jpeg

                if self.decision.state_changed():
                    self.serial.send_command(led, buzzer)
                    state_name = self.decision.get_state_name(state)
                    print(f"[App] State changed to {state_name}")

                if self.logger:
                    self.logger.log(sensor, detections, state)

                time.sleep(0.1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[App] Error: {e}")
                time.sleep(1)

        self._cleanup()

    def _cleanup(self):
        print("[App] Shutting down...")
        self.vision.stop()
        self.serial.close()
        if self.logger:
            self.logger.close()

if __name__ == "__main__":
    app = SmartDetectorApp()
    app.start()
