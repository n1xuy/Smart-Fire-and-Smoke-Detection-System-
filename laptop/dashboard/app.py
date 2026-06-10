import json
import time
import base64
import threading
from flask import Flask, render_template, Response

app = Flask(__name__, template_folder="templates", static_folder="static")
app_ref = None

def start_dashboard(app_instance):
    global app_ref
    app_ref = app_instance

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/stream")
    def stream():
        def generate():
            while True:
                if app_ref:
                    data = app_ref.shared_data
                    sensor = data.get("sensor", {})
                    detections = data.get("detections", [])
                    state = data.get("state", 0)
                    state_name = data.get("state_name", "SAFE")
                    led = data.get("led", "G")
                    buzzer = data.get("buzzer", 0)

                    frame_jpeg = data.get("frame_jpeg")
                    frame_b64 = ""
                    if frame_jpeg:
                        frame_b64 = base64.b64encode(frame_jpeg).decode("utf-8")

                    payload = {
                        "temperature": sensor.get("temperature", "--"),
                        "humidity": sensor.get("humidity", "--"),
                        "gas": sensor.get("gas", "--"),
                        "detections": detections,
                        "state": state,
                        "state_name": state_name,
                        "led": led,
                        "buzzer": buzzer,
                        "frame": frame_b64
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.3)

        return Response(generate(), mimetype="text/event-stream")

    from config import DASHBOARD_HOST, DASHBOARD_PORT
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False, threaded=True)
