"""Main file for our application"""

# Only needed for access to command line arguments
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import time

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
from .execute_process import ProgressWindow
from .widgets.options_widgets import (
    DropDownWidget,
    AdvancedOptions,
    Checkbox,
)
from .globals import Globals


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self) -> None:
        """Initiates the main window"""

        super().__init__()

        # Set default window settings
        self.window_width, self.window_height = 700, 400
        self.setWindowTitle("Fish detector 3000")
        self.setMinimumSize(self.window_width, self.window_height)
        self.setWindowIcon(QtGui.QIcon("app/images/app_logo.png"))

        # Sets main layout for the window
        self.parent_layout = QVBoxLayout()
        self.setLayout(self.parent_layout)
        print("Main window created")

        # Adds file browser panel
        self.file_browser_panel()
        self.parent_layout.addStretch()

        # Adds options panel
        self.options_panel()
        self.parent_layout.addStretch()

        # Adds advanced options panel
        self.parent_layout.addWidget(AdvancedOptions())
        self.parent_layout.addStretch()

        # Adds run button
        self.run_process_button()

        # Sets the layout
        widget = QWidget()
        widget.setLayout(self.parent_layout)
        self.setCentralWidget(widget)

    def file_browser_panel(self) -> None:
        """Sets up panel with open dir and save files"""
        vlayout = QVBoxLayout()

        self.dir_fb = FileBrowser("Open Dir", FileBrowser.OpenDirectory)
        self.save_fb = FileBrowser("Save File", FileBrowser.SaveFile)

        vlayout.addWidget(self.dir_fb)
        vlayout.addWidget(self.save_fb)

        vlayout.addStretch()
        self.parent_layout.addLayout(vlayout)

    def run_process_button(self) -> None:
        """Creates button to run process"""
        self.run_btn = QPushButton("Run")
        self.run_btn.setFixedWidth(100)
        self.run_btn.clicked.connect(self.create_progressbar_dialog)
        self.run_btn.setStyleSheet("background-color: green")
        self.parent_layout.addWidget(self.run_btn)
        self.parent_layout.setAlignment(self.run_btn, Qt.AlignmentFlag.AlignCenter)

    def options_panel(self) -> None:
        """Sets up panel with options"""

        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(DropDownWidget("Buffer Before", Globals.buffer_options))
        buffer_layout.addWidget(DropDownWidget("Buffer After", Globals.buffer_options))

        self.parent_layout.addLayout(buffer_layout)
        self.parent_layout.addWidget(Checkbox("Keep original video"))

    def create_progressbar_dialog(self) -> None:
        """Opens dialog with progressbar"""

        # Creates an instance of the Progress window class
        dlg = ProgressWindow()

        # Executes the window
        dlg.exec()


def main() -> None:
    """Main"""

    # log_location = "main"
    logger = logging.getLogger("log")
    logger.setLevel(logging.DEBUG)

    # Set up logging
    # format the log entries
    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = TimedRotatingFileHandler(
        "app/log/logfile.log",
        when="midnight",
        backupCount=10,
    )

    def namer(default_name: str) -> str:
        base_filename, ext, filedate = default_name.split(".")
        return f"{base_filename}.{filedate}.{ext}"

    handler.suffix = "%d-%m-%Y"
    handler.namer = namer
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    while True:
        logger.debug("Logger created")
        time.sleep(2)
        logger.debug("Hei")
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
