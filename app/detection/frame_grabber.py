"""This module contains the ThreadedFrameGrabber class. """

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import cpu_count
from pathlib import Path
from queue import Empty, PriorityQueue
from threading import Event, Thread
from types import TracebackType
from typing import Any, List, Optional, Tuple, Type

import cv2
import numpy as np
import torch
from torch import Tensor

from app.detection.batch_yolov8 import BatchYolov8
from app.logger import get_logger

logger = get_logger()


@dataclass
class BatchWrapper:
    """Wrapper for a batch of images."""

    index: int
    data: Tuple[Tensor, List[np.ndarray[Any, Any]]]

    def __lt__(self, other: "BatchWrapper") -> bool:
        """Less than operator for sorting batches."""
        return self.index < other.index


@dataclass
class ThreadedFrameGrabber:  # pylint: disable=too-many-instance-attributes
    """Class for grabbing frames from a video file in a separate thread, preprocessing them,
    and returning them in batches for use in an object detection model"""

    batch_size: int
    model: BatchYolov8
    video_path: Path
    batch_counter: int = 0
    num_workers: int = field(init=False)
    capture: cv2.VideoCapture = field(init=False)
    frame_count: int = field(init=False)
    unprocessed_batch_queue: PriorityQueue[
        Tuple[int, List[np.ndarray[Any, Any]]]
    ] = field(init=False)
    processed_batch_queue: PriorityQueue[Optional[BatchWrapper]] = field(init=False)
    shutdown_flag: Event = field(init=False)
    batch_loader_thread: Thread = field(init=False)
    executor: ThreadPoolExecutor = field(init=False)
    workers: List[Any] = field(init=False)
    frames_read: int = field(default=0)
    skipped_frames: int = field(default=0)

    def __enter__(self) -> "ThreadedFrameGrabber":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],  # pylint: disable=unused-argument
        exc_value: Optional[BaseException],  # pylint: disable=unused-argument
        traceback: Optional[TracebackType],  # pylint: disable=unused-argument
    ) -> None:
        self.close()

    def __post_init__(self) -> None:
        self.capture = cv2.VideoCapture(str(self.video_path))
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video file {self.video_path}")

        self.num_workers = int(cpu_count() / 2)

        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        self.unprocessed_batch_queue = PriorityQueue(maxsize=self.num_workers * 2)
        self.processed_batch_queue = PriorityQueue(maxsize=self.num_workers * 2)

        self.shutdown_flag = Event()

        self.batch_loader_thread = Thread(target=self.batch_loader)
        self.batch_loader_thread.start()

        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        self.workers = []

        for _ in range(self.num_workers):
            future = self.executor.submit(self.worker)
            self.workers.append(future)

    def read_next_frame(self) -> np.ndarray[Any, Any] | None:
        """Reads the next frame from the video file"""
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
        """Loadds batches of frames into the unprocessed batch queue"""
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

        logger.debug("Finished loading batches")

    def worker(self) -> None:
        """Processes batches of frames and puts them into the processed batch queue"""
        while not self.shutdown_flag.is_set():
            try:
                batch_index, batch = self.unprocessed_batch_queue.get(timeout=1)
            except Empty:
                if not self.batch_loader_thread.is_alive():
                    break
                continue

            self.processed_batch_queue.put(
                BatchWrapper(batch_index, (self.model.prepare_images(batch), batch))
            )

    def close(self) -> None:
        """Closes the video capture and shuts down the batch loader thread and workers"""
        self.shutdown_flag.set()
        logger.debug("Set shutdown flag")
        self.batch_loader_thread.join()
        logger.debug("Joined batch loader thread")
        self.executor.shutdown(wait=False)
        logger.debug("Shutdown executor")
        self.capture.release()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    def total_batch_count(self) -> int:
        """Returns the total number of batches that will be returned by this object."""
        return int(
            math.ceil((self.frame_count - self.skipped_frames) / self.batch_size)
        )

    def get_batch(self) -> Tuple[Tensor, List[np.ndarray[Any, Any]]] | None:
        """Returns the next batch of frames from the video file"""
        try:
            batch_wrapper = self.processed_batch_queue.get(timeout=5)
        except Empty:
            return None
        if batch_wrapper is None:
            return None

        self.batch_counter += 1
        return batch_wrapper.data

    def is_done(self) -> bool:
        """Returns true if all batches have been returned"""
        return self.batch_counter >= self.total_batch_count()
