"""_summary_"""
import typing
from dataclasses import dataclass
from PyQt6.QtCore import QProcess


@dataclass
class Globals:
    """_summary_"""

    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    process: typing.Optional[QProcess] = None
    process_path = r"app\dummy_script.py"
