"""report manager"""
from .report_manager import ReportManager


def main() -> int:
    """Main entry point for the application script"""
    report = ReportManager("xml", "C:/Users/lilli/Documents/hello")
    report.write_hello()
    # report2 = ReportManager("csv", "C:/Users/lilli/Documents/hello")
    # report3 = ReportManager("PDF", "C:/Users/lilli/Documents/hello")
    return 0
