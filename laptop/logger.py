import csv
import os
from datetime import datetime
from config import LOG_DIR

class Logger:
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = os.path.join(LOG_DIR, f"session_{timestamp}.csv")
        self.file = open(self.filepath, "w", newline="")
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            "timestamp", "temperature", "humidity", "gas",
            "yolo_fire_conf", "yolo_smoke_conf", "alert_state"
        ])
        self.file.flush()

    def log(self, sensor_data, vision_detections, alert_state):
        t = sensor_data.get("temperature", "")
        h = sensor_data.get("humidity", "")
        g = sensor_data.get("gas", "")

        fire_conf = ""
        smoke_conf = ""
        for det in vision_detections:
            if det["label"] == "fire":
                fire_conf = f"{det['confidence']:.3f}"
            elif det["label"] == "smoke":
                smoke_conf = f"{det['confidence']:.3f}"

        now = datetime.now().isoformat(timespec="milliseconds")
        self.writer.writerow([now, t, h, g, fire_conf, smoke_conf, alert_state])
        self.file.flush()

    def close(self):
        self.file.close()
