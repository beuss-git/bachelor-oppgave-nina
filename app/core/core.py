"""Core module for the application."""

import os
import logging
from typing import List, Tuple

from pathlib import Path
from app.detection.batch_yolov8 import BatchYolov8
from ..detection import detection
from ..video_processor import video_processor

logger = logging.getLogger(__name__)


class Core:
    """
    The core class for the application.
    This class is responsible for processing folders of videos.
    It also manages the active model used for video processing.
    In the future it will also handle report generation and management (through a different module)
    """

    def __init__(self, weights_path: str, device: str):
        try:
            self._model = BatchYolov8(weights_path=weights_path, device=device)
        except RuntimeError as err:
            logger.error("Failed to initialize model", exc_info=err)
            raise RuntimeError("Failed to initialize model", err) from err

        self._batch_size = 64
        self._max_batches_to_queue = 4

    def process_folder(self, folder_path: str) -> None:
        """Process a folder of videos."""
        for filename in os.listdir(folder_path):
            if filename.endswith(".mp4"):
                print(f"Processing {filename}")
                self.process_video(os.path.join(folder_path, filename))

    def process_video(self, video_path: str) -> None:
        """
        Process a video and save the processed video to the same folder as the original video.
        """

        frames_with_fish = detection.process_video(
            model=self._model,
            video_path=video_path,
            batch_size=self._batch_size,
            max_batches_to_queue=self._max_batches_to_queue,
            output_path=None,
        )
        print(f"Found {len(frames_with_fish)} frames with fish")

        # Convert the detected frames to frame ranges to cut the video
        frame_ranges = self.__detected_frames_to_range(frames_with_fish, frame_buffer=3)
        print(f"Found {len(frame_ranges)} frame ranges with fish")

        if len(frame_ranges) == 0:
            print("No fish detected, skipping video")
            return

        vid_path = Path(video_path)
        out_path = vid_path.parent / f"{vid_path.stem}_processed.mp4"
        print(f"Cutting video to {out_path}")
        # Cut the video to the detected frames
        video_processor.cut_video(video_path, str(out_path), frame_ranges)

    def __detected_frames_to_range(
        self, frames: List[int], frame_buffer: int
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
