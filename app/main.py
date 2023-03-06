"""Main file for our application"""

# Only needed for access to command line arguments
import sys
import os
from pathlib import Path
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
from app.logger import get_logger, create_logger
from .formats import Formats
from .widgets.options_widgets import AdvancedOptions
from .widgets.error_dialog import ErrorDialog
from .widgets.detection_window import DetectionWindow
from .panels import WidgetPanel

logger = get_logger()


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
        logger.info("Main window created")

        # Adds file browser panel

        self.open_dir = FileBrowser("Open Dir", Formats.FileType.OPEN_DIR)
        self.save_dir = FileBrowser("Save Dir", Formats.FileType.OPEN_DIR)
        WidgetPanel.add_file_browser_panel(
            self.parent_layout, self.open_dir, self.save_dir
        )
        self.parent_layout.addStretch()

        # Adds options panel
        WidgetPanel.add_options_panel(self.parent_layout)
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

        # Sets the layout
        widget = QWidget()
        widget.setLayout(self.parent_layout)
        self.setCentralWidget(widget)

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
