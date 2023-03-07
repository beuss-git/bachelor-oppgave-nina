"""This module contains the ThreadedFrameGrabber class. """


from queue import Queue
from typing import List, Any, Tuple
import math
import threading
from pathlib import Path
import cv2
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
        self.batch_queue: Queue[List[Any]] = Queue(max_batches_to_queue)
        self.original_batch_queue: Queue[List[Any]] = Queue(max_batches_to_queue)
        self.processed_batch_queue: Queue[Tensor] = Queue(max_batches_to_queue)
        self.thread_pool = []
        for _ in range(4):  # create 4 threads to process batches
            thread = threading.Thread(target=self.__prepare_images_thread)
            thread.daemon = True
            self.thread_pool.append(thread)
            thread.start()

        self.capture = cv2.VideoCapture(str(video_path))
        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        # Start the capture thread
        self.capture_thread = threading.Thread(target=self.__capture_images_thread)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def __prepare_images_thread(self) -> None:
        """Thread to prepare images for the model and put them in the processed queue."""
        while True:
            batch = self.batch_queue.get()
            self.original_batch_queue.put(batch)
            processed_batch = self.model.prepare_images(batch)
            self.processed_batch_queue.put(processed_batch)
            self.batch_queue.task_done()  # Mark the batch as done

    def __capture_images_thread(self) -> None:
        """Thread to capture frames from the video and put them in the queue."""
        while True:
            frames = []
            for _ in range(self.batch_size):
                ret, frame = self.capture.read()
                if not ret:
                    break
                frames.append(frame)
            if not frames:
                break
            self.batch_queue.put(frames)
        self.batch_queue.join()

    def get_batch(self) -> Tuple[Tensor, List[Any]]:
        """Gets the processed batch and the original batch images.

        Returns:
           The processed batch and the original batch images.
        """
        return self.processed_batch_queue.get(), self.original_batch_queue.get()

    def has_more_processed_batches(self) -> bool:
        """Check if there are more processed batches.

        Returns:
           True if there are more processed batches, False otherwise.
        """
        return not self.processed_batch_queue.empty()

    def is_done(self) -> bool:
        """Check if we have processed all frames.

        Returns:
           True if we have processed all frames, False otherwise.
        """
        return not self.capture_thread.is_alive() and self.batch_queue.empty()

    def total_batch_count(self) -> int:
        """Get the total number of batches that will be processed.

        Returns:
            The total number of batches.
        """
        return int(math.ceil(self.frame_count / self.batch_size))

    def batches_in_queue(self) -> int:
        """Get the number of batches in the queue.

        Returns:
           The number of batches in the queue.
        """
        return self.processed_batch_queue.qsize()
