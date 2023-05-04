"""_summary_"""
from typing import Callable

from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app import settings
from app.common import Common

# from app.settings import Settings

# TODO: Refactor and decouple from settings
#       Either DropDownWidget should be named something more specific
#       or it should be made more generic in terms of settings


class DropDownWidget(QWidget):  # pylint: disable=too-few-public-methods
    """Class for Buffertime widgets

    Args:
        QWidget (QWidget): Inherits from the QWidget class
    """

    def __init__(
        self,
        title: str,
        buffer: list[str],
        tooltip_text: str,
    ) -> None:
        """Initiates the widget with a ComboBox and Label

        Args:
            title (str): string added as the label for the combobox

        Returns:
            QHBoxLayout: Local layout with the combobox and label
        """

        # Creates the local layout for the class
        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Sets up a combobox
        self.combo_box = QComboBox()
        self.combo_box.setFixedWidth(60)
        self.combo_box.addItems(buffer)

        # Adds the combobox widget and label
        layout.addWidget(self.combo_box)
        layout.addWidget(add_label(title, tooltip_text))

        # saves label as a class variable for later use
        self.label = title

    def connect(self, slot: Callable[[int], None]) -> None:
        """Connects the index changed function to the slot

        Args:
            slot (Callable[[int], None]): function to be called when index is changed
        """
        self.combo_box.currentIndexChanged.connect(slot)

    def set_index(self, index: int) -> None:
        """Sets the index of the combobox

        Args:
            index (int): the new index of the combobox
        """
        self.combo_box.setCurrentIndex(index)

    def index_changed(self, index: int) -> None:
        """Saves the changed index in the comboBox

        Args:
            index (int): the new number that the combobox contains
        """
        if self.label == "Buffer After (s)":
            settings.buffer_after = index
        elif self.label == "Buffer Before (s)":
            settings.buffer_before = index
        elif self.label == "Batch Size":
            settings.batch_size = int(Common.batch_size[index])
        else:
            settings.report_format = Common.formats[index]


class AdvancedOptions(QWidget):
    """Class for Advanced option widget

    Args:
        QWidget (QWidget): Inherits from the QWidget class
    """

    options_open = False  # Variable for if the advanced options are open or not

    def __init__(self) -> None:
        """Initiates the widget with link to open  advanced options"""

        # Creates the local layout for the class
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.advanced_layout = QVBoxLayout()
        self.advanced_layout_horizontal_checkboxes = QHBoxLayout()
        self.advanced_layout_horizontal_dropdown_spinbox = QHBoxLayout()

        self.setLayout(layout)

        # Adds a clickable label
        self.label = QLabel()
        self.text = "<a href='#'>Advanced Options</a>"
        self.label.setText(self.text)
        self.label.setFont(
            QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10)
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.setStyleSheet(
            """QToolTip { color: #000000; background-color: #ffffff; border: 1px solid white; }"""
        )
        self.label.setToolTip("Click to show advanced options")

        # Adds function to clickable link
        self.label.linkActivated.connect(self.show_options)

        # Adds widgets to the layout
        layout.addWidget(self.label)
        layout.addLayout(self.advanced_layout_horizontal_checkboxes)
        layout.addLayout(self.advanced_layout_horizontal_dropdown_spinbox)
        layout.addLayout(self.advanced_layout)

    def show_options(self) -> None:
        """Shows or removes the advanced options"""

        # Checks if the advanced options are open or not
        if self.options_open is False:
            # If not open, then it shows the advanced options
            print("open options")
            self.advanced_options()
            self.options_open = True

        else:
            # If it is open, then the advanced options are removed from view
            print("close options")
            self.clear_layout(self.advanced_layout)
            self.clear_layout(self.advanced_layout_horizontal_checkboxes)
            self.clear_layout(self.advanced_layout_horizontal_dropdown_spinbox)
            self.options_open = False

    def advanced_options(self) -> None:
        """Sets up the advanced options"""

        get_report_cb = Checkbox("Get report", "Whether to get a report or not")
        get_report_cb.set_check_state(settings.get_report)

        def on_get_report_changed(state: bool) -> None:
            settings.get_report = state

        get_report_cb.connect(on_get_report_changed)
        self.advanced_layout_horizontal_checkboxes.addWidget(get_report_cb)

        box_around_fish_cb = Checkbox(
            "Box around fish detected",
            "If you want prediction boxes around fish and the probability",
        )
        box_around_fish_cb.set_check_state(settings.box_around_fish)

        def on_box_around_fish_changed(state: bool) -> None:
            settings.box_around_fish = state

        box_around_fish_cb.connect(on_box_around_fish_changed)
        self.advanced_layout_horizontal_checkboxes.addWidget(box_around_fish_cb)

        report_format_dd = DropDownWidget(
            "Report format", Common.formats, "What format the report should be in"
        )
        report_format_dd.set_index(Common.formats.index(settings.report_format))

        def on_report_format_changed(index: int) -> None:
            settings.report_format = Common.formats[index]

        report_format_dd.connect(on_report_format_changed)

        self.advanced_layout_horizontal_dropdown_spinbox.addWidget(report_format_dd)

        batch_size_dd = DropDownWidget(
            "Batch Size",
            Common.batch_size,
            "Only for experienced IT (AI) users. \nHow many frames should be processed at once",
        )

        batch_size_dd.set_index(Common.batch_size.index(str(settings.batch_size)))

        def on_batch_size_changed(index: int) -> None:
            settings.batch_size = int(Common.batch_size[index])

        batch_size_dd.connect(on_batch_size_changed)

        self.advanced_layout_horizontal_dropdown_spinbox.addWidget(batch_size_dd)
        prediction_tooltip = """How accurate the AI should be in its predictions,
less accurate means more predictions and possibility for false positives,
More accurate means less predictions and less false positives."""

        self.advanced_layout_horizontal_dropdown_spinbox.addWidget(
            SpinBox("Prediction threshold", 0, 100, prediction_tooltip),
        )

    def clear_layout(self, layout: QBoxLayout) -> None:
        """Removes all of the advanced options

        Args:
            layout (QHBoxLayout): the local layout that is to be cleared
        """
        if layout is None:  # Checks if the layout is empty
            return

        # Iterates through the items in the layout to delete them
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())


class Checkbox(QWidget):  # pylint: disable=too-few-public-methods
    """Class for Checkbox widget"""

    def __init__(self, msg: str, tooltip_text: str) -> None:
        """Sets up a checkbox for 'keeping the original video' option

        Returns:
            QHBoxLayout: local layout for the checkbox and label
        """

        # Creates the local layout
        QWidget.__init__(self)
        layout = QHBoxLayout()

        # Sets up the checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.checkbox.setFixedWidth(20)

        # Adds widgets to layout
        layout.addWidget(self.checkbox)
        layout.addWidget(add_label(msg, tooltip_text))
        self.setToolTip(tooltip_text)

        self.setLayout(layout)

    def set_check_state(self, state: bool) -> None:
        """Sets the check state of the checkbox

        Args:
            state (Qt.CheckState): the state to set the checkbox to
        """
        qt_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        self.checkbox.setCheckState(qt_state)

    def connect(self, slot: Callable[[bool], None]) -> None:
        """Connects the checkbox 'toggled' to a function

        Args:
            function (Callable): the function to connect to
        """
        self.checkbox.toggled.connect(lambda: slot(self.checkbox.isChecked()))


class SpinBox(QWidget):  # pylint: disable=too-few-public-methods
    """Class for SpinBox widget"""

    def __init__(self, msg: str, min_val: int, max_val: int, tooltip_text: str) -> None:
        """Sets up a spinbox for 'batch size' option

        Args:
            msg (str): the message to be displayed
            min_val (int): the minimum value for the spinbox
            max_val (int): the maximum value for the spinbox
            tooltil_text (str): a string with explaination of the label

        Returns:
            QHBoxLayout: local layout for the spinbox and label
        """

        # Creates the local layout
        QWidget.__init__(self)
        layout = QHBoxLayout()

        # Sets up the spinbox
        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)

        self.spinbox.setFixedWidth(50)
        # self.spinbox.setMinimum(min_val)
        # self.spinbox.setMaximum(max_val)
        self.spinbox.setSuffix("%")
        self.spinbox.setValue(95)

        def value_changed(value: int) -> None:
            settings.prediction_threshold = value

        self.spinbox.setValue(settings.prediction_threshold)
        self.spinbox.valueChanged.connect(value_changed)

        # Adds widgets to layout
        layout.addWidget(self.spinbox)
        layout.addWidget(add_label(msg, tooltip_text))

        self.setLayout(layout)


def add_label(title: str, tooltip_text: str) -> QLabel:
    """Creates a label

    Args:
        title (str): a string with the content of the label
        tooltil_text (str): a string with explaination of the label

    Returns:
        QLabel: The label with a standard font and text size
    """
    label = QLabel()
    label.setText(title)
    label.setToolTip(tooltip_text)
    label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10))
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    label.setStyleSheet(
        """QToolTip { color: #000000; background-color: #ffffff; border: 1px solid white; }"""
    )
    return label
