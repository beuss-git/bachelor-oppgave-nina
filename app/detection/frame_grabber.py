# TODO: Add docstrings
# pylint: disable=missing-class-docstring, missing-function-docstring
"""This module contains the ThreadedFrameGrabber class. """

import math
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, PriorityQueue
from threading import Event, Thread
from typing import Any, Generator, List, Optional, Tuple

import cv2
import numpy as np
from torch import Tensor

from app.detection.batch_yolov8 import BatchYolov8
from app.logger import get_logger

logger = get_logger()


@dataclass
class BatchWrapper:
    index: int
    data: Tuple[Tensor, List[np.ndarray[Any, Any]]]

    def __lt__(self, other: "BatchWrapper") -> bool:
        return self.index < other.index


@contextmanager
def threaded_frame_grabber(
    batch_size: int, model: BatchYolov8, video_path: Path, num_workers: int = 4
) -> Generator["ThreadedFrameGrabber", None, None]:
    grabber = ThreadedFrameGrabber(batch_size, model, video_path, num_workers)
    try:
        yield grabber
    finally:
        grabber.close()


class ThreadedFrameGrabber:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        batch_size: int,
        model: BatchYolov8,
        video_path: Path,
        num_workers: int = 4,
    ):
        self.model = model
        self.batch_size = batch_size
        self.capture = cv2.VideoCapture(str(video_path))
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video file {video_path}")

        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        self.unprocessed_batch_queue: PriorityQueue[
            Tuple[int, List[np.ndarray[Any, Any]]]
        ] = PriorityQueue(maxsize=num_workers * 2)
        self.processed_batch_queue: PriorityQueue[
            Optional[BatchWrapper]
        ] = PriorityQueue(maxsize=num_workers * 2)

        self.shutdown_flag = Event()

        self.batch_loader_thread = Thread(target=self.batch_loader)
        self.batch_loader_thread.start()

        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.workers = []

        self.frames_read = 0
        self.skipped_frames = 0

        for _ in range(num_workers):
            future = self.executor.submit(self.worker)
            self.workers.append(future)

    def read_next_frame(self) -> np.ndarray[Any, Any] | None:
        ret: bool
        frame: Optional[np.ndarray[Any, Any]]
        ret, frame = self.capture.read()
        while (
            not ret
            and not self.shutdown_flag.is_set()
            and self.frames_read + self.skipped_frames < self.frame_count
        ):
            self.skipped_frames += 1
            ret, frame = self.capture.read()
        if ret and frame is not None:
            self.frames_read += 1
            return frame
        return None

    def batch_loader(self) -> None:
        batch: List[np.ndarray[Any, Any]] = []
        batch_index = 0
        while not self.shutdown_flag.is_set():
            frame: np.ndarray[Any, Any] | None = self.read_next_frame()
            ret = frame is not None

            if ret and frame is not None:
                batch.append(frame)
                if len(batch) == self.batch_size:
                    self.unprocessed_batch_queue.put((batch_index, batch))
                    batch_index += 1
                    batch = []
            else:
                if len(batch) > 0:
                    self.unprocessed_batch_queue.put((batch_index, batch))
                break
        print("Finished loading batches")

    def worker(self) -> None:
        while not self.shutdown_flag.is_set():
            try:
                batch_index, batch = self.unprocessed_batch_queue.get(timeout=1)
            except Empty:
                if not self.batch_loader_thread.is_alive():
                    break
                continue

            prepared_batch = self.prepare(batch)
            self.processed_batch_queue.put(BatchWrapper(batch_index, prepared_batch))

    def prepare(
        self, batch: List[np.ndarray[Any, Any]]
    ) -> Tuple[Tensor, List[np.ndarray[Any, Any]]]:
        return self.model.prepare_images(batch), batch

    def close(self) -> None:
        self.shutdown_flag.set()
        print("Set shutdown flag")
        self.batch_loader_thread.join()
        print("Joined batch loader thread")
        self.executor.shutdown(wait=False)
        print("Shutdown executor")

    def total_batch_count(self) -> int:
        return int(
            math.ceil((self.frame_count - self.skipped_frames) / self.batch_size)
        )
