"""_summary_"""
import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QProcess


@dataclass
class Common:
    """Data class with global data"""

    class FileType(Enum):  # File browser modes
        """an enum class for different modes for FileBrowser

        Args:
          Enum (_type_): Base class for creating enumerated constants.
        """

        OPEN_FILE = 0
        OPEN_DIR = 1
        SAVE_FILE = 2

    process: typing.Optional[QProcess] = None  # The process to be executed
    process_path = r"app\dummy_script.py"  # The path to script executed

    # default window size
    default_window_width: int = 700
    default_window_height: int = 540

    # Buffer time saved
    buffer_options = ["0", "1", "2", "3", "4", "5"]

    # Report variables
    formats = ["CSV", "XLSX"]

    batch_size = ["8", "16", "32", "64", "128", "256"]

    weights_folder = Path(r"data/models")
