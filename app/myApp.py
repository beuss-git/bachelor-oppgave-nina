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

        wid = QWidget(self)
        # self.setCentralWidget(wid)
        v_layout = QVBoxLayout()
        wid.setFixedWidth(self.window_width)
        wid.setFixedHeight(int(self.window_height // 2))
        wid.setLayout(v_layout)

        wid2 = QWidget(self)
        # self.setCentralWidget(wid2)
        # wid2.move(0, int(self.window_height // 1.5))
        wid2.setFixedWidth(self.window_width)
        wid2.setFixedHeight(int(self.window_height // 2) + 50)
        h_layout = QHBoxLayout()
        wid2.setLayout(h_layout)

        self.browser_mode = mode
        self.filter_name = "All files (*)"
        # self.dirpath = QDir.currentPath()

        # Text label
        self.label = QLabel("Folder to analyze:")
        self.label.setFixedWidth(120)
        self.label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.adjustSize()
        v_layout.addWidget(self.label)

        # Text input
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setFixedWidth(int(self.window_width / 2))
        h_layout.addWidget(self.lineEdit)

        # Browse button
        browseBtn = QPushButton("Browse Files")
        browseBtn.setFixedWidth(100)
        browseBtn.clicked.connect(self.browse_files)
        h_layout.addWidget(browseBtn)
        h_layout.addStretch()

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
