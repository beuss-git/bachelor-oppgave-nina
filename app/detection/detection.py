"""Detection module for running inference on video."""
import threading
import time
from pathlib import Path
from typing import Any, Callable, List, Tuple

import cv2
import torch
from tqdm import tqdm
from ultralytics.yolo.utils.plotting import Annotator

from app import settings
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
    colors: List[Tuple[int, int, int]],
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
            annotator.box_label(xyxy, text, color=colors[pred["class_id"]])
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
    predictions = model.predict_batch(
        original_batch, processed_batch, max_detections=settings.max_detections
    )
    end_time = time.time()
    delta = end_time - start_time
    return predictions, delta


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def process_video(  # pylint:disable=too-many-branches
    model: BatchYolov8,
    video_path: Path,
    batch_size: int,
    max_batches_to_queue: int,  # pylint: disable=unused-argument
    output_path: Path | None,
    stop_event: threading.Event,
    notify_progress: Callable[[int], None] | None = None,
    end_frame: int | None = None,
) -> Tuple[List[int], List[torch.Tensor]]:
    """Runs inference on a video.
    And returns a list of frames containing fish and a list of predictions for each frame.

    Args:
        model: The Yolov8 batcher model.
        video_path: The path to the video to process.
        batch_size: The batch size.
        max_batches_to_queue: The maximum number of batches to queue.
        output_path: The path to save the output video to.

    Returns:
        A tuple containing:
        1. A list of frames containing fish.
        2. A list of predictions for each frame.
    """

    with ThreadedFrameGrabber(
        model=model,
        video_path=video_path,
        batch_size=batch_size,
    ) as frame_grabber:
        if end_frame:
            frame_grabber.frame_count = min(end_frame, frame_grabber.frame_count)
        if output_path is not None:
            vid_cap = frame_grabber.capture
            video_writer = __create_video_writer(
                save_path=output_path,
                fps=vid_cap.get(cv2.CAP_PROP_FPS),
                width=int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )

        frames_with_fish = []
        fps_count = 0.0
        frame_count = 0
        processed_frames = 0

        predictions_per_frame: List[torch.Tensor] = []

        with tqdm(
            total=frame_grabber.frame_count, desc="Processing frames", leave=False
        ) as pbar:
            while not frame_grabber.is_done():
                if stop_event.is_set():
                    logger.info("Stopping video processing")
                    break

                batch = frame_grabber.get_batch()
                if batch is None:
                    continue

                processed_batch, original_batch = batch

                (predictions, delta) = __process_batch(
                    original_batch, processed_batch, model
                )

                batch_fps = len(processed_batch) / delta
                fps_count += batch_fps
                processed_frames += len(processed_batch)
                pbar.update(len(processed_batch))
                pbar.set_description(f"Processing frames (FPS: {batch_fps:.2f})")

                # Annotate the batch
                if output_path is not None:
                    __annotate_batch(
                        vid_writer=video_writer,
                        results=predictions,
                        img0s=original_batch,
                        names=model.names,
                        colors=model.colors,
                    )

                # Check if any of the frames in the batch contain fish
                for i, pred in enumerate(predictions):
                    if len(pred) > 0:
                        frames_with_fish.append(frame_count + i)
                    predictions_per_frame.append(pred)

                # Update the frame count
                frame_count += len(original_batch)

                if notify_progress is not None:
                    notify_progress(
                        int((processed_frames / frame_grabber.frame_count) * 100)
                    )
        if notify_progress is not None:
            notify_progress(100)

        # Close and release the video writer
        if output_path is not None and video_writer is not None:
            video_writer.release()
            logger.debug("Video writer released")

        if processed_frames != frame_grabber.frame_count:
            logger.warning(
                "Processed frames (%s) does not match total frames (%s)",
                processed_frames,
                frame_grabber.frame_count,
            )

        # Will be 0 if stop_event is set before any frames are processed
        if processed_frames > 0:
            logger.info(
                "Average FPS: %s",
                {fps_count / (processed_frames / frame_grabber.batch_size)},
            )

    return frames_with_fish, predictions_per_frame


def detected_frames_to_ranges(
    frames: List[int], frame_buffer: int
) -> List[Tuple[int, int]]:
    """Convert a list of detected frames to a list of ranges.
        Due to detection inaccuracies we need to allow for some dead frames
        without detections within a valid range.

    Args:
        frames: A list of detected frames.
        frame_buffer: The number of frames we allow to be without detection
                        before we consider it a new range.
    """

    if len(frames) == 0:
        return []

    frame_ranges: List[Tuple[int, int]] = []
    start_frame = frames[0]
    end_frame = frames[0]

    for frame in frames[1:]:
        if frame <= end_frame + frame_buffer:
            # Extend the range
            end_frame = frame
        else:
            # Start a new range
            frame_ranges.append((start_frame, end_frame))
            start_frame = frame
            end_frame = frame

    # Add the last range
    frame_ranges.append((start_frame, end_frame))

    return frame_ranges
