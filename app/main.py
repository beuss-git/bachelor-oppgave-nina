"""Main file for our application"""

# Only needed for access to command line arguments
import sys
import os
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
from .widgets.options_widgets import (
    DropDownWidget,
    AdvancedOptions,
)
from .widgets.error_dialog import ErrorDialog
from .widgets.detection_window import DetectionWindow


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
        self.save_fb = FileBrowser("Save File", FileBrowser.OpenDirectory)

        vlayout.addWidget(self.dir_fb)
        vlayout.addWidget(self.save_fb)

        vlayout.addStretch()
        self.parent_layout.addLayout(vlayout)

    def run_process_button(self) -> None:
        """Creates button to run process"""
        self.run_btn = QPushButton("Run")
        self.run_btn.setFixedWidth(100)
        self.run_btn.clicked.connect(self.run)
        self.run_btn.setStyleSheet("background-color: green")
        self.parent_layout.addWidget(self.run_btn)
        self.parent_layout.setAlignment(self.run_btn, Qt.AlignmentFlag.AlignCenter)

    def options_panel(self) -> None:
        """Sets up panel with options"""

        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(DropDownWidget("Buffer Before", Globals.buffer_options))
        buffer_layout.addWidget(DropDownWidget("Buffer After", Globals.buffer_options))

    def run(self) -> None:
        """This will run core.process_folder with the selected folder"""
        print(f"Paths: {self.dir_fb.get_paths()}")
        input_paths = self.dir_fb.get_paths()
        if len(input_paths) == 0:
            ErrorDialog("No input folder selected", parent=self).exec()
            return

        output_paths = self.save_fb.get_paths()
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
    """Main"""

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
