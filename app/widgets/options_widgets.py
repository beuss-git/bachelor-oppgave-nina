"""_summary_"""
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QCheckBox,
    QLabel,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt


def buffertime_widget() -> QHBoxLayout:
    """_summary_

    Returns:
        QHBoxLayout: _description_
    """
    layout = QHBoxLayout()

    buffer_time = QComboBox()
    buffer_time.setFixedWidth(50)
    buffer_time.addItems(["0", "1", "2", "3", "4", "5"])
    # self.buffer_before.currentIndexChanged.connect()

    layout.addWidget(buffer_time)
    layout.addWidget(add_label("Buffertime"))

    return layout


def keep_original_checkbox() -> QHBoxLayout:
    """_summary_

    Returns:
        QHBoxLayout: _description_
    """
    layout = QHBoxLayout()

    keep_original = QCheckBox()
    keep_original.setCheckState(Qt.CheckState.Checked)
    keep_original.setFixedWidth(20)
    # keep_original.stateChanged.connect(self.show_state)
    layout.addWidget(keep_original)
    layout.addWidget(add_label("Keep original"))

    return layout


def add_label(title: str) -> QLabel:
    """_summary_

    Args:
        title (str): _description_

    Returns:
        QLabel: _description_
    """
    label = QLabel()
    label.setText(title)
    label.setFixedWidth(65)
    label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10))
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return label
