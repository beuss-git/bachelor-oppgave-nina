"""_summary_"""
from xml.dom import minidom
import csv
from fpdf import FPDF


class ReportManager:
    """_summary_"""

    def __init__(
        self,
        file_format: str,
        output_path: str,
        # frame_ranges: typing.List[typing.Tuple[int, int]],
    ) -> None:
        """_summary_

        Args:
            file_format (str): _description_
            output_path (str): _description_
            frame_ranges (typing.List[typing.Tuple[int, int]]): _description_
        """
        self.output_path = output_path

        if file_format == "xml":
            print("xml file written")
            self.write_xml_file()
        if file_format == "csv":
            print("csv file written")
            self.write_csv_file()
        if file_format == "PDF":
            print("pdf file written")
            self.write_pdf_file()

    def write_xml_file(self) -> None:
        """_summary_"""
        root: minidom.Document = minidom.Document()

        xml = root.createElement("root")
        root.appendChild(xml)  # type: ignore

        product_child = root.createElement("product")
        product_child.setAttribute("name", "Geeks for Geeks")

        xml.appendChild(product_child)  # type: ignore

        xml_str = root.toprettyxml(indent="\t")

        save_path_file = self.output_path + "/me.xml"

        with open(save_path_file, "w", encoding="ascii", errors="ignore") as out:
            out.write(xml_str)

    def write_csv_file(self) -> None:
        """_summary_"""
        save_path_file = self.output_path + "/meh.csv"

        with open(
            save_path_file, "w", newline="", encoding="ascii", errors="ignore"
        ) as file:
            writer = csv.writer(file)

            writer.writerow(["SNo", "Name", "Subject"])
            writer.writerow([1, "Ash Ketchum", "English"])
            writer.writerow([2, "Gary Oak", "Mathematics"])
            writer.writerow([3, "Brock Lesner", "Physics"])

    def write_pdf_file(self) -> None:
        """_summary_"""
        save_path_file = self.output_path + "/meh.pdf"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(40, 10, "Hello World!")
        pdf.output(save_path_file, "F")

    def write_hello(self) -> None:
        """_summary_"""
        print("Hello")
