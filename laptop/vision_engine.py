import cv2
import numpy as np
from config import CAMERA_ID, YOLO_FRAME_INTERVAL, YOLO_MODEL_PATH

class VisionEngine:
    def __init__(self):
        self.cap = None
        self.model = None
        self._detections = []
        self._frame = None
        self._frame_count = 0
        self._running = False
        self._model_loaded = False

    def start(self):
        self.cap = cv2.VideoCapture(CAMERA_ID)
        if not self.cap.isOpened():
            print("[Vision] Could not open camera")
            return False

        try:
            from ultralytics import YOLO
            self.model = YOLO(YOLO_MODEL_PATH)
            try:
                import torch
                if torch.cuda.is_available():
                    self.model.to("cuda")
                    print(f"[Vision] Using GPU: {torch.cuda.get_device_name(0)}")
                else:
                    print("[Vision] CUDA not available, using CPU")
            except Exception:
                print("[Vision] Device setup failed, using CPU")
            self._model_loaded = True
        except Exception as e:
            print(f"[Vision] YOLO model not loaded ({e}). Running without detection.")
            self._model_loaded = False

        self._running = True
        return True

    def update(self):
        if not self._running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self._frame_count += 1
        self._frame = frame

        if self._model_loaded and self._frame_count % YOLO_FRAME_INTERVAL == 0:
            results = self.model(frame, device=self.model.device, verbose=False)[0]
            dets = []
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = results.names[cls_id]
                if label.lower() in ("fire", "smoke"):
                    dets.append({"label": label.lower(), "confidence": conf})
            self._detections = dets

    def get_detections(self):
        return list(self._detections)

    def get_annotated_frame(self):
        if self._frame is None:
            return None

        frame = self._frame.copy()
        if self._model_loaded:
            results = self.model(frame, device=self.model.device, verbose=False)[0]
            frame = results.plot()
        return frame

    def get_frame_jpeg(self):
        frame = self.get_annotated_frame()
        if frame is None:
            return None
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buffer.tobytes()

    def stop(self):
        self._running = False
        if self.cap:
            self.cap.release()
