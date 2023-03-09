# pylint: skip-file
# mypy: ignore-errors

import logging
import os
import sys
from pathlib import Path

import torch

from app import settings
from app.detection import detection
from app.detection.batch_yolov8 import BatchYolov8
from app.logger import create_logger, get_logger
from app.timer import Timer
from app.video_processor import video_processor

MODELS_DIR = "app/vdi_perf_test/models"

MODEL_NAMES = [
    "yolov8n.pt",
    "yolov8s.pt",
    "yolov8m.pt",
    "yolov8l.pt",
    "yolov8x.pt",
]
BATCH_SIZES = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
# BATCH_SIZES = [1024]

DEVICE = "cuda:0"

VIDEO_INPUT = Path("app/vdi_perf_test/input.mp4")
VIDEO_OUTPUT = Path("app/vdi_perf_test/output.mp4")

log = get_logger()


def perform_test(
    model: BatchYolov8, batch_size: int = 64, max_batches_to_queue: int = 4
) -> None:
    with Timer(f"Processing video (batch_size={batch_size}, device={DEVICE})"):
        frames_with_fish = detection.process_video(
            model=model,
            video_path=VIDEO_INPUT,
            batch_size=batch_size,
            max_batches_to_queue=max_batches_to_queue,
            output_path=None,
        )

    # frame_ranges = detection.detected_frames_to_range(frames_with_fish, frame_buffer=3)

    # with Timer("Cutting video"):
    # Cut the video to the detected frames
    # video_processor.cut_video(VIDEO_INPUT, VIDEO_OUTPUT, frame_ranges)


def main() -> int:
    create_logger(level=logging.INFO)
    settings.setup()

    # MODEL_NAMES.reverse()
    for model_name in MODEL_NAMES:
        try:
            # Clear CUDA cache to free up memory from the last model/iteration
            log.info("Initializing %s", model_name)
            model = BatchYolov8(
                Path(os.path.join(MODELS_DIR, model_name)),
                DEVICE,
            )

        except Exception as err:
            log.error("Failed to load model %s: %s", model_name, err)
            return 1

        for batch_size in BATCH_SIZES:
            try:
                perform_test(model, batch_size=batch_size, max_batches_to_queue=4)
            except RuntimeError as err:
                if "CUDA out of memory" in str(err):
                    log.warning("Ran out of memory, skipping batch size %s", batch_size)
                else:
                    log.error("Failed to process video: %s", err)
                break

            except Exception as err:
                log.error("Failed to process video: %s", err)
                break  # might be due to OOM

        # free memory
        del model
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.reset_max_memory_cached()
    return 0


if __name__ == "__main__":
    sys.exit(main())
