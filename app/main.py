"""Main file for our application"""

# Only needed for access to command line arguments
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

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
from app.execute_process import ProgressWindow
from app.widgets.options_widgets import (
    AdvancedOptions,
)
from app.panels import WidgetPanel
from app.formats import Formats
from app.settings import Settings


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self) -> None:
        """Initiates the main window"""

        super().__init__()

        # Set concurrent window settings
        self.window_width, self.window_height = (
            Settings.get_window_width(),
            Settings.get_window_height(),
        )
        # Set minimum/default window settings
        self.min_window_width, self.min_window_height = (
            Formats.default_window_width,
            Formats.default_window_height,
        )
        self.setWindowTitle("Fish detector 3000")
        self.setMinimumSize(self.min_window_width, self.min_window_height)
        self.resize(self.window_width, self.window_height)
        self.setWindowIcon(QtGui.QIcon("app/images/app_logo.png"))

        # Initializes the main layout for the window
        self.widget = QWidget()
        self.parent_layout = QVBoxLayout()

        # Sets the layout
        self.widget.setLayout(self.parent_layout)
        self.setCentralWidget(self.widget)
        print("Main window created")

        # Adds file browser panel
        WidgetPanel().file_browser_panel(self.parent_layout)
        self.parent_layout.addStretch()

        # Adds options panel
        WidgetPanel().options_panel(self.parent_layout)
        self.parent_layout.addStretch()

        # Adds advanced options panel
        self.parent_layout.addWidget(AdvancedOptions())
        self.parent_layout.addStretch()

        # Adds run button
        self.run_btn = self.run_process_button()

    def run_process_button(self) -> QPushButton:
        """Creates button to run process"""
        run_btn = QPushButton("Run")
        run_btn.setFixedWidth(100)

        def create_progressbar_dialog() -> None:
            """Opens dialog with progressbar"""
            # Creates an instance of the Progress window class and executes the window
            ProgressWindow().exec()

        run_btn.clicked.connect(create_progressbar_dialog)
        run_btn.setStyleSheet("background-color: green")
        self.parent_layout.addWidget(run_btn)
        self.parent_layout.setAlignment(run_btn, Qt.AlignmentFlag.AlignCenter)
        return run_btn

    # def get_setting_values(self) -> None:
    #    """Gets the settings values"""
    #    self.setting_window = QSettings("MainWindow", "Window Size")
    #    self.setting_variables = QSettings("MainWindow", "Variables")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pylint: disable=C0103
        """Saves settings when window is closed. Overrides the closeEvent method"""
        Settings.set_window_size(
            self.widget.frameGeometry().width(), self.widget.frameGeometry().height()
        )
        Settings.set_path_values(Settings.get_save_path(), Formats.FileType.SAVE_FILE)
        Settings.set_path_values(Settings.get_open_path(), Formats.FileType.OPEN_DIR)
        Settings.set_buffer_values(
            Settings.get_buffer_before(), Settings.get_buffer_after()
        )
        Settings.set_keep_original(Settings.get_keep_original())
        Settings.set_get_report(Settings.get_get_report())
        Settings.set_report_format(Settings.get_report_format())
        # Settings.close_event
        super().closeEvent(event)


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

    # Set up logging to file to rotate every midnight
    handler = TimedRotatingFileHandler(
        "app/log/logfile.log",
        when="midnight",
        backupCount=10,
    )

    # Set up custom naming for log files
    def namer(default_name: str) -> str:
        base_filename, ext, filedate = default_name.split(".")
        return f"{base_filename}.{filedate}.{ext}"

    handler.suffix = "%d-%m-%Y"
    handler.namer = namer
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Set up logging to console
    root_logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    logger.info("Logger created")

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
