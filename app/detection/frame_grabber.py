"""This module contains the ThreadedFrameGrabber class. """


from queue import Queue
from threading import Thread
from typing import List, Any
import math
import time
import numpy as np
from yolov5.utils import dataloaders

# from torch.utils.data.dataloader import DataLoader


class ThreadedFrameGrabber:
    """Continuously grabs frames from a video in batches and puts them into a queue."""

    def __init__(
        self, input_path: str, batch_size: int = 16, max_batches_to_queue: int = 0
    ):
        """Initialize the BatchFrameGrabber.

        Args:
            input_path: The path to the video.
            batch_size: The batch size. Defaults to 16.
            max_batches_in_queue: The maximum number of batches to queue. Defaults to 0.
        """

        try:
            self.dataset = dataloaders.LoadImages(input_path, img_size=640)
        except Exception as err:
            raise RuntimeError(f"Failed to open {input_path}", err) from err

        self.frame_count = self.dataset.frames
        self.image_list: List[Any] = []
        self.batch_queue: Queue[List[Any]] = Queue(max_batches_to_queue)
        self.batch_size = batch_size

        self.thread = Thread(target=self.__run)
        self.thread.start()

        self.done = False

    def __run(self) -> None:
        """
        This function is run in a separate thread and continuously grabs frames from the video.
        """
        for _, _, im0s, _, _ in self.dataset:
            self.image_list.append(im0s)
            if (
                len(self.image_list) >= self.batch_size
                or len(self.image_list) >= self.frame_count
            ):
                self.batch_queue.put(self.image_list)
                self.image_list = []

            # Wait for the queue to have space
            while self.batch_queue.full():
                time.sleep(0.1)
        self.done = True

    def get_next_batch(self) -> List[np.ndarray[Any, Any]] | None:
        """Get the next batch of frames.

        Returns:
            The next batch of frames.
        """
        if not self.batch_queue.empty():
            return self.batch_queue.get()
        return None

    def is_done(self) -> bool:
        """Check if we have processed all frames.

        Returns:
            True if we have processed all frames, False otherwise.
        """
        return self.done

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
        return self.batch_queue.qsize()
