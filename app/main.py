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
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QProcess, QDir
import re
import qdarktheme


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

        parent_layout = QVBoxLayout()
        self.setLayout(parent_layout)

        self.fileBrowserPanel(parent_layout)
        parent_layout.addStretch()

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


class FileBrowser(QWidget):
    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    def __init__(self, title: str, mode: int = OpenFile) -> None:
        """_summary_

        Args:
            title (Any): _description_
            mode (int, optional): _description_. Defaults to OpenFile.
        """
        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.browser_mode = mode
        self.filter_name = "All files (*.*)"
        self.dirpath = QDir.currentPath()

        self.label = QLabel()
        self.label.setText(title)
        self.label.setFixedWidth(65)
        self.label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.label)

        self.lineEdit = QLineEdit(self)
        self.lineEdit.setFixedWidth(180)

        layout.addWidget(self.lineEdit)

        self.button = QPushButton("Browse Files")
        self.button.clicked.connect(self.getFile)
        layout.addWidget(self.button)
        layout.addStretch()

        # --------------------------------------------------------------------

    # For example,
    #    setMode(FileBrowser.OpenFile)
    #    setMode(FileBrowser.OpenFiles)
    #    setMode(FileBrowser.OpenDirectory)
    #    setMode(FileBrowser.SaveFile)
    def setMode(self, mode: int) -> None:
        self.mode = mode

    # --------------------------------------------------------------------
    # For example,
    #    setFileFilter('Images (*.png *.xpm *.jpg)')
    def setFileFilter(self, text: str) -> None:
        self.filter_name = text

    # --------------------------------------------------------------------
    def setDefaultDir(self, path: str) -> None:
        self.dirpath = path

    # --------------------------------------------------------------------
    def getFile(self) -> None:
        self.filepaths = []

        if self.browser_mode == FileBrowser.OpenFile:
            self.filepaths.append(
                QFileDialog.getOpenFileName(
                    self,
                    caption="Choose File",
                    directory=self.dirpath,
                    filter=self.filter_name,
                )[0]
            )
        elif self.browser_mode == FileBrowser.OpenFiles:
            self.filepaths.extend(
                QFileDialog.getOpenFileNames(
                    self,
                    caption="Choose Files",
                    directory=self.dirpath,
                    filter=self.filter_name,
                )[0]
            )
        elif self.browser_mode == FileBrowser.OpenDirectory:
            self.filepaths.append(
                QFileDialog.getExistingDirectory(
                    self, caption="Choose Directory", directory=self.dirpath
                )
            )
        else:
            options = QFileDialog.Options()
            if sys.platform == "darwin":
                options |= QFileDialog.DontUseNativeDialog
            self.filepaths.append(
                QFileDialog.getSaveFileName(
                    self,
                    caption="Save/Save As",
                    directory=self.dirpath,
                    filter=self.filter_name,
                    options=options,
                )[0]
            )
        if len(self.filepaths) == 0:
            return
        elif len(self.filepaths) == 1:
            self.lineEdit.setText(self.filepaths[0])
        else:
            self.lineEdit.setText(",".join(self.filepaths))

    # --------------------------------------------------------------------
    def setLabelWidth(self, width: int) -> None:
        self.label.setFixedWidth(width)

    # --------------------------------------------------------------------
    def setlineEditWidth(self, width: int) -> None:
        self.lineEdit.setFixedWidth(width)

    # --------------------------------------------------------------------
    def getPaths(self) -> typing.List[str]:
        return self.filepaths


# -------------------------------------------------------------------
