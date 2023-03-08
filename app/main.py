"""Main file for our application"""

# Only needed for access to command line arguments
import os
import sys
from pathlib import Path

import qdarktheme
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app.common import Common
from app.logger import create_logger, get_logger
from app.settings import Settings
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
        self.window_width, self.window_height = (
            Settings.get_window_width(),
            Settings.get_window_height(),
        )
        self.setWindowTitle("Fish detector 3000")
        self.setMinimumSize(Common.default_window_width, Common.default_window_height)
        self.resize(self.window_width, self.window_height)
        self.setWindowIcon(QtGui.QIcon("app/images/app_logo.png"))

        # Initializes the main layout for the central widget
        self.central_widget = QWidget()
        self.parent_layout = QVBoxLayout()
        self.central_widget.setLayout(self.parent_layout)
        self.setCentralWidget(self.central_widget)
        logger.info("Main window created")

        # Adds file browser panel
        self.open_dir = FileBrowser("Open Dir", Common.FileType.OPEN_DIR)
        self.save_dir = FileBrowser("Save Dir", Common.FileType.OPEN_DIR)
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
        logger.info("Paths: %s", self.open_dir.get_paths())
        input_paths = self.open_dir.get_paths()
        if len(input_paths) == 0:
            ErrorDialog("No input folder selected", parent=self).exec()
            return

        output_paths = self.save_dir.get_paths()
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

        dlg = DetectionWindow(
            Path(input_folder_path), Path(output_folder_path), parent=self
        )
        dlg.exec()

        # Re-enable button now that processing is done
        self.run_btn.setEnabled(True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pylint: disable=C0103
        """Saves settings when window is closed. Overrides the closeEvent method"""
        Settings.set_window_size(
            self.central_widget.frameGeometry().width(),
            self.central_widget.frameGeometry().height(),
        )
        Settings.set_path_values(Settings.get_save_path(), Common.FileType.SAVE_FILE)
        Settings.set_path_values(Settings.get_open_path(), Common.FileType.OPEN_DIR)
        Settings.set_buffer_values(
            Settings.get_buffer_before(), Settings.get_buffer_after()
        )
        Settings.set_keep_original(Settings.get_keep_original())
        Settings.set_get_report(Settings.get_get_report())
        Settings.set_report_format(Settings.get_report_format())

        logger.info("Saving settings")

        # Settings.close_event
        super().closeEvent(event)


def main() -> None:
    """Main"""

    # Create the logger
    create_logger()

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
