"""This module contains the ThreadedFrameGrabber class. """


import math
import multiprocessing as mp
from pathlib import Path
from typing import Any, List, Tuple

import cv2
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
        max_batches_to_queue: int,
        model: BatchYolov8,
        video_path: Path,
    ):
        self.model = model
        self.batch_size = batch_size

        self.capture = cv2.VideoCapture(str(video_path))
        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        self.pool = mp.pool.ThreadPool()
        self.queue = self.pool.map_async(self.prepare, self.load())

    def load(self):
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

    def prepare(self, batch):
        return self.model.prepare_images(batch), batch

    def close(self) -> None:
        self.pool.close()
        # Release any occupied memory
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def get_batches(self, timeout=10) -> Tuple[Tensor, List[Any]]:
        """Gets the processed batches and the original batches images.

        Yield:
           The processed batch and the original batch images.
        """
        try:
            for processed, original in self.queue.get(timeout):
                yield processed, original
        except mp.TimeoutError:
            yield None

    def total_batch_count(self) -> int:
        """Get the total number of batches that will be processed.

        Returns:
            The total number of batches.
        """
        return int(math.ceil(self.frame_count / self.batch_size))
