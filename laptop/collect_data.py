import cv2
import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "dataset" / "collected"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def collect_images(camera_id: int = 0, class_name: str = "fire"):
    """
    Capture images from camera for dataset collection.

    Controls:
      SPACE  - save current frame as {class_name}_XXXX.jpg
      f      - switch class to 'fire'
      s      - switch class to 'smoke'
      ESC/q  - quit
    """
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"[Collect] Cannot open camera {camera_id}")
        return

    counter = 0
    class_name = class_name.lower()
    print(f"[Collect] Class: {class_name.upper()}")
    print("[Collect] SPACE=save  f=fire  s=smoke  ESC/q=quit")
    print(f"[Collect] Saving to: {OUTPUT_DIR}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Collect] Failed to read frame")
            break

        display = frame.copy()
        cv2.putText(
            display,
            f"Class: {class_name.upper()} | Saved: {counter}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Data Collection - Press SPACE to capture", display)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            break
        elif key == ord(" "):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{class_name}_{timestamp}.jpg"
            filepath = OUTPUT_DIR / filename
            cv2.imwrite(str(filepath), frame)
            counter += 1
            print(f"[Collect] Saved: {filepath}")
        elif key == ord("f"):
            class_name = "fire"
            print(f"[Collect] Switched to: FIRE")
        elif key == ord("s"):
            class_name = "smoke"
            print(f"[Collect] Switched to: SMOKE")

    cap.release()
    cv2.destroyAllWindows()
    print(f"[Collect] Done. {counter} images saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    camera = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cls = sys.argv[2] if len(sys.argv) > 2 else "fire"
    collect_images(camera, cls)
