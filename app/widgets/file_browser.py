"""Creates a widget for browsing files depending on the mode"""
from typing import List
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QPushButton,
)
from PyQt6.QtCore import QDir, QSettings
import app.settings as Settings
from app.widgets.widgets_options import (
    add_label,
)
from app.common import Common

settings = QSettings("\bachelor-oppgave-nina")
config_dat_dir = Path(os.path.dirname("bachelor-oppgave-nina"))


if settings.contains("dirpath"):
    dirpath = settings.value("dirpath")
else:
    settings.setValue("dirpath", "dirpath")


class FileBrowser(QWidget):  # pylint: disable=too-few-public-methods
    """Class for browsing files widget

    Args:
        QWidget (QWidget): Inherits QWidget
    """

    # Creates empty list for filepaths
    filepaths: List[str] = []

    def __init__(
        self, title: str, mode: Common.FileType = Common.FileType.OPEN_FILE
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
        if mode == Common.FileType.SAVE_FILE:
            self.line_edit.setText(Settings.Settings.get_save_path())
        else:
            self.line_edit.setText(Settings.Settings.get_open_path())
        layout.addWidget(self.line_edit)

        # Creates a button to open the file browser
        button = QPushButton("Browse Files")

        def use_get_file() -> None:
            self.get_file(mode, self.filepaths)

        button.clicked.connect(use_get_file)
        layout.addWidget(button)
        layout.addStretch()

    def get_file(self, mode: Common.FileType, filepaths: List[str]) -> None:
        """Opens file browser to gather one or more file(s) or save a file"""
        get_dir = QDir.currentPath()
        match mode:
            # If open single file
            case Common.FileType.OPEN_FILE:
                filepaths.append(
                    QFileDialog.getOpenFileName(
                        self,
                        caption="Choose File",
                        directory=get_dir,
                        filter=self.filter_name,
                    )[0]
                )

            # Else open multiple files
            case Common.FileType.OPEN_FILES:
                filepaths.extend(
                    QFileDialog.getOpenFileNames(
                        self,
                        caption="Choose Files",
                        directory=get_dir,
                        filter=self.filter_name,
                    )[0]
                )

            # Else open directory
            case Common.FileType.OPEN_DIR:
                filepaths.append(
                    QFileDialog.getExistingDirectory(
                        self, caption="Choose Directory", directory=get_dir
                    )
                )

            # Else save file
            case _:
                filepaths.append(
                    QFileDialog.getSaveFileName(
                        self,
                        caption="Save/Save As",
                        directory=get_dir,
                        filter=self.filter_name,
                    )[0]
                )

        # If the user cancels the file browser, the filepaths list will be empty
        if len(filepaths) == 0:
            return

        # If the user selects only one file, the filepaths list will have only one element
        if len(filepaths) == 1:
            self.line_edit.setText(filepaths[0])
            self.path_changed(filepaths[0], mode)

        # If the user selects more than one file, the filepaths list will have more than one element
        else:
            self.line_edit.setText(",".join(filepaths))
            self.path_changed(",".join(filepaths), mode)

    def path_changed(self, path: str, mode: Common.FileType) -> None:
        """Saves the changed path to the global variables

        Args:
            path (str): The path to save
        """
        Settings.Settings.set_path_values(path, mode)

    def get_paths(self) -> List[str]:
        """Returns the file path

        Returns:
            str: File path
        """
        return self.filepaths
