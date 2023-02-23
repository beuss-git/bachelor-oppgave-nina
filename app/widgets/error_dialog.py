"""This module contains the error dialog widget."""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QLabel, QWidget


class ErrorDialog(QDialog):
    """This is an error dialog.
    It will display an error message and a OK/CANCEL button layout."""

    def __init__(
        self,
        message: str,
        parent: QWidget | None = None,
        buttons: QDialogButtonBox.StandardButton = QDialogButtonBox.StandardButton.Ok,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Error")

        self.button_box = QDialogButtonBox(buttons)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.dialog_layout = QVBoxLayout()

        msg = QLabel(message)
        self.dialog_layout.addWidget(msg)
        self.dialog_layout.addWidget(self.button_box)

        self.setLayout(self.dialog_layout)
