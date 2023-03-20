"""This module contains the ThreadedFrameGrabber class. """


import math
import multiprocessing as mp
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple

import cv2
import numpy as np
import torch
from torch import Tensor

from app.detection.batch_yolov8 import BatchYolov8
from app.logger import get_logger

logger = get_logger()


class ThreadedFrameGrabber:  # pylint: disable=too-many-instance-attributes
    """A class to grab frames from a video in a separate thread."""

    def __init__(
        self,
        batch_size: int,
        model: BatchYolov8,
        video_path: Path,
    ):
        """
        Initializes the ThreadedFrameGrabber.

        Args:
            batch_size: The number of frames per batch.
            model: The BatchYolov8 object for processing images.
            video_path: The path to the input video file.
        """
        self.model = model
        self.batch_size = batch_size

        self.capture = cv2.VideoCapture(str(video_path))
        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        self.pool = mp.pool.ThreadPool()
        self.queue = self.pool.map_async(self.prepare, self.load())

    def load(self) -> Generator[List[np.ndarray[Any, Any]], None, None]:
        """
        Loads frames from the video file in batches.

        Yields:
            A batch of frames as numpy arrays.
        """
        while True:
            batch = []
            for _ in range(self.batch_size):
                ret, frame = self.capture.read()
                if ret:
                    batch.append(frame)
                else:
                    break
            if not batch:
                break
            yield batch

    def prepare(
        self, batch: List[np.ndarray[Any, Any]]
    ) -> Tuple[Tensor, List[np.ndarray[Any, Any]]]:
        """
        Prepares a batch of images using the model.

        Args:
            batch: A list of images as numpy arrays.

        Returns:
            A tuple containing the processed images as tensors
            and the original images as numpy arrays.
        """
        return self.model.prepare_images(batch), batch

    def close(self) -> None:
        """
        Closes the thread pool and releases GPU memory.
        """
        self.pool.close()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    def __enter__(self) -> "ThreadedFrameGrabber":
        """
        Enters the context manager.

        Returns:
            The current instance of the ThreadedFrameGrabber.
        """
        return self

    def __exit__(
        self, kind: Optional[Any], value: Optional[Any], traceback: Optional[Any]
    ) -> None:
        """
        Exits the context manager and cleans up resources.

        Args:
            kind: The type of exception, if any.
            value: The instance of the exception, if any.
            traceback: A traceback object encapsulating the call stack, if any.
        """
        self.close()

    def get_batches(
        self, timeout: int = 10
    ) -> Generator[Optional[Tuple[Tensor, List[np.ndarray[Any, Any]]]], None, None]:
        """
        Gets the processed batches and the original batches images.

        Args:
            timeout: The timeout in seconds for fetching the batches.

        Yields:
            The processed batch and the original batch images.
        """
        try:
            for processed, original in self.queue.get(timeout):
                yield processed, original
        except mp.TimeoutError:
            yield None

    def total_batch_count(self) -> int:
        """
        Get the total number of batches that will be processed.

        Returns:
            The total number of batches.
        """
        return int(math.ceil(self.frame_count / self.batch_size))
