"""Progress bar when loading AI models."""
import typing
import re

from PyQt6.QtWidgets import (
    QPlainTextEdit,
    QProgressBar,
    QDialog,
    QVBoxLayout,
)
from PyQt6.QtCore import QProcess
from .globals import Globals


# A regular expression, to extract the % complete.
progress_re = re.compile(r"Total complete: (\d+)%")


class ProgressWindow(QDialog):
    """Progress window."""

    def __init__(self, _: int = Globals.OpenFile) -> None:
        """_summary_

        Args:
            mode (int, optional): _description_. Defaults to OpenFile.
        """

        super().__init__()

        self.dialog_layout = QVBoxLayout()

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.dialog_layout.addWidget(self.text)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.dialog_layout.addWidget(self.progress)

        self.setLayout(self.dialog_layout)

        self.start_process()

    def message(self, message: str) -> None:
        """Print a message to the text box."""
        self.text.appendPlainText(message)

    def start_process(self) -> None:
        """Start the process."""
        if Globals.Process is None:
            self.message("Starting process...")
            Globals.Process = QProcess()
            Globals.Process.readyReadStandardOutput.connect(self.handle_stdout)
            Globals.Process.readyReadStandardError.connect(self.handle_stderr)
            Globals.Process.stateChanged.connect(self.handle_state)
            Globals.Process.finished.connect(self.process_finished)
            Globals.Process.start("python", [Globals.ProcessPath])

    def handle_stderr(self) -> None:
        """_summary_"""
        if Globals.Process is not None:
            data = Globals.Process.readAllStandardError()
            stderr = data.data().decode("utf8")
            # Extract progress if it is in the data.
            progress = simple_percent_parser(stderr)
            if progress:
                self.progress.setValue(progress)
            self.message(stderr)

    def handle_stdout(self) -> None:
        """_summary_"""
        if Globals.Process is not None:
            data = Globals.Process.readAllStandardOutput()
            stdout = data.data().decode("utf8")
            self.message(stdout)

    def handle_state(self, state: typing.Any) -> None:
        """_summary_

        Args:
            state (Any): _description_
        """
        states = {
            QProcess.ProcessState.NotRunning: "Not running",
            QProcess.ProcessState.Starting: "Starting",
            QProcess.ProcessState.Running: "Running",
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def process_finished(self) -> None:
        """Process finished."""
        self.message("Process finished.")
        Globals.Process = None


def simple_percent_parser(output: typing.Any) -> typing.Optional[int]:
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    match = progress_re.search(output)
    if match:
        pc_complete = match.group(1)
        return int(pc_complete)
    return None
