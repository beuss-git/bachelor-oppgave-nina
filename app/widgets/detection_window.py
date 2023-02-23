"""Detection window widget."""
import os
from typing import List, Tuple

from pathlib import Path
from contextlib import redirect_stdout
import io
from PyQt6.QtWidgets import (
    QPlainTextEdit,
    QProgressBar,
    QDialog,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QPushButton,
)
from PyQt6.QtCore import pyqtSignal, QThread
from app.detection.batch_yolov5 import BatchYolov5
from app.globals import Globals
from app.detection import detection
from app.video_processor import video_processor


class DetectionWorker(QThread):
    """Detection worker thread."""

    progress_changed = pyqtSignal(int)
    add_text = pyqtSignal(str)
    input_folder_path: Path | None = None
    output_folder_path: Path | None = None

    def __init__(self, folder_path: Path, output_folder_path: Path) -> None:
        super().__init__()

        self.input_folder_path = folder_path
        self.output_folder_path = output_folder_path

    def run(self) -> None:
        """Run the detection."""
        if Globals.model is None:
            self.log("Initializing the model...")
            Globals.model = BatchYolov5(
                "C:\\Users\\benja\\Downloads\\yolov5s-imgsize-640.pt", "cuda:0"
            )
        stream_target = io.StringIO()
        with redirect_stdout(stream_target):
            self.process_folder()
        # self.log(stream_target.getvalue())

    def log(self, text: str) -> None:
        """Log text to the console."""
        self.add_text.emit(text)

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
            self.process_video(os.path.join(self.input_folder_path, video))

    def process_video(self, video_path: str) -> None:
        """
        Process a video and save the processed video to the same folder as the original video.
        """
        if Globals.model is None or self.output_folder_path is None:
            return

        # self.add_text.emit(f"Processing {video_path}")

        frames_with_fish = detection.process_video(
            model=Globals.model,
            video_path=video_path,
            batch_size=64,
            max_batches_to_queue=4,
            output_path=None,
            notify_progress=lambda progress: self.progress_changed.emit(int(progress)),
        )

        print(f"Found {len(frames_with_fish)} frames with fish")

        self.add_text.emit(f"Found {len(frames_with_fish)} frames with fish")

        # Convert the detected frames to frame ranges to cut the video
        frame_ranges = self.__detected_frames_to_range(frames_with_fish, frame_buffer=3)
        print(f"Found {len(frame_ranges)} frame ranges with fish")
        self.add_text.emit(f"Found {len(frame_ranges)} frame ranges with fish")

        if len(frame_ranges) == 0:
            print("No fish detected, skipping video")
            return

        vid_path = Path(video_path)
        out_path = self.output_folder_path / f"{vid_path.stem}_processed.mp4"

        # Cut the video to the detected frames
        video_processor.cut_video(video_path, str(out_path), frame_ranges)
        self.log(f"Saved processed video to {out_path}")

        self.progress_changed.emit(100)

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


class DetectionWindow(QDialog):
    """Detection window widget."""

    def __init__(
        self,
        input_folder_path: str,
        output_folder_path: str,
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

        self.worker = DetectionWorker(Path(input_folder_path), Path(output_folder_path))
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.add_text.connect(self.output.appendPlainText)
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
        # Add button to close window
        self.close_button.show()
