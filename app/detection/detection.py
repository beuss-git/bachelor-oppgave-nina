"""Detection module for running inference on video."""
import time
from pathlib import Path
from typing import List, Optional, Any, Tuple
import cv2
from tqdm import tqdm
import torch
import numpy as np
from yolov5.utils.plots import Annotator

from .batch_yolov5 import BatchYolov5
from .frame_grabber import ThreadedFrameGrabber


def create_video_writer(
    save_path: str,
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
    save_path = str(
        Path(save_path).with_suffix(".mp4")
    )  # force *.mp4 suffix on results videos
    return cv2.VideoWriter(
        save_path, cv2.VideoWriter_fourcc(*fourcc), fps, (width, height)
    )


def annotate_batch(
    vid_writer: cv2.VideoWriter,
    names: List[str],
    results: List[torch.Tensor],
    img0s: List[Any],
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
    batch: List[np.ndarray[Any, Any]], model: BatchYolov5
) -> Tuple[List[torch.Tensor], float]:
    """Process a batch of frames.

    Args:
        batch: Batch of frames
        model: The Yolov5 model

    Returns:
        The time it took to process the batch.
    """
    start_time = time.time()
    predictions = model.predict_batch(batch)
    end_time = time.time()
    delta = end_time - start_time
    return (predictions, delta)


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def process_video(
    video_path: str,
    weights_path: str,
    device: str,
    batch_size: int,
    max_batches_to_queue: int,
    output_path: Optional[str],
) -> bool:
    """Runs inference on a video.

    Args:
        video_path: The path to the video to process.
        weights_path: The path to the weights file.
        device: The device to run inference on.
        batch_size: The batch size.
        max_batches_to_queue: The maximum number of batches to queue.

    Returns:
        True if the video was processed successfully, False otherwise.
    """

    try:
        frame_grabber = ThreadedFrameGrabber(
            video_path, batch_size=batch_size, max_batches_to_queue=max_batches_to_queue
        )
    except RuntimeError as err:
        print("Failed to initialize frame grabber", err)
        return False

    try:
        model = BatchYolov5(weights_path=weights_path, device=device)
    except RuntimeError as err:
        print("Failed to initialize model", err)
        return False

    # Wait for the first batch to be ready
    while frame_grabber.batches_in_queue() == 0:
        time.sleep(0.1)

    if output_path is not None:
        vid_cap = frame_grabber.dataset.cap
        video_writer = create_video_writer(
            save_path=output_path,
            fps=vid_cap.get(cv2.CAP_PROP_FPS),
            width=int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    try:
        total_fps = 0.0

        with tqdm(
            total=frame_grabber.total_batch_count(), desc="Processing batches"
        ) as pbar:
            while not frame_grabber.is_done() or not frame_grabber.batch_queue.empty():
                batch = frame_grabber.get_next_batch()
                if batch is None:
                    # This will happen if the batch size is too large or if the disk is too slow.
                    # The grabber can't keep up with the inference speed.
                    print("No batch available, waiting...")
                    # Wait for more batches to be available
                    time.sleep(0.1)
                    continue

                (predictions, delta) = __process_batch(batch, model)

                batch_fps = len(batch) / delta
                total_fps += batch_fps
                pbar.update(1)
                pbar.set_description(f"Processing batches (FPS: {batch_fps:.2f})")

                # Annotate the batch
                if output_path is not None:
                    annotate_batch(
                        vid_writer=video_writer,
                        names=model.names,
                        results=predictions,
                        img0s=batch,
                    )

        print(f"Average FPS: {total_fps / frame_grabber.total_batch_count()}")
    except RuntimeError as err:
        print(err)
        return False
    return True
