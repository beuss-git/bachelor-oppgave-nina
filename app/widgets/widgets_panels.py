"""Widgets Panels for the application."""
from dataclasses import dataclass

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from app.common import Common
from app.widgets.file_browser import FileBrowser
from app.widgets.widgets_options import Checkbox, DropDownWidget


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
        buffer_layout.addWidget(DropDownWidget("Buffer Before", Common.buffer_options))
        buffer_layout.addWidget(DropDownWidget("Buffer After", Common.buffer_options))

        parent_layout.addLayout(buffer_layout)
        parent_layout.addWidget(Checkbox("Keep original video"))
