"""This is the main file to train the model."""
import ultralytics
from ultralytics import YOLO

# Use if you want to debug
# os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

if __name__ == "__main__":
    ultralytics.checks()
    model = YOLO("yolov8s.pt")
    model.train(
        data="nina_new.yaml",
        epochs=100,
        val=True,
        batch=16,
        imgsz=640,
        device=0,
        half=True,
        workers=8,
        v5loader=True,
    )  # train the model

    # model.val(data="brackish.yaml", batch_size=8)  # test the model
