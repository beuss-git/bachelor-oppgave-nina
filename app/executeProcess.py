import typing
import re

from PyQt6.QtWidgets import (
    QPlainTextEdit,
    QProgressBar,
    QDialog,
    QVBoxLayout,
    QWidget,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QProcess
from globals import Globals


# A regular expression, to extract the % complete.
progress_re = re.compile("Total complete: (\d+)%")


class ProgressWindow(QDialog):
    def __init__(self, mode: int = Globals.OpenFile) -> None:
        """_summary_

        Args:
            mode (int, optional): _description_. Defaults to OpenFile.
        """

        super().__init__()

        self.p: typing.Optional[QProcess] = None

        self.dialog_layout = QVBoxLayout()

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.dialog_layout.addWidget(self.text)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.dialog_layout.addWidget(self.progress)

        self.setLayout(self.dialog_layout)

    def message(self, s: str) -> None:
        """Print a message to the text box."""
        self.text.appendPlainText(s)

    def start_process(self) -> None:
        """Start the process."""
        if self.p is None:
            self.message("Starting process...")
            self.p = QProcess()
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)
            self.p.start("python", ["app\dummy_script.py"])

    def handle_stderr(self) -> None:
        if self.p is not None:
            data = self.p.readAllStandardError()
            stderr = bytes(data).decode("utf8")
            # Extract progress if it is in the data.
            progress = simple_percent_parser(stderr)
            if progress:
                self.progress.setValue(progress)
            self.message(stderr)

    def handle_stdout(self) -> None:
        if self.p is not None:
            data = self.p.readAllStandardOutput()
            stdout = bytes(data).decode("utf8")
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
        self.p = None


def simple_percent_parser(output: typing.Any) -> typing.Optional[int]:
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    m = progress_re.search(output)
    if m:
        pc_complete = m.group(1)
        return int(pc_complete)
    return None
