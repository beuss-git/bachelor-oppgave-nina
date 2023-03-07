"""Widget Panels for the application."""
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
)
from app.formats import Formats
from app.widgets.file_browser import FileBrowser
from .widgets.options_widgets import (
    DropDownWidget,
    Checkbox,
)


@dataclass
class WidgetPanel:
    """_summary_"""

    def __init__(self) -> None:
        pass

    def file_browser_panel(self, parent_layout: QVBoxLayout) -> None:
        """Sets up panel with open dir and save files"""
        vlayout = QVBoxLayout()
        open_dir = FileBrowser("Open Dir", Formats.FileType.OPEN_DIR)
        save_file = FileBrowser("Save File", Formats.FileType.SAVE_FILE)
        vlayout.addWidget(open_dir)
        vlayout.addWidget(save_file)

        vlayout.addStretch()
        parent_layout.addLayout(vlayout)

    def options_panel(self, parent_layout: QVBoxLayout) -> None:
        """Sets up panel with options"""

        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(DropDownWidget("Buffer Before", Formats.buffer_options))
        buffer_layout.addWidget(DropDownWidget("Buffer After", Formats.buffer_options))

        parent_layout.addLayout(buffer_layout)
        parent_layout.addWidget(Checkbox("Keep original video"))
