"""_summary_"""
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QWidget,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from ..globals import Globals


class OptionsWidget(QWidget):
    """_summary_

    Args:
        QWidget (_type_): _description_
    """

    def __init__(self, title: str) -> None:
        """_summary_

        Returns:
            QHBoxLayout: _description_
        """
        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)

        buffer_time = QComboBox()
        buffer_time.setFixedWidth(50)
        buffer_time.addItems(["0", "1", "2", "3", "4", "5"])
        buffer_time.currentIndexChanged.connect(self.index_changed)

        layout.addWidget(buffer_time)
        layout.addWidget(add_label(title))

        self.label = title

    def index_changed(self, index: int) -> None:
        """_summary_

        Args:
            index (int): _description_
        """

        if self.label == "Buffer After":
            Globals.buffer_after = index
        elif self.label == "Buffer Before":
            Globals.buffer_before = index

        print(self.label + ": " + str(index))


def keep_original_checkbox() -> QHBoxLayout:
    """_summary_

    Returns:
        QHBoxLayout: _description_
    """
    layout = QHBoxLayout()

    keep_original = QCheckBox()
    keep_original.setCheckState(Qt.CheckState.Checked)
    keep_original.setFixedWidth(20)
    keep_original.stateChanged.connect(set_checked)
    layout.addWidget(keep_original)
    layout.addWidget(add_label("Keep original"))

    return layout


def set_checked(checked: bool) -> None:
    """_summary_

    Args:
        checked (bool): _description_
    """
    Globals.check = checked
    print("Keep original: " + str(checked))
    print("Global" + str(Globals.check))


def add_label(title: str) -> QLabel:
    """_summary_

    Args:
        title (str): _description_

    Returns:
        QLabel: _description_
    """
    label = QLabel()
    label.setText(title)
    label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10))
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return label
