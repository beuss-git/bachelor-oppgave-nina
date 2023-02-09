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
    QDialog,
    QLineEdit,
    QHBoxLayout,
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
    QProgressBar,
)
from PyQt6 import QtGui
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QProcess, QDir
import re
import qdarktheme
from fileBrowser import FileBrowser
from globals import Globals
from executeProcess import ProgressWindow


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self, mode: int = Globals.OpenFile) -> None:
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

        parent_layout = QVBoxLayout()
        self.setLayout(parent_layout)

        self.fileBrowserPanel(parent_layout)
        parent_layout.addStretch()

        run_btn = QPushButton("Run")
        run_btn.setFixedWidth(100)
        run_btn.clicked.connect(self.create_dialog)
        run_btn.setStyleSheet("background-color: green")
        parent_layout.addWidget(run_btn)
        parent_layout.setAlignment(run_btn, Qt.AlignmentFlag.AlignCenter)

        widget = QWidget()
        widget.setLayout(parent_layout)
        self.setCentralWidget(widget)

    def fileBrowserPanel(self, parent_layout: typing.Any) -> None:
        vlayout = QVBoxLayout()

        self.fileFB = FileBrowser("Open File", FileBrowser.OpenFile)
        self.filesFB = FileBrowser("Open Files", FileBrowser.OpenFiles)
        self.dirFB = FileBrowser("Open Dir", FileBrowser.OpenDirectory)
        self.saveFB = FileBrowser("Save File", FileBrowser.SaveFile)

        vlayout.addWidget(self.fileFB)
        vlayout.addWidget(self.filesFB)
        vlayout.addWidget(self.dirFB)
        vlayout.addWidget(self.saveFB)

        vlayout.addStretch()
        parent_layout.addLayout(vlayout)

    def create_dialog(self, s: QProcess) -> None:
        dlg = ProgressWindow()
        dlg.exec()


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
