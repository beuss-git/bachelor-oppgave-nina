"""Widgets Panels for the application."""
from dataclasses import dataclass

from PyQt6.QtWidgets import QHBoxLayout, QMessageBox, QVBoxLayout

from app import settings
from app.common import Common
from app.widgets.file_browser import FileBrowser
from app.widgets.widgets_options import Checkbox, DropDownWidget


def confirmation_dialog(message: str, title: str) -> int:
    """Shows a confirmation dialog when checkbox"""

    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Icon.Warning)
    message_box.setText(message)
    message_box.setWindowTitle(title)
    message_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    message_box.setDefaultButton(QMessageBox.StandardButton.No)

    return message_box.exec()


@dataclass
class WidgetsPanel:
    """_summary_"""

    def __init__(self) -> None:
        pass

    @staticmethod
    def add_file_browser_panel(
        parent_layout: QVBoxLayout, open_dir: FileBrowser, save_file: FileBrowser
    ) -> None:
        """Sets up panel with open dir and save files"""
        vlayout = QVBoxLayout()
        vlayout.addWidget(open_dir)
        vlayout.addWidget(save_file)

        vlayout.addStretch()
        parent_layout.addLayout(vlayout)

    @staticmethod
    def add_options_panel(parent_layout: QVBoxLayout) -> None:
        """Sets up panel with options"""

        buffer_layout = QHBoxLayout()

        buffer_before_dd = DropDownWidget(
            "Buffer Before (s)",
            Common.buffer_options,
            "Time in seconds before the fish is detected",
        )
        buffer_before_dd.set_index(settings.buffer_before)

        def on_buffer_before_changed(index: int) -> None:
            settings.buffer_before = index

        buffer_before_dd.connect(on_buffer_before_changed)

        buffer_layout.addWidget(buffer_before_dd)

        buffer_after_dd = DropDownWidget(
            "Buffer After (s)",
            Common.buffer_options,
            "Time in seconds before the fish is detected",
        )
        buffer_after_dd.set_index(settings.buffer_after)

        def on_buffer_after_changed(index: int) -> None:
            settings.buffer_after = index

        buffer_after_dd.connect(on_buffer_after_changed)
        buffer_layout.addWidget(buffer_after_dd)

        parent_layout.addLayout(buffer_layout)
        keep_original_cb = Checkbox(
            "Keep original video", "Whether to keep the original video or not"
        )
        keep_original_cb.set_check_state(settings.keep_original)

        def on_keep_original_cb_toggled(state: bool) -> None:
            if not state:
                # Set checkbox to checked so it isn't unchecked while the dialog is open
                if (
                    confirmation_dialog(
                        "Are you sure you don't want to keep the original video?",
                        "Delete original video",
                    )
                    == QMessageBox.StandardButton.Yes
                ):
                    settings.keep_original = state
                else:
                    # Keep the checkbox checked
                    keep_original_cb.set_check_state(True)
            settings.keep_original = state

        keep_original_cb.connect(on_keep_original_cb_toggled)

        parent_layout.addWidget(keep_original_cb)
