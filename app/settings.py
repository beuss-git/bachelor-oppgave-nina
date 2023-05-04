"""Settings class for the application."""

import sys
from types import ModuleType
from typing import Any, Dict, Tuple

from PyQt6.QtCore import QSettings

from app.logger import get_logger

# region Settings

# Window settings
window_width: int = 700
window_height: int = 400

# File settings
open_path: str = ""  # Path to open file
save_path: str = ""  # Path to save file
buffer_before: int = 0
buffer_after: int = 0
keep_original: bool = True

# Advanced settings
get_report: bool = False

report_format: str = "CSV"

batch_size: int = 8

prediction_threshold: int = 50

box_around_fish: bool = False

video_crf: int = 23

max_detections: int = 100

# endregion

# ----------------------------------------------------------------------------- #

# key: name, value: ((default) value, type)
__entries: Dict[str, Tuple[Any, type]] = {}

# Create __settings as QSettings and store it as ini in data folder
__settings = QSettings("settings.ini", QSettings.Format.IniFormat)

__logger = get_logger()


# This is a hack to get the above module variables
module_vars = locals()


def __setup_entries() -> None:
    """Adds all the entries to the settings entries."""
    # use the above variables and access them through the module

    to_delete = []
    for name, value in module_vars.items():
        if name.startswith("__"):
            continue

        # Check if the value is a variable of the supported types
        if not isinstance(value, (int, float, str, bool)):
            continue

        __logger.debug("Adding entry %s with default value %s", name, value)
        __add_entry(name, value, type(value))
        to_delete += [name]

    # Delete the attributes so it doesn't get exported, and we force everything through __getattr__
    for name in to_delete:
        del module_vars[name]


def __add_entry(name: str, default_value: Any, value_type: type) -> None:
    """Adds a new entry to the settings entries.

    Args:
        name: The name of the entry as it will be exported by the module and in the ini file.
        default_value: The default value
        value_type: The type of the value

    Raises:
        ValueError: If the entry already exists
        ValueError: If the default value is not of specified type
    """
    if name in __entries:
        raise ValueError(f"Entry {name} already exists")

    # We could infer the type, but better to be explicit and raise an error if it's wrong
    if not isinstance(default_value, value_type):
        raise ValueError(f"Default value {default_value} is not of type {value_type}")

    __entries[name] = (default_value, value_type)


# TODO: rename
def __populate_entries_from_ini_config() -> None:
    """Reads the values from the ini file and sets the values in the module."""

    for name, (default_value, value_type) in __entries.items():
        value = __settings.value(name, default_value, value_type)

        # If the value is not of the correct type, use the default value
        if not isinstance(value, value_type):
            value = default_value
            __logger.warning(
                "Value for %s is not of type %s, using default value", name, value_type
            )

        __logger.debug("Setting %s to %s", name, value)
        __entries[name] = (value, value_type)


class SettingsModule(ModuleType):  # pylint: disable=too-few-public-methods
    """A subclass of the settings module that overrides __setattr__"""

    def __setattr__(self, name: str, value: Any) -> None:
        # Access the entries through the module dict
        entries = sys.modules[__name__].__dict__["__entries"]
        settings = sys.modules[__name__].__dict__["__settings"]
        logger = sys.modules[__name__].__dict__["__logger"]

        if name in entries:
            entry_type = entries[name][1]
            entries[name] = (value, entry_type)

            if not isinstance(value, entry_type):
                raise ValueError(
                    f"[{name}] Value {value} is not of type {entries[name][1]}"
                )

            settings.setValue(name, value)
            logger.debug("Storing %s as %s", name, value)
            settings.sync()
        else:
            super().__setattr__(name, value)


# Override the __getattr__ method of the settings module
def __getattr__(name: str) -> Any:
    if name in __entries:
        return __entries[name][0]
    raise AttributeError(f"Module {__name__} has no attribute {name}")


def setup() -> None:
    """Sets up the settings module."""

    __logger.debug("Settings stored at %s", __settings.fileName())

    __setup_entries()
    __populate_entries_from_ini_config()

    # Replace the settings module with a subclass that overrides __setattr__
    sys.modules[__name__].__class__ = SettingsModule
