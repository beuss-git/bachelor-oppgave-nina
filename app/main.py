"""Main file for our application"""

# Only needed for access to command line arguments
import sys
import typing
import qdarktheme

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from app.widgets.file_browser import FileBrowser
from .globals import Globals
from .execute_process import ProgressWindow
from .widgets.options_widgets import (
    BuffertimeWidget,
    AdvancedOptions,
    keep_original_checkbox,
)


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

        self.parent_layout = QVBoxLayout()
        self.setLayout(self.parent_layout)
        print("Main window created")

        self.file_browser_panel()
        self.parent_layout.addStretch()

        self.options_panel()
        self.parent_layout.addStretch()

        # self.advanced_options()
        self.parent_layout.addWidget(AdvancedOptions())
        self.parent_layout.addStretch()

        self.run_process_button(self.parent_layout)

        widget = QWidget()
        widget.setLayout(self.parent_layout)
        self.setCentralWidget(widget)

    def file_browser_panel(self) -> None:
        """_summary_

        Args:
            parent_layout (typing.Any): _description_
        """
        vlayout = QVBoxLayout()

        # self.file_fb = FileBrowser("Open File", FileBrowser.OpenFile)
        # self.files_fb = FileBrowser("Open Files", FileBrowser.OpenFiles)
        self.dir_fb = FileBrowser("Open Dir", FileBrowser.OpenDirectory)
        self.save_fb = FileBrowser("Save File", FileBrowser.SaveFile)

        # vlayout.addWidget(self.file_fb)
        # vlayout.addWidget(self.files_fb)
        vlayout.addWidget(self.dir_fb)
        vlayout.addWidget(self.save_fb)

        vlayout.addStretch()
        self.parent_layout.addLayout(vlayout)

    def run_process_button(self, parent_layout: typing.Any) -> None:
        """_summary_

        Args:
            parent_layout (typing.Any): Testing this :)
        """
        self.run_btn = QPushButton("Run")
        self.run_btn.setFixedWidth(100)
        self.run_btn.clicked.connect(self.create_progressbar_dialog)
        self.run_btn.setStyleSheet("background-color: green")
        parent_layout.addWidget(self.run_btn)
        parent_layout.setAlignment(self.run_btn, Qt.AlignmentFlag.AlignCenter)

    def options_panel(self) -> None:
        """_summary_

        Args:
            parent_layout (typing.Any): _description_
        """

        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(BuffertimeWidget("Buffer Before"))
        buffer_layout.addWidget(BuffertimeWidget("Buffer After"))

        self.parent_layout.addLayout(buffer_layout)
        self.parent_layout.addLayout(keep_original_checkbox())

    def create_progressbar_dialog(self) -> None:
        """_summary_"""
        dlg = ProgressWindow()
        dlg.exec()


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
