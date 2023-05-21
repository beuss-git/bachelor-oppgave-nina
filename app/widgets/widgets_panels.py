"""Widgets Panels for the application."""
from dataclasses import dataclass

from PyQt6.QtWidgets import QHBoxLayout, QMessageBox, QVBoxLayout

from app import settings
from app.common import Common
from app.logger import get_logger
from app.widgets.file_browser import FileBrowser
from app.widgets.widgets_options import Checkbox, DropDownWidget

logger = get_logger()


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
    def add_options_panel(
        parent_layout: QVBoxLayout,
    ) -> None:  # pylint: disable=too-many-locals
        """Sets up panel with options"""

        layout_r1 = QHBoxLayout()
        layout_r2 = QHBoxLayout()
        layout_r3 = QHBoxLayout()

        WidgetsPanel.__add_buffer_before_dropdown(layout_r1)
        WidgetsPanel.__add_buffer_after_dropdown(layout_r1)

        get_report_cb = Checkbox("Get Report", "Whether to get a report or not")
        get_report_cb.set_check_state(settings.get_report)

        def on_get_report_changed(state: bool) -> None:
            settings.get_report = state

        get_report_cb.connect(on_get_report_changed)
        layout_r2.addWidget(get_report_cb)

        report_format_dd = DropDownWidget(
            "Report Format", Common.formats, "What format the report should be in"
        )
        report_format_dd.set_index(Common.formats.index(settings.report_format))

        def on_report_format_changed(index: int) -> None:
            settings.report_format = Common.formats[index]

        report_format_dd.connect(on_report_format_changed)

        layout_r2.addWidget(report_format_dd)

        keep_original_cb = Checkbox(
            "Keep Original Video", "Whether to keep the original video or not"
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
        layout_r3.addWidget(keep_original_cb)

        box_around_fish_cb = Checkbox(
            "Box Around Fish Detected",
            "Will place a box around the fish detected in the video "
            + "including the confidence level and label",
        )
        box_around_fish_cb.set_check_state(settings.box_around_fish)

        def on_box_around_fish_changed(state: bool) -> None:
            settings.box_around_fish = state

        box_around_fish_cb.connect(on_box_around_fish_changed)
        layout_r3.addWidget(box_around_fish_cb)

        parent_layout.addLayout(layout_r1)
        parent_layout.addLayout(layout_r2)
        parent_layout.addLayout(layout_r3)

    @staticmethod
    def __add_buffer_before_dropdown(layout: QHBoxLayout) -> None:
        buffer_before_dd = DropDownWidget(
            "Buffer Before (s)",
            Common.buffer_options,
            "Time in seconds before the fish is detected",
        )
        buffer_before_dd.set_index(settings.buffer_before)

        def on_buffer_before_changed(index: int) -> None:
            settings.buffer_before = index

        buffer_before_dd.connect(on_buffer_before_changed)
        layout.addWidget(buffer_before_dd)

    @staticmethod
    def __add_buffer_after_dropdown(layout: QHBoxLayout) -> None:
        buffer_after_dd = DropDownWidget(
            "Buffer After (s)",
            Common.buffer_options,
            "Time in seconds before the fish is detected",
        )
        buffer_after_dd.set_index(settings.buffer_after)

        def on_buffer_after_changed(index: int) -> None:
            settings.buffer_after = index

        buffer_after_dd.connect(on_buffer_after_changed)
        layout.addWidget(buffer_after_dd)
