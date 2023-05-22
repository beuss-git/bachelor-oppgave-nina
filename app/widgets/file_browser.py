"""Creates a widget for browsing files depending on the mode"""
import os
from typing import ClassVar, List

from PyQt6.QtCore import QDir, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.common import Common
from app.widgets.widgets_options import add_label


class FileBrowser(QWidget):  # pylint: disable=too-few-public-methods
    """Class for browsing files widget

    Args:
        QWidget (QWidget): Inherits QWidget
    """

    # Creates empty list for filepaths
    filepaths: List[str] = []
    path_changed: ClassVar[pyqtSignal] = pyqtSignal(str)

    def __init__(
        self,
        title: str,
        tooltip_text: str,
        mode: Common.FileType = Common.FileType.OPEN_FILE,
    ) -> None:
        """Initiates the widget with LineEdit, Label and Button to browse files

        Args:
            title (Any): Label title
            tooltip_text (str): Tooltip text
            mode (int, optional): What kind of file browsing widget. Defaults to OpenFile.
            default_paths (List[str], optional): Default path(s) to display. Defaults to None.
        """

        # Creates empty list for filepaths
        self.filepath = ""

        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.filter_name = "All files (*.*)"

        # Adds the label
        self.label = title
        layout.addWidget(add_label(title, tooltip_text))

        # Creates a line edit to display the file path
        self.line_edit = QLineEdit(self)
        layout.addWidget(self.line_edit)

        # Connect signal to update the path
        self.line_edit.textChanged.connect(self.update_path)

        # Creates a button to open the file browser
        button = QPushButton("Browse Files")

        def use_get_file() -> None:
            self.get_file(mode)

        button.clicked.connect(use_get_file)
        layout.addWidget(button)
        layout.addStretch()

    def update_path(self, path: str) -> None:
        """Sets the path in the line edit"""
        self.line_edit.setText(path)
        self.filepath = path
        self.path_changed.emit(self.filepath)

    def get_file(self, mode: Common.FileType) -> None:
        """Opens file browser to gather one or more file(s) or save a file"""
        stored_path = self.get_path()

        # Check that the path is valid
        if stored_path and os.path.exists(stored_path):
            start_dir = stored_path
        else:
            start_dir = QDir.currentPath()

        filepath: str = ""
        match mode:
            case Common.FileType.OPEN_FILE:
                filepath = QFileDialog.getOpenFileName(
                    self,
                    caption="Choose File",
                    directory=start_dir,
                    filter=self.filter_name,
                )[0]
            case Common.FileType.OPEN_DIR:
                options = QFileDialog.Option(0)
                # options |= ~QFileDialog.Option.ShowFilesOnly

                # Changes directory to not native directory of OS
                options = (
                    QFileDialog.Option.DontUseNativeDialog
                )  # Use if want to see files in directory
                filepath = QFileDialog.getExistingDirectory(
                    self,
                    caption="Choose Directory",
                    directory=start_dir,
                    options=options,
                )
            # Else save file
            case Common.FileType.SAVE_FILE:
                filepath = QFileDialog.getSaveFileName(
                    self,
                    caption="Save/Save As",
                    directory=start_dir,
                    filter=self.filter_name,
                )[0]
            case _:
                raise ValueError(f"Invalid mode {mode}")

        if len(filepath) > 0:
            self.update_path(filepath)

    def set_path(self, path: str) -> None:
        """Sets the file path

        Args:
            path (str): File path
        """
        self.update_path(path)

    def get_path(self) -> str | None:
        """Returns the file path

        Returns:
            str: File path
        """
        return self.filepath
