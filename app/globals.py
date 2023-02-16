"""_summary_"""
import typing
from dataclasses import dataclass
from PyQt6.QtCore import QProcess


@dataclass
class Globals:
    """Data class with global data"""

    #
    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    process: typing.Optional[QProcess] = None  # The process to be executed
    process_path = r"app\dummy_script.py"  # The path to script executed

    # Buffer time saved
    buffer_after = 0
    buffer_before = 0
    buffer_options = ["0", "1", "2", "3", "4", "5"]

    # Variable for keeping the original video
    check = False

    # Report variables
    formats = ["PDF", "CSV", "XML"]
