"""Creates a widget for browsing files depending on the mode"""
from typing import List

from PyQt6.QtCore import QDir
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

    def __init__(
        self,
        title: str,
        mode: Common.FileType = Common.FileType.OPEN_FILE,
        default_paths: List[str] | None = None,
    ) -> None:
        """Initiates the widget with LineEdit, Label and Button to browse files

        Args:
            title (Any): Label title
            mode (int, optional): What kind of file browsing widget. Defaults to OpenFile.
        """

        # Creates empty list for filepaths
        self.filepaths: List[str] = []

        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.filter_name = "All files (*.*)"

        # Adds the label
        self.label = title
        layout.addWidget(add_label(title))

        # Creates a line edit to display the file path
        self.line_edit = QLineEdit(self)
        layout.addWidget(self.line_edit)

        # Creates a button to open the file browser
        button = QPushButton("Browse Files")

        def use_get_file() -> None:
            self.get_file(mode)

        button.clicked.connect(use_get_file)
        layout.addWidget(button)
        layout.addStretch()

        # Sets the default path(s)
        if default_paths is not None:
            self.update_paths(default_paths)

    def update_paths(self, paths: List[str]) -> None:
        """Sets the path in the line edit"""
        self.line_edit.setText(",".join(paths))
        self.filepaths = paths

    def get_file(self, mode: Common.FileType) -> None:
        """Opens file browser to gather one or more file(s) or save a file"""
        stored_path = self.get_path()
        start_dir = stored_path if stored_path else QDir.currentPath()

        filepaths: List[str] = []
        match mode:
            # If open single file
            case Common.FileType.OPEN_FILE:
                filepaths.append(
                    QFileDialog.getOpenFileName(
                        self,
                        caption="Choose File",
                        directory=start_dir,
                        filter=self.filter_name,
                    )[0]
                )

            # Else open multiple files
            case Common.FileType.OPEN_FILES:
                filepaths.extend(
                    QFileDialog.getOpenFileNames(
                        self,
                        caption="Choose Files",
                        directory=start_dir,
                        filter=self.filter_name,
                    )[0]
                )

            # Else open directory
            case Common.FileType.OPEN_DIR:
                filepaths.append(
                    QFileDialog.getExistingDirectory(
                        self, caption="Choose Directory", directory=start_dir
                    )
                )

            # Else save file
            case _:
                filepaths.append(
                    QFileDialog.getSaveFileName(
                        self,
                        caption="Save/Save As",
                        directory=start_dir,
                        filter=self.filter_name,
                    )[0]
                )

        # If the user cancels the file browser, the filepaths list will be empty
        if len(filepaths) == 0:
            return

        # The above statement seems to be wrong, as it returns an empty string if the user cancels-
        # but keeping both for now.
        if len(filepaths) == 1 and filepaths[0] == "":
            return

        self.update_paths(filepaths)

    def get_paths(self) -> List[str]:
        """Returns the file path

        Returns:
            str: File path
        """
        return self.filepaths

    def get_path(self) -> str | None:
        """Returns the file path

        Returns:
            str: File path
        """
        if len(self.filepaths) > 0:
            return self.filepaths[0]
        return None
