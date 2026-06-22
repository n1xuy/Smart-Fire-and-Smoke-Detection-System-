import os
import sys
import shutil
import zipfile
from pathlib import Path

import torch
from ultralytics import YOLO

BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

ROBOFLOW_WORKSPACE = "middle-east-tech-university"
ROBOFLOW_PROJECT = "fire-and-smoke-detection-hiwia"
ROBOFLOW_VERSION = 2

CLASS_NAMES = ["fire", "smoke"]


def _prompt_api_key() -> str:
    print("\n" + "=" * 60)
    print("  Roboflow API Key Required")
    print("=" * 60)
    print("  1. Go to https://roboflow.com  |  Sign up (free)")
    print("  2. Go to https://universe.roboflow.com/settings/api")
    print("  3. Copy your API key")
    print("=" * 60)
    key = input("Enter your Roboflow API key: ").strip()
    if not key:
        print("[Train] No API key provided. Exiting.")
        sys.exit(1)
    return key


def download_dataset(api_key: str) -> Path:
    from roboflow import Roboflow

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT)
    version = project.version(ROBOFLOW_VERSION)
    dataset = version.download("yolov8", location=str(DATASET_DIR))
    path = Path(dataset.location)
    print(f"[Train] Dataset downloaded to: {path}")
    return path


def _find_yaml(path: Path):
    if (path / "data.yaml").exists():
        return path / "data.yaml"
    for z in path.glob("*.zip"):
        print(f"[Train] Extracting {z.name}...")
        with zipfile.ZipFile(z, "r") as zf:
            zf.extractall(path)
        z.unlink()
    if (path / "data.yaml").exists():
        return path / "data.yaml"
    for sub in path.iterdir():
        if sub.is_dir():
            yaml = _find_yaml(sub)
            if yaml:
                return yaml
    return None


def verify_dataset(path: Path) -> bool:
    yaml = _find_yaml(path)
    if not yaml:
        return False
    import yaml as pyyaml
    with open(yaml) as f:
        cfg = pyyaml.safe_load(f)
    names = cfg.get("names", [])
    print(f"[Train] Dataset classes: {names}")
    print(f"[Train] data.yaml: {yaml}")
    return True


def train(dataset_path: Path, model_size: str = "s", epochs: int = 150, imgsz: int = 640):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Train] Device: {device}")
    if device == "cuda":
        print(f"[Train] GPU: {torch.cuda.get_device_name(0)}  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    model = YOLO(f"yolo11{model_size}.pt")

    data_yaml = str(_find_yaml(dataset_path))

    batch_size = 32 if device == "cuda" else 8

    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=0 if device == "cuda" else "cpu",
        patience=30,
        save=True,
        project=str(MODELS_DIR / "training"),
        name="fire_smoke",
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        cos_lr=True,
        augment=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        close_mosaic=10,
        val=True,
        workers=4,
    )

    best_src = MODELS_DIR / "training" / "fire_smoke" / "weights" / "best.pt"
    dst = MODELS_DIR / "best.pt"

    if best_src.exists():
        shutil.copy2(best_src, dst)
        print(f"[Train] Model saved: {dst} ({best_src.stat().st_size / 1024:.0f} KB)")
    else:
        last_src = MODELS_DIR / "training" / "fire_smoke" / "weights" / "last.pt"
        if last_src.exists():
            shutil.copy2(last_src, dst)
            print(f"[Train] Last checkpoint saved: {dst}")

    try:
        metrics = model.val()
        print(f"[Train] mAP@0.5: {metrics.results_dict.get('metrics/mAP_0.5', 0):.3f}")
    except Exception as e:
        print(f"[Train] Validation metrics unavailable: {e}")

    print(f"\n[Train] Done! Model ready at: {dst}")
    return dst


def main():
    print("=" * 60)
    print("  Smart Fire & Smoke Detection - YOLO Training")
    print("=" * 60)

    if not torch.cuda.is_available():
        print("\n[WARN] CUDA not detected. CPU training will be very slow.")
        force_cpu = os.environ.get("FORCE_CPU", "").lower() in ("1", "true", "yes")
        if not force_cpu:
            try:
                ans = input("Continue with CPU anyway? (y/N): ").strip().lower()
                if ans != "y":
                    print("[Train] Aborted.")
                    sys.exit(0)
            except EOFError:
                print("[Train] Non-interactive mode. Set FORCE_CPU=1 to skip this prompt.")
                sys.exit(0)

    key = os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        key = _prompt_api_key()

    print(f"\n[Train] Downloading dataset: {ROBOFLOW_WORKSPACE}/{ROBOFLOW_PROJECT} v{ROBOFLOW_VERSION}")
    dataset_path = download_dataset(key)

    if not verify_dataset(dataset_path):
        print("[Train] Dataset verification failed. Aborting.")
        sys.exit(1)

    model_size = os.environ.get("YOLO_MODEL_SIZE", "s")
    epochs = int(os.environ.get("YOLO_EPOCHS", "150"))

    print(f"\n[Train] Starting training  model=yolo11{model_size}  epochs={epochs}")
    train(dataset_path, model_size=model_size, epochs=epochs)


if __name__ == "__main__":
    main()
