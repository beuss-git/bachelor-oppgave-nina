"""Main file for our application"""

# Only needed for access to command line arguments
import os
import sys
from pathlib import Path

import qdarktheme
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app import settings

# import app.settings as settings
from app.common import Common
from app.logger import create_logger, get_logger

# from app.settings import Settings
from app.widgets.detection_window import DetectionWindow
from app.widgets.error_dialog import ErrorDialog
from app.widgets.file_browser import FileBrowser
from app.widgets.widgets_options import AdvancedOptions
from app.widgets.widgets_panels import WidgetsPanel

logger = get_logger()


class MainWindow(QMainWindow):  # pylint: disable=too-few-public-methods
    """Main Window"""

    def __init__(self) -> None:
        """Initiates the main window"""

        super().__init__()

        # Set default window settings
        self.setWindowTitle("Fish detector 3000")
        self.setMinimumSize(Common.default_window_width, Common.default_window_height)
        self.resize(settings.window_width, settings.window_height)
        self.setWindowIcon(QtGui.QIcon("app/images/app_logo.png"))

        # Initializes the main layout for the central widget
        self.central_widget = QWidget()
        self.parent_layout = QVBoxLayout()
        self.central_widget.setLayout(self.parent_layout)
        self.setCentralWidget(self.central_widget)
        logger.info("Main window created")

        # Adds file browser panel
        self.open_dir = FileBrowser(
            "Open Dir", "What path to find video files in", Common.FileType.OPEN_DIR
        )
        self.open_dir.set_path(settings.open_path)

        def on_open_dir_changed(new_path: str) -> None:
            settings.open_path = new_path

        self.open_dir.path_changed.connect(on_open_dir_changed)

        self.save_dir = FileBrowser(
            "Save Dir", "What path to save video files to", Common.FileType.OPEN_DIR
        )
        self.save_dir.set_path(settings.save_path)

        def on_save_dir_changed(new_path: str) -> None:
            settings.save_path = new_path

        self.save_dir.path_changed.connect(on_save_dir_changed)

        WidgetsPanel.add_file_browser_panel(
            self.parent_layout, self.open_dir, self.save_dir
        )
        self.parent_layout.addStretch()

        # Adds options panel
        WidgetsPanel.add_options_panel(self.parent_layout)
        self.parent_layout.addStretch()

        # Adds advanced options panel
        self.parent_layout.addWidget(AdvancedOptions())
        self.parent_layout.addStretch()

        # Adds run button
        self.run_btn = QPushButton("Run")
        self.run_btn.setFixedWidth(100)
        self.run_btn.clicked.connect(self.run)
        self.run_btn.setStyleSheet("background-color: green")
        self.parent_layout.addWidget(self.run_btn)
        self.parent_layout.setAlignment(self.run_btn, Qt.AlignmentFlag.AlignCenter)

    def run(self) -> None:
        """This will run core.process_folder with the selected folder"""
        if not os.path.exists(settings.open_path):
            ErrorDialog("Input folder does not exist", parent=self).exec()
            return

        if not os.path.exists(settings.save_path):
            ErrorDialog("Output folder does not exist", parent=self).exec()
            return

        # Disable run button while processing
        self.run_btn.setEnabled(False)

        dlg = DetectionWindow(
            Path(settings.open_path), Path(settings.save_path), parent=self
        )
        dlg.exec()

        # Re-enable button now that processing is done
        self.run_btn.setEnabled(True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pylint: disable=C0103
        """Updates window width and window height settings. Overrides the closeEvent method"""

        # Update window size
        frame_geometry = self.central_widget.frameGeometry()
        settings.window_width = frame_geometry.width()
        settings.window_height = frame_geometry.height()

        # Settings.close_event
        super().closeEvent(event)


def main() -> int:
    """Main"""

    # Create the logger
    create_logger()

    settings.setup()

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

    return 0
