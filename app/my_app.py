<<<<<<< HEAD:app/myApp.py
# Only needed for access to command line arguments
import sys
import typing

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QFileDialog,
    QPushButton,
    QLabel,
    QWidget,
    QLineEdit,
    QHBoxLayout,
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
    QProgressBar,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QProcess
import re
import qdarktheme

# A regular expression, to extract the % complete.
progress_re = re.compile("Total complete: (\d+)%")


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


class MainWindow(QMainWindow):
    """Main Window"""

    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    def __init__(self, mode: int = OpenFile) -> None:
        """_summary_

        Args:
            mode (int, optional): _description_. Defaults to OpenFile.
        """

        super().__init__()

        self.p: typing.Optional[QProcess] = None

        # Set default window settings
        self.window_width, self.window_height = 700, 400
        self.setWindowTitle("Fish detector 3000")
        self.setMinimumSize(self.window_width, self.window_height)
        self.setWindowIcon(QtGui.QIcon("app/images/app_logo.png"))

        self.browser_mode = mode
        self.filter_name = "All files (*)"
        # self.dirpath = QDir.currentPath()

        parent_layout = QVBoxLayout()
        parent_layout.addWidget(self.set_label_title("Folder to Analyse:"))

        file_analyse_layout = self.file_management_widget()

        parent_layout.addLayout(file_analyse_layout)
        parent_layout.addWidget(self.set_label_title("Save to Folder:"))

        file_save_layout = self.file_management_widget()

        parent_layout.addLayout(file_save_layout)

        buffers = QHBoxLayout()

        parent_layout.addLayout(self.buffer_time_widget(buffers, "Buffer before"))
        parent_layout.addLayout(self.buffer_time_widget(buffers, "Buffer after"))

        checkbox = QHBoxLayout()

        keep_original = QCheckBox()
        keep_original.setCheckState(Qt.CheckState.Checked)
        keep_original.setFixedWidth(20)
        # keep_original.stateChanged.connect(self.show_state)
        checkbox.addWidget(keep_original)
        checkbox.addWidget(self.set_label_title("Keep original files"))

        parent_layout.addLayout(checkbox)

        run_btn = QPushButton("Run")
        run_btn.setFixedWidth(100)
        run_btn.clicked.connect(self.start_process)
        run_btn.setStyleSheet("background-color: green")
        parent_layout.addWidget(run_btn)
        parent_layout.setAlignment(run_btn, Qt.AlignmentFlag.AlignCenter)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        parent_layout.addWidget(self.text)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        parent_layout.addWidget(self.progress)

        widget = QWidget()
        widget.setLayout(parent_layout)
        self.setCentralWidget(widget)

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

    def buffer_time_widget(self, layout: QHBoxLayout, text: str) -> QHBoxLayout:
        # layout = QHBoxLayout()

        self.buffer_time = QComboBox()
        self.buffer_time.setFixedWidth(50)
        self.buffer_time.addItems(["0", "1", "2", "3", "4", "5"])
        # self.buffer_before.currentIndexChanged.connect()

        layout.addWidget(self.buffer_time)

        layout.addWidget(self.set_label_title(text))

        return layout

    def file_management_widget(self) -> QHBoxLayout:

        layout = QHBoxLayout()

        # Text input
        self.lineEdit = QLineEdit(self)
        # self.lineEdit.setFixedWidth(int(self.window_width / 2))

        # Browse button
        self.browseBtn = QPushButton("Browse Files")
        # browseBtn.setFixedWidth(100)
        self.browseBtn.clicked.connect(self.browse_files)

        layout.addWidget(self.lineEdit)
        layout.addWidget(self.browseBtn)

        return layout

    def set_label_title(self, title: str) -> QLabel:
        """Set the title of the file chooser.

        Args:
            title (str): Title of the window.
        """
        # Text label
        self.label = QLabel(title)
        # self.label.setFixedWidth(120)
        self.label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.adjustSize()
        return self.label

    # Set the central widget of the Window.
    # self.show()
    # self.setCentralWidget(button)

    def browse_files(self) -> typing.Tuple[typing.List[str], str]:
        """Open a dialog to select a file, and return the path to it."""
        filename = QFileDialog.getOpenFileNames()
        print(filename)
        self.lineEdit.setText(filename[0][0])

        return filename


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)
# Apply the complete dark theme to your Qt App.
qdarktheme.setup_theme("auto")
# Default is "rounded".
# stylesheet = qdarktheme.setup_theme(corner_shape="sharp")

window = MainWindow()
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()
=======
"""Module for testing PyQt6"""
import sys
import typing

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("My App")
        self.resize(700, 400)

        self.label = QLabel()

        self.input = QLineEdit()
        self.input.textChanged.connect(self.label.setText)

        self.browse_files()

        layout = QVBoxLayout()
        layout.addWidget(self.input)
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)

        # Set the central widget of the Window.
        self.setCentralWidget(container)

    def browse_files(self) -> typing.Tuple[str, str]:
        """Open a dialog to select a file, and return the path to it."""
        filename = QFileDialog.getOpenFileName()
        return filename


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

window = MainWindow()
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()
>>>>>>> master:app/my_app.py
