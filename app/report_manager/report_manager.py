"""_summary_"""
from xml.dom import minidom
import csv
from fpdf import FPDF
from app.data_manager.data_manager import DataManager


class ReportManager:
    """_summary_"""

    def __init__(
        self,
        input_path: str,
        output_path: str,
        data: DataManager,
    ) -> None:
        """_summary_

        Args:
            input_path (str): _description_
            output_path (str): _description_
            data (DataManager):
        """
        self.output_path = output_path
        self.input_path = input_path
        self.datamanager = data

    def write_xml_file(self) -> None:
        """_summary_"""
        root: minidom.Document = minidom.Document()

        item_list = self.datamanager.get_data()

        xml = root.createElement("Fish Detections")
        root.appendChild(xml)  # type: ignore

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

        with open(save_path_file, "w", encoding="ascii", errors="ignore") as out:
            out.write(xml_str)

    def write_csv_file(self) -> None:
        """_summary_"""
        save_path_file = self.output_path + "/meh.csv"

        row_list = self.datamanager.get_data()

        with open(
            save_path_file, "w", newline="", encoding="ascii", errors="ignore"
        ) as file:
            writer = csv.writer(file)
            writer.writerows(row_list)

    def write_pdf_file(self) -> None:
        """_summary_"""
        save_path_file = self.output_path + "/meh.pdf"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(40, 10, "Hello World!")
        pdf.output(save_path_file, "F")
