import typing

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QLabel,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QDir


class Widgets:
    def buffertime_widget(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        buffer_time = QComboBox()
        buffer_time.setFixedWidth(50)
        buffer_time.addItems(["0", "1", "2", "3", "4", "5"])
        # self.buffer_before.currentIndexChanged.connect()

        layout.addWidget(buffer_time)
        layout.addWidget(self.add_label("Buffertime"))

        return layout

    def keep_original_checkbox(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        keep_original = QCheckBox()
        keep_original.setCheckState(Qt.CheckState.Checked)
        keep_original.setFixedWidth(20)
        # keep_original.stateChanged.connect(self.show_state)
        layout.addWidget(keep_original)
        layout.addWidget(self.add_label("Keep original"))

        return layout

    def add_label(self, title: str) -> QLabel:
        label = QLabel()
        label.setText(title)
        label.setFixedWidth(65)
        label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return label
