"""report manager"""
from app.data_manager.data_manager import DataManager
from .report_manager import ReportManager


def main() -> int:
    """Main entry point for the application script"""

    datamanager = DataManager()
    # datamanager.create_table()
    datamanager.create_tables()
    datamanager.add_video_data(10, "test", "2023-02-23", "30:00:00")
    datamanager.add_detection_data(
        10,
        [("12:00:00", "13:00:00"), ("12:00:00", "13:00:00"), ("12:00:00", "13:00:00")],
    )
    datamanager.close_connection()

    report = ReportManager("xml", "C:/Users/lilli/Documents/hello")
    report.write_hello()
    # report2 = ReportManager("csv", "C:/Users/lilli/Documents/hello")
    # report3 = ReportManager("PDF", "C:/Users/lilli/Documents/hello")
    return 0
