"""_summary_"""
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QWidget,
)
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from ..globals import Globals


class DropDownWidget(QWidget):  # pylint: disable=too-few-public-methods
    """Class for Buffertime widgets

    Args:
        QWidget (QWidget): Inherits from the QWidget class
    """

    def __init__(
        self,
        title: str,
        buffer: list[str],
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
        self.buffer_time = QComboBox()
        self.buffer_time.setFixedWidth(50)
        self.buffer_time.addItems(buffer)
        self.buffer_time.currentIndexChanged.connect(
            self.index_changed
        )  # connects interaction to the index changed function

        # Adds the combobox widget and label
        layout.addWidget(self.buffer_time)
        layout.addWidget(add_label(title))

        # saves label as a class variable for later use
        self.label = title

    def index_changed(self, index: int) -> None:
        """Saves the changed index in the comboBox

        Args:
            index (int): the new number that the combobox contains
        """

        if self.label == "Buffer After":
            Globals.buffer_after = index
        elif self.label == "Buffer Before":
            Globals.buffer_before = index

        print(self.label + ": " + str(index))


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
            self.options_open = False

    def advanced_options(self) -> None:
        """Sets up the advanced options"""
        self.advanced_layout.addWidget(Checkbox("Get report"))
        self.advanced_layout.addWidget(DropDownWidget("Report format", Globals.formats))

    def clear_layout(self, layout: QVBoxLayout) -> None:
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

    def __init__(self, msg: str) -> None:
        """Sets up a checkbox for 'keeping the original video' option

        Returns:
            QHBoxLayout: local layout for the checkbox and label
        """

        # Creates the local layout
        QWidget.__init__(self)
        layout = QHBoxLayout()

        # Sets up the checkbox
        self.keep_original = QCheckBox()
        self.keep_original.setCheckState(Qt.CheckState.Checked)
        self.keep_original.setFixedWidth(20)
        self.keep_original.stateChanged.connect(self.set_checked)

        # Adds widgets to layout
        layout.addWidget(self.keep_original)
        layout.addWidget(add_label(msg))

        self.setLayout(layout)

    def set_checked(self, checked: bool) -> None:
        """Saves the status of the checkbox

        Args:
            checked (bool): a bool for whether or not the checkbox is checked or not
        """
        Globals.check = checked
        print("Keep original: " + str(checked))
        print("Global " + str(Globals.check))


def add_label(title: str) -> QLabel:
    """Creates a label

    Args:
        title (str): a string with the content of the label

    Returns:
        QLabel: The label with a standard font and text size
    """
    label = QLabel()
    label.setText(title)
    label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold, pointSize=10))
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return label
