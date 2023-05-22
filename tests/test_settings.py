# pylint: skip-file
# mypy: ignore-errors
import pytest

from app import settings


def test_setup():
    """Tests the setup function"""
    settings.setup()

    # Test that all the entries have the correct types
    assert isinstance(settings.window_width, int)
    assert isinstance(settings.window_height, int)
    assert isinstance(settings.open_path, str)
    assert isinstance(settings.save_path, str)
    assert isinstance(settings.buffer_before, int)
    assert isinstance(settings.buffer_after, int)
    assert isinstance(settings.keep_original, bool)
    assert isinstance(settings.get_report, bool)
    assert isinstance(settings.report_format, str)


def test_save_load():
    """Test the save and load functions."""
    settings.setup()

    settings.window_width = 700
    settings.open_path = ""

    # Check that the values were saved correctly
    assert settings.__settings.value("window_width") == 700
    assert settings.__settings.value("open_path") == ""

    # Change some values again
    settings.window_width = 800
    settings.open_path = "/some/path/to/dir"

    # Check that the values were saved correctly
    assert settings.__settings.value("window_width") == 800
    assert settings.__settings.value("open_path") == "/some/path/to/dir"


def test_existing_entry_change_value():
    # Arrange
    settings.setup()
    expected = 1234

    # Act
    settings.window_width = expected

    # Assert
    assert settings.window_width == expected


def test_existing_entry_change_type_raises_error():
    # Arrange
    settings.setup()

    # Act + Assert
    with pytest.raises(ValueError):
        settings.window_width = "not an int"


def test_new_entry_adds_to_entries():
    # Arrange
    settings.setup()
    expected = ("new_entry", 42, int)

    # Act
    settings.__add_entry(*expected)

    # Assert
    assert expected[0] in settings.__entries
    assert settings.__entries[expected[0]] == (expected[1], expected[2])


def test_new_entry_with_wrong_default_type_raises_error():
    # Arrange
    settings.setup()

    # Act + Assert
    with pytest.raises(ValueError):
        settings.__add_entry("bad_entry", "not an int", int)


def test_new_entry_with_wrong_type_raises_error():
    # Arrange
    settings.setup()
    settings.__add_entry("bad_entry", 42, int)

    # Act + Assert
    with pytest.raises(ValueError):
        settings.bad_entry = "not an int"
