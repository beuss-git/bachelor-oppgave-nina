"""Detection window widget."""
import io
import os
import sys
import threading
import time
from contextlib import redirect_stdout
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import torch
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import settings
from app.common import Common
from app.data_manager.data_manager import DataManager
from app.detection import detection
from app.detection.batch_yolov8 import BatchYolov8
from app.report_manager.report_manager import ReportManager
from app.video_processor import Detection, video_processor

# TODO: test all these file types
ALLOWED_EXTENSIONS = (".mp4", ".m4a", ".avi", ".mkv", ".mov", ".wmv")


class DetectionWorker(QThread):
    """Detection worker thread."""

    update_task_progress = pyqtSignal(int)
    update_task_format = pyqtSignal(str)
    update_overall_progress = pyqtSignal(int)
    set_video_count = pyqtSignal(int)
    update_time_prediction_sig = pyqtSignal(str)

    add_log = pyqtSignal(str)

    input_folder_path: Path
    output_folder_path: Path
    model: BatchYolov8 | None

    def __init__(self, folder_path: Path, output_folder_path: Path) -> None:
        super().__init__()

        self.input_folder_path = folder_path
        self.output_folder_path = output_folder_path
        self.model = None
        self.stop_event = threading.Event()
        self.start_time = time.time()
        self.video_start_time = 0.0
        self.last_time_update = 0.0

    def stop(self) -> None:
        """Stop worker from processing more videos."""
        self.log("Stopping...")
        self.stop_event.set()

    def run(self) -> None:
        """Run the detection."""

        if self.model is None:
            self.log(f"Initializing the model using {settings.weights}...")
            self.model = BatchYolov8(
                Common.weights_folder / settings.weights,
                "cuda:0",
            )
        stream_target = io.StringIO()
        with redirect_stdout(stream_target):
            self.process_folder()
        # self.log(stream_target.getvalue())

    def log(self, text: str) -> None:
        """Log text to the console."""
        self.add_log.emit(text)

    def process_folder(self) -> None:
        """Process a folder of videos."""
        if self.input_folder_path is None:
            return

        with DataManager() as data_manager:
            report_manager = ReportManager(
                self.output_folder_path,
                data_manager,
            )

            try:
                report_manager.check_can_write_report()
            except PermissionError:
                self.log("Please close the report file.")
                return

            videos = [
                filename
                for filename in os.listdir(self.input_folder_path)
                if filename.lower().endswith(ALLOWED_EXTENSIONS)
            ]

            if len(videos) == 0:
                self.log("No videos found in the input folder")
                return

            self.set_video_count.emit(len(videos))
            self.update_overall_progress.emit(0)

            for i, video in enumerate(videos):
                self.log(f"Processing {i + 1}/{len(videos)} ({video})")
                video_path = self.input_folder_path / video
                if not self.process_video(i, len(videos), video_path, data_manager):
                    break
                data_manager.add_video_data(video_path, video, self.output_folder_path)

                # Delete the original video if the user has selected to do so
                if not settings.keep_original:
                    video_path.unlink()

                self.update_overall_progress.emit(i + 1)

            if settings.get_report:
                try:
                    report_manager.write_report(videos)
                except PermissionError:
                    self.log("Could not write report. Please close the report file.")

    def tensors_to_predictions(
        self, tensors: List[torch.Tensor]
    ) -> Dict[int, List[Detection]]:
        """Convert the tensors to a dictionary of frame number to detections."""
        detections: Dict[int, List[Detection]] = {}
        for frame, tensor in enumerate(tensors):
            # annotator.text((32, 32), text, txt_color=(0, 255, 255))
            detections[frame] = []
            for pred in tensor:
                bndbox = pred["bndbox"]
                detections[frame].append(
                    Detection(
                        label=str(pred["name"]),
                        confidence=float(pred["conf"]),
                        xmin=int(bndbox["xmin"]),
                        ymin=int(bndbox["ymin"]),
                        xmax=int(bndbox["xmax"]),
                        ymax=int(bndbox["ymax"]),
                    )
                )
        return detections

    def __add_buffer_to_ranges(
        self, frame_ranges: List[Tuple[int, int]], video_path: Path
    ) -> List[Tuple[int, int]]:
        """Add buffer time before and after each frame range and merge overlapping ranges"""

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Add buffer time to each frame range
        frame_ranges_with_buffer = [
            (
                max(0, start_frame - int(fps * settings.buffer_before)),
                min(video_length, end_frame + int(fps * settings.buffer_after)),
            )
            for (start_frame, end_frame) in frame_ranges
        ]

        # Merge overlapping frame ranges
        merged_ranges: List[Tuple[int, int]] = []
        for start_frame, end_frame in frame_ranges_with_buffer:
            if not merged_ranges or start_frame > merged_ranges[-1][1]:
                merged_ranges.append((start_frame, end_frame))
            else:
                merged_ranges[-1] = (
                    merged_ranges[-1][0],
                    max(merged_ranges[-1][1], end_frame),
                )

        return merged_ranges

    def get_fps(self, video_path: Path) -> float:
        """Get the FPS of a video."""
        cap = cv2.VideoCapture(str(video_path))
        return float(cap.get(cv2.CAP_PROP_FPS))

    def process_video(
        self,
        video_num: int,
        num_videos: int,
        video_path: Path,
        data_manager: DataManager,
    ) -> bool:
        """
        Process a video and save the processed video to the same folder as the original video.

        Returns True if we should continue processing videos, False if we should stop.
        """
        if self.model is None or self.output_folder_path is None:
            self.log("Model or output folder path is None")
            return False

        # self.add_text.emit(f"Processing {video_path}")

        # Update threshold
        self.model.conf_thres = settings.prediction_threshold / 100

        self.update_task_progress.emit(0)
        self.update_task_format.emit("Performing detection: %p%")

        self.video_start_time = time.time()

        def detection_notify_progress(progress: int) -> None:
            self.update_task_progress.emit(progress)
            self.update_time_prediction(int(progress / 2), video_num, num_videos)

        frames_with_fish, tensors = detection.process_video(
            model=self.model,
            video_path=video_path,
            batch_size=settings.batch_size,
            max_batches_to_queue=4,
            output_path=None,
            stop_event=self.stop_event,
            notify_progress=detection_notify_progress,
        )

        # If the stop event is set, stop processing and return
        if self.stop_event.is_set():
            return False

        print(f"Found {len(frames_with_fish)} frames with fish")

        self.add_log.emit(f"Found {len(frames_with_fish)} frames with fish")

        # Convert the detected frames to frame ranges to cut the video
        frame_ranges = detection.detected_frames_to_ranges(
            frames_with_fish,
            frame_buffer=int(self.get_fps(video_path) * settings.frame_buffer_seconds),
        )
        print(f"Found {len(frame_ranges)} frame ranges with fish")
        self.add_log.emit(f"Found {len(frame_ranges)} frame ranges with fish")

        frame_ranges = self.__add_buffer_to_ranges(frame_ranges, video_path)

        if len(frame_ranges) == 0:
            print("No fish detected, skipping video")
            return True

        vid_path = Path(video_path)
        out_path = self.output_folder_path / f"{vid_path.stem}_processed.mp4"

        dets = None
        if settings.box_around_fish:
            dets = self.tensors_to_predictions(tensors)

        self.update_task_progress.emit(0)
        self.update_task_format.emit("Cutting video: %p%")

        def cut_notify_progress(progress: int) -> None:
            self.update_task_progress.emit(progress)
            self.update_time_prediction(int(progress / 2) + 50, video_num, num_videos)

        # Cut the video to the detected frames
        # TODO: implement the stop event for this function too
        video_processor.cut_video(
            video_path,
            out_path,
            frame_ranges,
            dets,
            notify_progress=cut_notify_progress,
        )
        # Just show percentage at this point
        self.update_task_format.emit("%p%")

        self.log(f"Saved processed video to {out_path}")

        # It will get set to 100 in cut_video, but we aren't actually done
        self.update_task_progress.emit(99)
        data_manager.add_detection_data(video_path, frame_ranges)
        self.update_task_progress.emit(100)

        return True

    def update_time_prediction(
        self, progress: int, video_num: int, num_videos: int
    ) -> None:
        """Update the time prediction label.

        Args:
            progress: The progress of the current task.
            video_num: The number of the current video.
            num_videos: The total number of videos.
        """
        current_time = time.time()
        # Don't update more than once per second
        if current_time - self.last_time_update < 1.0:
            return
        self.last_time_update = current_time

        total_elapsed_time = current_time - self.start_time
        video_elapsed_time = current_time - self.video_start_time

        if progress > 0:
            # Calculate the remaining time for the current video
            time_left_current_video = video_elapsed_time * (100 - progress) / progress

            if video_num > 0:
                # Calculate the average time spent per video for the videos processed so far
                avg_time_per_video = (
                    total_elapsed_time - video_elapsed_time
                ) / video_num

                # Estimate the time left for the remaining videos
                time_left_remaining_videos = avg_time_per_video * (
                    num_videos - (video_num + 1)
                )
            else:
                # If this is the first video, estimate the total time for the current video
                total_time_current_video = video_elapsed_time * 100 / progress

                # Use the total time for the current video as an estimate for the remaining videos
                time_left_remaining_videos = total_time_current_video * (num_videos - 1)

            # Calculate the total time left
            time_left = time_left_current_video + time_left_remaining_videos

            time_left_str = str(timedelta(seconds=int(time_left)))
            self.update_time_prediction_sig.emit(f"Total Time Left: {time_left_str}")


class DetectionWindow(
    QDialog
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Detection window widget."""

    def __init__(
        self,
        input_folder_path: Path,
        output_folder_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Detection Progress")

        self.dialog_layout = QVBoxLayout()

        self.__add_time_prediction_label()

        # Add the main output textbox.
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setSizeAdjustPolicy(
            QPlainTextEdit.SizeAdjustPolicy.AdjustToContents
        )
        self.dialog_layout.addWidget(self.output)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setMinimumSize(600, 300)

        # Create the label and set its text.
        self.task_progress_label = QLabel("Task Progress:")
        # Add the label to the layout.
        self.dialog_layout.addWidget(self.task_progress_label)
        # Create the progress bar.
        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setRange(0, 100)
        # Add the progress bar to the layout.
        self.dialog_layout.addWidget(self.task_progress_bar)

        # Create the label and set its text.
        label = QLabel("Overall Progress:")
        # Add the label to the layout.
        self.dialog_layout.addWidget(label)
        # Create the overall progress bar.
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        # Set the format
        self.overall_progress_bar.setFormat("%v / %m")
        # Add the overall progress bar to the layout.
        self.dialog_layout.addWidget(self.overall_progress_bar)

        self.setLayout(self.dialog_layout)

        self.worker = DetectionWorker(input_folder_path, output_folder_path)
        # Connect the signals to the worker.
        self.worker.update_task_progress.connect(self.task_progress_bar.setValue)
        self.worker.update_task_format.connect(self.task_progress_bar.setFormat)
        self.worker.update_overall_progress.connect(self.overall_progress_bar.setValue)
        self.worker.update_time_prediction_sig.connect(
            self.update_time_prediction_label
        )
        self.worker.set_video_count.connect(
            lambda count: self.overall_progress_bar.setRange(0, count)
        )

        self.worker.add_log.connect(self.output.appendPlainText)

        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

        self.__add_stop_button()

        # Hacky fix for disabling the output directory button on the VDI
        if sys.platform != "linux":
            self.__add_open_output_dir_button(output_folder_path)

        self.__add_close_button()

    def update_time_prediction_label(self, text: str) -> None:
        """Update the time prediction label with the given text."""
        self.time_prediction_label.setText(text)

    def __add_time_prediction_label(self) -> None:
        """Add the time prediction label to the layout."""
        self.time_prediction_label = QLabel("Total Time Left: N/A")
        self.dialog_layout.addWidget(self.time_prediction_label)

    def __add_stop_button(self) -> None:
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.__stop_button_clicked)
        self.dialog_layout.addWidget(self.stop_button)

    def __add_open_output_dir_button(self, output_folder_path: Path) -> None:
        self.open_output_dir_button = QPushButton("Open output directory")
        self.open_output_dir_button.hide()

        def on_open_output_dir() -> None:
            if sys.platform == "win32":
                os.startfile(str(output_folder_path))  # pylint: disable=no-member
            elif sys.platform == "linux":
                os.system(f"xdg-open '{output_folder_path}'")
            else:
                raise OSError("Unsupported operating system")

        self.open_output_dir_button.clicked.connect(on_open_output_dir)

        self.dialog_layout.addWidget(self.open_output_dir_button)

    def __add_close_button(self) -> None:
        self.close_button = QPushButton("Close")
        self.close_button.hide()

        # This is needed because self.close returns a bool
        def on_close() -> None:
            self.close()

        self.close_button.clicked.connect(on_close)
        self.dialog_layout.addWidget(self.close_button)

    def __stop_button_clicked(self) -> None:
        """Called when the stop button is clicked."""
        self.worker.stop()
        self.stop_button.setEnabled(False)

    def worker_finished(self) -> None:
        """Called when the worker has finished."""
        # Show button to close window now that the worker has finished
        self.open_output_dir_button.show()
        self.close_button.show()
        self.stop_button.hide()

        # Hide the task progress bar and label
        self.task_progress_bar.hide()
        self.task_progress_label.hide()

        # Set the overall progress bar to finished
        if self.worker.stop_event.is_set():
            self.overall_progress_bar.setFormat("Stopped")
        else:
            self.overall_progress_bar.setFormat("Finished")
        self.update_time_prediction_label("Time left: N/A")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pylint: disable=C0103
        """Called when the window is closed."""
        # Stop the worker when the window is closed
        self.worker.stop()
        event.accept()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # pylint: disable=C0103
        """We use this to ignore the escape key, so that the window can't be closed by accident."""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)
