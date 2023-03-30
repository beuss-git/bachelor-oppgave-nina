"""Detection module for running inference on video."""
import time
from pathlib import Path
from typing import Any, Callable, List, Tuple

import cv2
import torch
from tqdm import tqdm
from ultralytics.yolo.utils.plotting import Annotator

from app.logger import get_logger

from .batch_yolov8 import BatchYolov8
from .frame_grabber import ThreadedFrameGrabber

logger = get_logger()


def __create_video_writer(
    save_path: Path,
    fps: float,
    width: int,
    height: int,
    fourcc: str = "mp4v",
) -> cv2.VideoWriter:
    """Create a video writer object.

    Args:
        save_path: The path to save the video to.
        fps: The frames per second of the video.
        width: The width of the video.
        height: The height of the video.
        fourcc: The fourcc code for the video. Defaults to "mp4v".

    Returns:
        The video writer object.
    """
    save_path = save_path.with_suffix(".mp4")  # force *.mp4 suffix on results videos
    return cv2.VideoWriter(
        str(save_path), cv2.VideoWriter_fourcc(*fourcc), fps, (width, height)
    )


def __annotate_batch(
    vid_writer: cv2.VideoWriter,
    results: List[torch.Tensor],
    img0s: List[Any],
    names: List[str],
) -> None:
    """Annotates a batch of images and writes them to a video."""

    for predictions, img0 in zip(results, img0s):
        # pred = F.softmax(res, dim=1)  # probabilities
        annotator = Annotator(img0, line_width=2, example=str(names), pil=True)
        for pred in predictions:
            # top5i = prob.argsort(0, descending=True)[:5].tolist()  # top 5 indices
            text = f"{pred['conf']:.2f} {pred['name']}"
            # annotator.text((32, 32), text, txt_color=(0, 255, 255))
            bndbox = pred["bndbox"]

            xyxy = (bndbox["xmin"], bndbox["ymin"], bndbox["xmax"], bndbox["ymax"])
            annotator.box_label(xyxy, text, color=(255, 0, 255))
        im0 = annotator.result()

        # Write to the video
        vid_writer.write(im0)


def __process_batch(
    original_batch: List[Any],
    processed_batch: torch.Tensor,
    model: BatchYolov8,
) -> Tuple[List[torch.Tensor], float]:
    """Process a batch of frames.

    Args:
        batch: Batch of frames
        model: The Yolov8 model

    Returns:
        The time it took to process the batch.
    """

    start_time = time.time()
    predictions = model.predict_batch(original_batch, processed_batch)
    end_time = time.time()
    delta = end_time - start_time
    return predictions, delta


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def process_video(
    model: BatchYolov8,
    video_path: Path,
    batch_size: int,
    max_batches_to_queue: int,
    output_path: Path | None,
    notify_progress: Callable[[int], None] | None = None,
) -> List[int]:
    """Runs inference on a video. And returns a list of frames containing fish.

    Args:
        model: The Yolov8 batcher model.
        video_path: The path to the video to process.
        batch_size: The batch size.
        max_batches_to_queue: The maximum number of batches to queue.
        output_path: The path to save the output video to.

    Returns:
        A list of frames containing fish.
    """

    try:
        frame_grabber = ThreadedFrameGrabber(
            model=model,
            video_path=video_path,
            batch_size=batch_size,
            max_batches_to_queue=max_batches_to_queue,
        )
    except RuntimeError as err:
        logger.error("Failed to initialize frame grabber", exc_info=err)
        # print("Failed to initialize frame grabber", err)
        return []

    # Wait for the first batch to be ready
    while frame_grabber.batches_in_queue() == 0:
        time.sleep(0.1)

    if output_path is not None:
        vid_cap = frame_grabber.capture
        video_writer = __create_video_writer(
            save_path=output_path,
            fps=vid_cap.get(cv2.CAP_PROP_FPS),
            width=int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )

    frames_with_fish = []
    try:
        fps_count = 0.0
        frame_count = 0

        with tqdm(
            total=frame_grabber.total_batch_count(), desc="Processing batches"
        ) as pbar:
            while not frame_grabber.is_done() or not frame_grabber.batch_queue.empty():
                [processed_batch, original_batch] = frame_grabber.get_batch()
                if processed_batch is None:
                    # This will happen if the batch size is too large or if the disk is too slow
                    # The grabber can't keep up with the inference speed
                    logger.warning("No batch available, waiting...")
                    # print("No batch available, waiting...")
                    # Wait for more batches to be available
                    time.sleep(0.1)
                    continue

                (predictions, delta) = __process_batch(
                    original_batch, processed_batch, model
                )

                batch_fps = len(processed_batch) / delta
                fps_count += batch_fps
                pbar.update(1)
                pbar.set_description(f"Processing batches (FPS: {batch_fps:.2f})")

                # Annotate the batch
                if output_path is not None:
                    __annotate_batch(
                        vid_writer=video_writer,
                        results=predictions,
                        img0s=original_batch,
                        names=model.names,
                    )

                # Check if any of the frames in the batch contain fish
                for i, pred in enumerate(predictions):
                    if len(pred) > 0:
                        frames_with_fish.append(frame_count + i)

                # Update the frame count
                frame_count += len(original_batch)
                if notify_progress is not None:
                    notify_progress((pbar.n / pbar.total) * 100)
        if notify_progress is not None:
            notify_progress(100)
        print(f"Average FPS: {fps_count / frame_grabber.total_batch_count()}")
    except RuntimeError as err:
        logger.error("Failed to process video", exc_info=err)
        # print(err)
        return []

    return frames_with_fish
