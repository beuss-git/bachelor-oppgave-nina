"""Main file for our application"""

# Only needed for access to command line arguments
import sys
import typing
import os
import qdarktheme

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QWidget,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from app.widgets.file_browser import FileBrowser
from .globals import Globals

from .widgets.options_widgets import (
    buffertime_widget,
    keep_original_checkbox,
)
from .widgets.error_dialog import ErrorDialog
from .widgets.detection_window import DetectionWindow


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self, _: int = Globals.OpenFile) -> None:
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

        parent_layout = QVBoxLayout()
        self.setLayout(parent_layout)
        print("Main window created")

        self.file_browser_panel(parent_layout)
        parent_layout.addStretch()

        self.options_panel(parent_layout)
        parent_layout.addStretch()

        self.run_process_button(parent_layout)

        widget = QWidget()
        widget.setLayout(parent_layout)
        self.setCentralWidget(widget)

    def file_browser_panel(self, parent_layout: typing.Any) -> None:
        """_summary_

        Args:
            parent_layout (typing.Any): _description_
        """
        vlayout = QVBoxLayout()

        # self.file_fb = FileBrowser("Open File", FileBrowser.OpenFile)
        # self.files_fb = FileBrowser("Open Files", FileBrowser.OpenFiles)
        self.in_dir_fb = FileBrowser("Input Dir", FileBrowser.OpenDirectory)
        self.out_dir_fb = FileBrowser("Save Dir", FileBrowser.OpenDirectory)
        # self.save_fb = FileBrowser("Save File", FileBrowser.SaveFile)

        # Set default file paths
        # TODO: use QSettings to save last used paths
        self.in_dir_fb.set_default_paths([r"C:\Users\benja\Pictures\test_folder"])
        self.out_dir_fb.set_default_paths(
            [r"C:\Users\benja\Pictures\test_folder\output"]
        )

        # vlayout.addWidget(self.file_fb)
        # vlayout.addWidget(self.files_fb)
        vlayout.addWidget(self.in_dir_fb)
        vlayout.addWidget(self.out_dir_fb)
        # vlayout.addWidget(self.save_fb)

        vlayout.addStretch()
        parent_layout.addLayout(vlayout)

    def run_process_button(self, parent_layout: typing.Any) -> None:
        """_summary_

        Args:
            parent_layout (typing.Any): _description_
        """
        self.run_btn = QPushButton("Run")
        self.run_btn.setFixedWidth(100)
        self.run_btn.clicked.connect(self.run)
        self.run_btn.setStyleSheet("background-color: green")
        parent_layout.addWidget(self.run_btn)
        parent_layout.setAlignment(self.run_btn, Qt.AlignmentFlag.AlignCenter)

    def options_panel(self, parent_layout: typing.Any) -> None:
        """_summary_

        Args:
            parent_layout (typing.Any): _description_
        """
        parent_layout.addLayout(buffertime_widget())
        parent_layout.addLayout(keep_original_checkbox())

    def run(self) -> None:
        """This will run core.process_folder with the selected folder"""
        print(f"Paths: {self.in_dir_fb.get_paths()}")
        input_paths = self.in_dir_fb.get_paths()
        if len(input_paths) == 0:
            ErrorDialog("No input folder selected", parent=self).exec()
            return

        output_paths = self.out_dir_fb.get_paths()
        if len(output_paths) == 0:
            ErrorDialog("No output folder selected", parent=self).exec()
            return

        input_folder_path = input_paths[0]
        output_folder_path = output_paths[0]

        if not os.path.exists(input_folder_path):
            ErrorDialog("Input folder does not exist", parent=self).exec()
            return

        if not os.path.exists(output_folder_path):
            ErrorDialog("Output folder does not exist", parent=self).exec()
            return

        # Disable run button while processing
        self.run_btn.setEnabled(False)

        dlg = DetectionWindow(input_folder_path, output_folder_path, parent=self)
        dlg.exec()

        # Re-enable button now that processing is done
        self.run_btn.setEnabled(True)


def main() -> None:
    """_summary_"""

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
