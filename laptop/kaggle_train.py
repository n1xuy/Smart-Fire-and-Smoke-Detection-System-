# ============================================================
# Smart Fire & Smoke Detection - YOLO Training on Kaggle
# ============================================================
# How to use:
# 1. Go to kaggle.com → Create New Notebook
# 2. Paste this entire cell
# 3. Run all cells
# 4. Download the trained model from Output
#
# 获取 Roboflow API Key：
#   1. 打开 https://roboflow.com 注册免费账号
#   2. 进入 https://universe.roboflow.com/settings/api
#   3. 复制你的 Private API Key 粘贴到下面

import os
import shutil
import zipfile
from pathlib import Path

import torch
from ultralytics import YOLO

# ── CONFIG ──
ROBOFLOW_API_KEY = ""  # ← 在这里填入你的 Roboflow API Key
YOLO_MODEL_SIZE = "x"  # "n"|"s"|"m"|"l"|"x" - 用 x 冲 85%+
EPOCHS = 300
IMGSZ = 640
DATASET_WORKSPACE = "middle-east-tech-university"
DATASET_PROJECT = "fire-and-smoke-detection-hiwia"
DATASET_VERSION = 2

BASE_DIR = Path("/kaggle/working")
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)


def download_dataset():
    from roboflow import Roboflow
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(DATASET_WORKSPACE).project(DATASET_PROJECT)
    version = project.version(DATASET_VERSION)
    dataset = version.download("yolov8", location=str(DATASET_DIR))
    path = Path(dataset.location)
    for z in path.glob("*.zip"):
        with zipfile.ZipFile(z, "r") as zf:
            zf.extractall(path)
        z.unlink()
    return path


def find_yaml(path: Path):
    if (path / "data.yaml").exists():
        return path / "data.yaml"
    for sub in path.iterdir():
        if sub.is_dir():
            yaml = find_yaml(sub)
            if yaml:
                return yaml
    return None


def train():
    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"[Train] Device: {device}")
    if torch.cuda.is_available():
        print(f"[Train] GPU: {torch.cuda.get_device_name(0)}")

    dataset_path = download_dataset()
    data_yaml = str(find_yaml(dataset_path))

    model = YOLO(f"yolo11{YOLO_MODEL_SIZE}.pt")

    model.train(
        data=data_yaml,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=16,
        device=device,
        patience=30,
        save=True,
        project=str(MODELS_DIR / "training"),
        name="fire_smoke",
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        cos_lr=True,
        augment=True,
        hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
        translate=0.1, scale=0.5, fliplr=0.5,
        mosaic=1.0, close_mosaic=10,
        val=True,
    )

    best = MODELS_DIR / "training" / "fire_smoke" / "weights" / "best.pt"
    dst = MODELS_DIR / "best.pt"
    if best.exists():
        shutil.copy2(best, dst)
        print(f"[Train] Model saved: {dst}")
    else:
        last = MODELS_DIR / "training" / "fire_smoke" / "weights" / "last.pt"
        if last.exists():
            shutil.copy2(last, dst)
            print(f"[Train] Last checkpoint saved: {dst}")

    # Copy to Kaggle output (named best_x.pt to not overwrite local best.pt)
    kaggle_out = Path("/kaggle/working")
    shutil.copy2(dst, kaggle_out / "best_x.pt")
    print(f"[Train] Output ready: {kaggle_out / 'best_x.pt'}")

    # Zip dataset for reproducibility
    shutil.make_archive(str(kaggle_out / "dataset"), "zip", dataset_path)
    print(f"[Train] Dataset archived: {kaggle_out / 'dataset.zip'}")


if __name__ == "__main__":
    train()
