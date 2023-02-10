import typing
from PyQt6.QtCore import QProcess


class Globals:
    OpenFile = 0
    OpenFiles = 1
    OpenDirectory = 2
    SaveFile = 3

    Process: typing.Optional[QProcess] = None
    ProcessPath = "app\dummy_script.py"
