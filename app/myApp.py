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
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt


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
        run_btn.setStyleSheet("background-color: green")
        parent_layout.addWidget(run_btn)
        parent_layout.setAlignment(run_btn, Qt.AlignmentFlag.AlignCenter)

        widget = QWidget()
        widget.setLayout(parent_layout)
        self.setCentralWidget(widget)

        """
        # self.setCentralWidget(wid)
        v_layout = QVBoxLayout()
        # wid.setFixedWidth(self.window_width)
        # wid.setFixedHeight(int(self.window_height // 2))

        # Text label
        self.label = QLabel("Folder to Analyse:")
        self.label.setFixedWidth(120)
        self.label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.adjustSize()
        v_layout.addWidget(self.label)
        v_layout.addLayout(self.file_management_widget())

        # Text label
        self.label = QLabel("Save to Folder:")
        self.label.setFixedWidth(120)
        self.label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.adjustSize()
        v_layout.addWidget(self.label)
        v_layout.addLayout(self.file_management_widget())

        wid = QWidget(self)
        wid.setLayout(v_layout)
        self.setCentralWidget(wid)
        """

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

window = MainWindow()
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()
