"""Writes a detection report into chosen path"""
import csv
import typing
from pathlib import Path
from xml.dom import minidom

import xlsxwriter
from fpdf import FPDF

from app import settings
from app.data_manager.data_manager import DataManager
from app.logger import get_logger

logger = get_logger()


class ReportManager:
    """A class for managing writing the report"""

    def __init__(
        self,
        input_path: Path | None,
        output_path: Path | None,
        data: DataManager,
    ) -> None:
        """Initiates by saving necessary values to be available across the class

        Args:
            input_path (Path): the path the video is inputted from
            output_path (Path): the path the report will be outputted
            data (DataManager): manager for connecting to the sqlite database
        """
        self.output_path = output_path
        self.input_path = input_path
        self.datamanager = data
        self.file_format = settings.report_format
        self.report_name = "/Processing_report"

    def write_report(self, videos: typing.List[str]) -> None:
        """writes a report based on the list of videos entered"""

        match self.file_format:
            case "CSV":
                self.write_csv_file(videos)
            case "PDF":
                self.write_pdf_file(videos)
            case "XML":
                self.write_xml_file(videos)
            case "XLSX":
                self.write_xlsx_file(videos)

    def write_xml_file(self, videos: typing.List[str]) -> None:
        """Writes a report in the format of an xml file

        Args:
            videos (List[str]): List of videos that should be included in the report
        """

        root: minidom.Document = minidom.Document()

        # gets data from teh database
        item_list = self.datamanager.get_data(videos)

        # Sets up the root element of the file
        xml = root.createElement("Fish Detections")
        root.appendChild(xml)  # type: ignore

        # iterates through the list of detections to organize them into the file
        previous_video = ""
        for item in item_list:
            if str(item[0]) != previous_video:
                video = root.createElement("Video: " + str(item[0]))
                previous_video = str(item[0])
                xml.appendChild(video)  # type: ignore
            child = root.createElement("Detection" + str(item[1]))
            child.setAttribute("starttime", str(item[2]))
            child.setAttribute("endtime", str(item[3]))
            video.appendChild(child)  # type: ignore

        xml_str = root.toprettyxml(indent="\t")

        save_path_file = str(self.output_path) + self.report_name + ".xml"

        # open the output pathway and saves the file
        with open(save_path_file, "w", encoding="ascii", errors="ignore") as out:
            out.write(xml_str)

    def write_csv_file(self, videos: typing.List[str]) -> None:
        """Writes a report in the format of a csv file

        Args:
           videos (List[str]): List of videos that should be included in the report
        """

        save_path_file = str(self.output_path) + self.report_name + ".csv"

        # Gets data from database and appends it to column titles
        row_list = [
            ("Video", "detectionID", "Start", "End")
        ] + self.datamanager.get_data(videos)
        logger.info(row_list)

        # opens the output pathway and saves the file
        with open(
            save_path_file, "w", newline="", encoding="ascii", errors="ignore"
        ) as file:
            writer = csv.writer(file)
            writer.writerows(row_list)

    def write_pdf_file(self, videos: typing.List[str]) -> None:
        """Writes a report in the format of a pdf file

        Args:
            videos (List[str]): List of videos that should be included in the report
        """

        save_path_file = str(self.output_path) + self.report_name + ".pdf"

        # Gets data from the data base
        item_list = self.datamanager.get_data(videos)

        # sets up the pdf
        pdf = FPDF()
        pdf.add_page()

        # iterates through the detections to format and organize the file
        previous_video = ""
        for item in item_list:
            if str(item[0]) != previous_video:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(40, 10, str(item[0]))
                pdf.ln(10)
                previous_video = str(item[0])
            pdf.set_font("Arial", "", 11)
            pdf.cell(20, 10, "Detection" + str(item[1]))
            pdf.ln(6)
            pdf.cell(50, 10, "StartTime: " + str(item[2]))
            pdf.cell(50, 10, "EndTime: " + str(item[3]))
            pdf.ln(8)

        # opens the output pathway and saves the file
        pdf.output(save_path_file, "F")

    def write_xlsx_file(self, videos: typing.List[str]) -> None:
        """writes a report in the format of a xlsx file

        Args:
            videos (typing.List[str]): List of videos that should be included in the report
        """
        # Workbook() takes one, non-optional, argument
        # which is the filename that we want to create.
        save_path_file = str(self.output_path) + self.report_name + ".xlsx"

        workbook = xlsxwriter.Workbook(save_path_file)

        # The workbook object is then used to add new
        # worksheet via the add_worksheet() method.
        detectionsheet = workbook.add_worksheet()

        row_list = [
            ("Video", "detectionID", "Start", "End")
        ] + self.datamanager.get_data(videos)
        logger.info(row_list)

        row = 0
        col = 0

        for video, detection, start, end in row_list:
            detectionsheet.write(row, col, video)
            detectionsheet.write(row, col + 1, detection)
            detectionsheet.write(row, col + 2, start)
            detectionsheet.write(row, col + 3, end)
            row += 1

        summarysheet = workbook.add_worksheet()

        row_list = [
            (
                "Video",
                "Date",
                "Total detections",
                "Input Videolength",
                "Output Videolength",
            )
        ] + self.datamanager.get_video_data()
        logger.info(row_list)

        row = 0

        for video, date, detection, start, end in row_list:
            summarysheet.write(row, col, video)
            summarysheet.write(row, col + 1, date)
            summarysheet.write(row, col + 2, detection)
            summarysheet.write(row, col + 3, start)
            summarysheet.write(row, col + 4, end)
            row += 1

        # Finally, close the Excel file
        # via the close() method.
        workbook.close()
