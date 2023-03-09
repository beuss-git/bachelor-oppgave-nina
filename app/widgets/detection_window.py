"""Detection window widget."""
import io
import os
from contextlib import redirect_stdout
from pathlib import Path
from typing import List, Tuple

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.data_manager.data_manager import DataManager
from app.detection import detection
from app.detection.batch_yolov8 import BatchYolov8
from app.report_manager.report_manager import ReportManager
from app.video_processor import video_processor


class DetectionWorker(QThread):
    """Detection worker thread."""

    update_progress = pyqtSignal(int)
    add_log = pyqtSignal(str)
    input_folder_path: Path | None = None
    output_folder_path: Path | None = None
    model: BatchYolov8 | None = None

    def __init__(self, folder_path: Path, output_folder_path: Path) -> None:
        super().__init__()

        self.input_folder_path = folder_path
        self.output_folder_path = output_folder_path
        self.data_manager: DataManager
        self.report_manager: ReportManager

    def run(self) -> None:
        """Run the detection."""
        self.data_manager = DataManager()

        if self.model is None:
            self.log("Initializing the model...")
            self.model = BatchYolov8(
                Path(r"C:\Users\lilli\Downloads\yolov8n.pt"),
                "cuda:0",
            )
        stream_target = io.StringIO()
        with redirect_stdout(stream_target):
            self.process_folder()
        # self.log(stream_target.getvalue())

        self.data_manager.close_connection()

    def log(self, text: str) -> None:
        """Log text to the console."""
        self.add_log.emit(text)

    def process_folder(self) -> None:
        """Process a folder of videos."""
        if self.input_folder_path is None:
            return
        videos = [
            filename
            for filename in os.listdir(self.input_folder_path)
            if filename.endswith(".mp4")
        ]

        for i, video in enumerate(videos):
            self.log(f"Processing {i + 1}/{len(videos)} ({video})")
            self.data_manager.add_video_data(self.input_folder_path / video, video)
            self.process_video(self.input_folder_path / video)

    def process_video(self, video_path: Path) -> None:
        """
        Process a video and save the processed video to the same folder as the original video.
        """
        if self.model is None or self.output_folder_path is None:
            return

        # self.add_text.emit(f"Processing {video_path}")

        frames_with_fish = detection.process_video(
            model=self.model,
            video_path=video_path,
            batch_size=16,
            max_batches_to_queue=4,
            output_path=None,
            notify_progress=lambda progress: self.update_progress.emit(int(progress)),
        )

        print(f"Found {len(frames_with_fish)} frames with fish")

        self.add_log.emit(f"Found {len(frames_with_fish)} frames with fish")

        # Convert the detected frames to frame ranges to cut the video
        frame_ranges = self.__detected_frames_to_range(frames_with_fish, frame_buffer=3)
        print(f"Found {len(frame_ranges)} frame ranges with fish")
        self.add_log.emit(f"Found {len(frame_ranges)} frame ranges with fish")

        if len(frame_ranges) == 0:
            print("No fish detected, skipping video")
            return

        vid_path = Path(video_path)
        out_path = self.output_folder_path / f"{vid_path.stem}_processed.mp4"

        # Cut the video to the detected frames
        video_processor.cut_video(video_path, out_path, frame_ranges)
        self.log(f"Saved processed video to {out_path}")

        self.update_progress.emit(100)
        self.data_manager.add_detection_data(video_path, frame_ranges)

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


class DetectionWindow(QDialog):  # pylint: disable=too-few-public-methods
    """Detection window widget."""

    def __init__(
        self,
        input_folder_path: Path,
        output_folder_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.dialog_layout = QVBoxLayout()

        # Add the main output textbox.
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setSizeAdjustPolicy(
            QPlainTextEdit.SizeAdjustPolicy.AdjustToContents
        )
        self.dialog_layout.addWidget(self.output)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setMinimumSize(600, 300)

        # Add the progress bar.
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.dialog_layout.addWidget(self.progress_bar)

        self.setLayout(self.dialog_layout)

        self.worker = DetectionWorker(input_folder_path, output_folder_path)
        self.worker.update_progress.connect(self.progress_bar.setValue)
        self.worker.add_log.connect(self.output.appendPlainText)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

        # Stop worker when window is closed
        self.finished.connect(self.worker.terminate)

        self.close_button = QPushButton("Close")

        # This is needed because self.close returns a bool
        def on_close() -> None:
            self.close()

        self.close_button.clicked.connect(on_close)
        self.dialog_layout.addWidget(self.close_button)
        self.close_button.hide()

    def worker_finished(self) -> None:
        """Called when the worker has finished."""
        # Show button to close window now that the worker has finished
        self.close_button.show()
