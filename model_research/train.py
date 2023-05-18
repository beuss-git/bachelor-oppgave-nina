"""This is the main file to train the model."""
import ultralytics
from ultralytics import YOLO

# Use if you want to debug
# os.environ["CUDA_LAUNCH_BLOCKING"] = "1"


def train(resume: bool) -> None:
    """Train the model.

    Args:
        resume: If True, resume training from last checkpoint.
    """
    # Initialize with starting weights
    model = YOLO("yolov8s.pt")

    # Train
    model.train(
        resume=resume,
        data="nina.yaml",
        epochs=120,
        val=True,
        batch=8,
        imgsz=640,
        device=None,
        close_mosaic=10,
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.001,
        degrees=10,
        scale=0.6,
        perspective=0.0005,
        flipud=0.01,
        hsv_h=0.2,
        hsv_s=0.7,
        hsv_v=0.7,
        v5loader=True,
        workers=16,
    )


if __name__ == "__main__":
    # Perform checks
    ultralytics.checks()

    # Start/resume training
    train(resume=False)
