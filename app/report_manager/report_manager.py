"""Writes a detection report into chosen path"""
from xml.dom import minidom
import csv
from fpdf import FPDF
from app.data_manager.data_manager import DataManager


class ReportManager:
    """A class for managing writing the report"""

    def __init__(
        self,
        input_path: str,
        output_path: str,
        data: DataManager,
    ) -> None:
        """Initiates by saving necessary values to be available across the class

        Args:
            input_path (str): the path the video is inputted from
            output_path (str): the path the report will be outputted
            data (DataManager): manager for connecting to the sqlite database
        """
        self.output_path = output_path
        self.input_path = input_path
        self.datamanager = data

    def write_xml_file(self) -> None:
        """Writes a report in the format of an xml file"""

        root: minidom.Document = minidom.Document()

        # gets data from teh database
        item_list = self.datamanager.get_data(["tihi"])

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

        save_path_file = self.output_path + "/me.xml"

        # open the output pathway and saves the file
        with open(save_path_file, "w", encoding="ascii", errors="ignore") as out:
            out.write(xml_str)

    def write_csv_file(self) -> None:
        """Writes a report in the format of a csv file"""

        save_path_file = self.output_path + "/meh.csv"

        # Gets data from database and appends it to column titles
        row_list = [
            ("Video", "detectionID", "Start", "End")
        ] + self.datamanager.get_data(["oof"])

        # opens the output pathway and saves the file
        with open(
            save_path_file, "w", newline="", encoding="ascii", errors="ignore"
        ) as file:
            writer = csv.writer(file)
            writer.writerows(row_list)

    def write_pdf_file(self) -> None:
        """Writes a report in teh format of a pdf file"""

        save_path_file = self.output_path + "/meh.pdf"

        # Gets data from the data base
        item_list = self.datamanager.get_data(["tihi", "awe"])

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
