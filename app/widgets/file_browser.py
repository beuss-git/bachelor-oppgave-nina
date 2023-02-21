"""Creates a widget for browsing files depending on the mode"""
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
        QWidget (QWidget): Inherits QWidget
    """

    # File browser modes
    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    def __init__(self, title: str, mode: int = OpenFile) -> None:
        """Initiates the widget with LineEdit, Label and Button to browse files

        Args:
            title (Any): Label title
            mode (int, optional): What kind of file browsing widget. Defaults to OpenFile.
        """

        # Creates empty list for filepaths
        self.filepaths: typing.List[str] = []

        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.browser_mode = mode
        self.filter_name = "All files (*.*)"
        self.dirpath = QDir.currentPath()

        # Adds the label
        self.label = title
        layout.addWidget(add_label(title))

        # Creates a line edit to display the file path
        self.line_edit = QLineEdit(self)
        layout.addWidget(self.line_edit)

        # Creates a button to open the file browser
        self.button = QPushButton("Browse Files")
        self.button.clicked.connect(self.get_file)
        layout.addWidget(self.button)
        layout.addStretch()

    def get_file(self) -> None:
        """Opens file browser to gather one or more file(s) or save a file"""
        self.filepaths = []

        # If open single file
        if self.browser_mode == FileBrowser.OpenFile:
            self.filepaths.append(
                QFileDialog.getOpenFileName(
                    self,
                    caption="Choose File",
                    directory=self.dirpath,
                    filter=self.filter_name,
                )[0]
            )

        # Else open multiple files
        elif self.browser_mode == FileBrowser.OpenFiles:
            self.filepaths.extend(
                QFileDialog.getOpenFileNames(
                    self,
                    caption="Choose Files",
                    directory=self.dirpath,
                    filter=self.filter_name,
                )[0]
            )

        # Else open directory
        elif self.browser_mode == FileBrowser.OpenDirectory:
            self.filepaths.append(
                QFileDialog.getExistingDirectory(
                    self, caption="Choose Directory", directory=self.dirpath
                )
            )

        # Else save file
        else:
            self.filepaths.append(
                QFileDialog.getSaveFileName(
                    self,
                    caption="Save/Save As",
                    directory=self.dirpath,
                    filter=self.filter_name,
                )[0]
            )

        # If the user cancels the file browser, the filepaths list will be empty
        if len(self.filepaths) == 0:
            return

        # If the user selects only one file, the filepaths list will have only one element
        if len(self.filepaths) == 1:
            self.line_edit.setText(self.filepaths[0])

        # If the user selects more than one file, the filepaths list will have more than one element
        else:
            self.line_edit.setText(",".join(self.filepaths))
