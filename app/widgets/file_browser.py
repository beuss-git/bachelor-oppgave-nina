"""Open the file browser and return the selected file path."""
import typing

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QPushButton,
)
from PyQt6.QtCore import QDir
from .options_widgets import (
    add_label,
)


class FileBrowser(QWidget):
    """Class for browsing files widget

    Args:
        QWidget (_type_): _description_

    Returns:
        _type_: _description_
    """

    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    def __init__(self, title: str, mode: int = OpenFile) -> None:
        """Initiates the widget with LineEdit, Label and Button to browse files

        Args:
            title (Any): _description_
            mode (int, optional): _description_. Defaults to OpenFile.
        """

        self.filepaths: typing.List[str] = []
        # self.mode: int = mode

        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.browser_mode = mode
        self.filter_name = "All files (*.*)"
        self.dirpath = QDir.currentPath()

        self.label = add_label(title)
        layout.addWidget(self.label)

        self.line_edit = QLineEdit(self)
        self.line_edit.setFixedWidth(180)

        layout.addWidget(self.line_edit)

        self.button = QPushButton("Browse Files")
        self.button.clicked.connect(self.get_file)
        layout.addWidget(self.button)
        layout.addStretch()

        # --------------------------------------------------------------------

    # For example,
    #    setMode(FileBrowser.OpenFile)
    #    setMode(FileBrowser.OpenFiles)
    #    setMode(FileBrowser.OpenDirectory)
    #    setMode(FileBrowser.SaveFile)
    # def set_mode(self, mode: int) -> None:
    #    """_summary_"""
    #    self.mode = mode

    # --------------------------------------------------------------------
    # For example,
    #    setFileFilter('Images (*.png *.xpm *.jpg)')
    def set_file_filter(self, text: str) -> None:
        """_summary_

        Args:
            text (str): _description_
        """
        self.filter_name = text

    # --------------------------------------------------------------------
    def set_default_dir(self, path: str) -> None:
        """_summary_

        Args:
            path (str): _description_
        """
        self.dirpath = path

    # --------------------------------------------------------------------
    def get_file(self) -> None:
        """Opens file browser to gather one or more file(s) or save a file"""
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
            self.filepaths.append(
                QFileDialog.getSaveFileName(
                    self,
                    caption="Save/Save As",
                    directory=self.dirpath,
                    filter=self.filter_name,
                )[0]
            )

        if len(self.filepaths) == 0:
            return
        if len(self.filepaths) == 1:
            self.line_edit.setText(self.filepaths[0])
        else:
            self.line_edit.setText(",".join(self.filepaths))

    # --------------------------------------------------------------------
    def set_label_width(self, width: int) -> None:
        """_summary_

        Args:
            width (int): _description_
        """
        self.label.setFixedWidth(width)

    # --------------------------------------------------------------------
    def set_line_edit_width(self, width: int) -> None:
        """_summary_

        Args:
            width (int): _description_
        """
        self.line_edit.setFixedWidth(width)

    # --------------------------------------------------------------------
    def get_paths(self) -> typing.List[str]:
        """_summary_

        Returns:
            typing.List[str]: _description_
        """
        return self.filepaths


# -------------------------------------------------------------------
