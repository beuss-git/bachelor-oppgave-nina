import sys
import typing

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
    QPushButton,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QDir
from optionsWidgets import Widgets


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

        layout.addWidget(Widgets.add_label(self, title))

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
        """else:
            options = QFileDialog.options()
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
            )"""
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
