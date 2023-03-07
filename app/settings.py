"""Settings for the application."""
import typing

# from PyQt6 import QtGui
from PyQt6.QtCore import QSettings
from app.common import Common

# from .globals import Globals


class Settings:
    """Settings saved in the registry"""

    # Window settings
    setting_window = QSettings("MainWindow", "WindowSize")
    setting_variables = QSettings("MainWindow", "Variables")
    window_width: int = 700
    window_height: int = 400

    # File settings
    open_path: str = ""  # Path to open file
    save_path: str = ""  # Path to save file
    buffer_before: int = 0
    buffer_after: int = 0
    keep_original: bool = False

    # Advanced settings
    get_report: bool = False
    report_format: str = "CSV"

    def __init__(self) -> None:
        pass

    # def set_all_values(self) -> None:
    #    # setting_values = get_setting_values()

    #    setting_variables.value("open_path", "", type=str)
    #    setting_variables.value("save_path", "", type=str)
    #    setting_variables.value("buffer_before", 0, type=int)
    #    setting_variables.value("buffer_after", 0, type=int)
    #    setting_variables.value("keep_original", False, type=bool)

    @staticmethod
    def set_window_size(width: int, height: int) -> None:
        """Sets the window size"""
        Settings.setting_window.setValue("window_width", width)
        Settings.setting_window.setValue("window_height", height)

    @staticmethod
    def set_path_values(path: str, browser_type: Common.FileType) -> None:
        """Sets the path values"""
        match browser_type:
            # TODO: fix save path
            case Common.FileType.SAVE_FILE:
                Settings.setting_variables.setValue("save_path", path)
            case _:
                Settings.setting_variables.setValue("open_path", path)

    @staticmethod
    def set_buffer_values(before: int, after: int) -> None:
        """Sets the buffer values"""
        Settings.setting_variables.setValue("buffer_before", before)
        Settings.setting_variables.setValue("buffer_after", after)

    @staticmethod
    def set_buffer_before(before: int) -> None:
        """Sets the buffer before value"""
        Settings.setting_variables.setValue("buffer_before", before)

    @staticmethod
    def set_buffer_after(after: int) -> None:
        """Sets the buffer after value"""
        Settings.setting_variables.setValue("buffer_after", after)

    @staticmethod
    def set_keep_original(toggle: bool) -> None:
        """Sets the keep original value"""
        Settings.setting_variables.setValue("keep_original", toggle)

    @staticmethod
    def set_get_report(toggle: bool) -> None:
        """Sets the get report value"""
        Settings.setting_variables.setValue("get_report", toggle)

    @staticmethod
    def set_report_format(format_report: str) -> None:
        """Sets the report format value"""
        Settings.setting_variables.setValue("report_format", format_report)

    # @staticmethod
    # def get_setting_values() -> None:
    #    """Gets the settings values"""
    #    setting_window = QSettings("MainWindow", "WindowSize")
    #    setting_variables = QSettings("MainWindow", "Variables")

    @staticmethod
    def get_window_width() -> typing.Any:
        """Gets the window width"""
        return Settings.setting_window.value(
            "window_width", Settings.window_width, type=int
        )

    @staticmethod
    def get_window_height() -> typing.Any:
        """Gets the window height"""
        return Settings.setting_window.value(
            "window_height", Settings.window_height, type=int
        )

    @staticmethod
    def get_open_path() -> str:
        """Gets the open path"""
        return str(Settings.setting_variables.value("open_path", "", type=str))

    @staticmethod
    def get_save_path() -> str:
        """Gets the save path"""
        return str(Settings.setting_variables.value("save_path", "", type=str))

    @staticmethod
    def get_buffer_before() -> int:
        """Gets the buffer before"""
        return int(Settings.setting_variables.value("buffer_before", 0, type=int))

    @staticmethod
    def get_buffer_after() -> int:
        """Gets the buffer after"""
        return int(Settings.setting_variables.value("buffer_after", 0, type=int))

    @staticmethod
    def get_keep_original() -> bool:
        """Gets the keep original value"""
        return bool(Settings.setting_variables.value("keep_original", False, type=bool))

    @staticmethod
    def get_get_report() -> bool:
        """Gets the get report value"""
        return bool(Settings.setting_variables.value("get_report", False, type=bool))

    @staticmethod
    def get_report_format() -> str:
        """Gets the report format value"""
        return str(Settings.setting_variables.value("report_format", "CSV", type=str))

    @staticmethod
    def close_event() -> None:
        """Saves settings when window is closed. Overrides the closeEvent method"""
        # Basic window settings
        # setting_window.setValue("window_width", window_width)
        # setting_window.setValue("window_height", window_height)

        # Variables
        Settings.setting_variables.setValue("open_path", Settings.open_path)
        Settings.setting_variables.setValue("save_path", Settings.save_path)
        Settings.setting_variables.setValue("buffer_before", Settings.buffer_before)
        Settings.setting_variables.setValue("buffer_after", Settings.buffer_after)
        Settings.setting_variables.setValue("keep_original", Settings.keep_original)
