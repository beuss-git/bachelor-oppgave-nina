"""Converts the ground truth annotations from AAU Bounding Box annotation format to YOLO format"""
import argparse
import os
import typing
import pathlib
import cv2
import pandas as pd


def aaut_to_yolo(parsed_args: dict[str, typing.Any]) -> None:
    """
    Converts the ground truth annotations from AAU Bounding Box annotation format to YOLO format
    Args:
        parsed_args (dict[str, typing.Any]): The parsed arguments from the command line
    """
    # yolo_txt_files_path = parsed_args["yoloTxtFiles"]
    annotation_path = parsed_args["annotationCSV"]
    category_file_path = parsed_args["categories"]
    image_folder_path = parsed_args["imageFolder"]
    output_path = parsed_args["outputPath"]
    pathlib.Path(output_path).mkdir(exist_ok=True, parents=True)

    _, category_numbers = import_categories(category_file_path)
    annotations_df = pd.read_csv(annotation_path, sep=";")

    yolo_df = compute_yolo_bbs(annotations_df)

    # for _, _, files in os.walk(os.path.abspath(yolo_txt_files_path)):
    for _, _, files in os.walk(os.path.abspath(image_folder_path)):
        for filename in files:
            img_name = f"{os.path.splitext(filename)[0]}.png"
            txt_name = f"{os.path.splitext(filename)[0]}.txt"
            # Check if the image has any annotations in the csv file
            if img_name in yolo_df["Filename"].values:
                # Get a list of annotations from the frame and write it to the yolo txt file
                ann_list = get_yolo_bbs(
                    yolo_df, img_name, category_numbers, image_folder_path
                )
                write_to_yolo_file(txt_name, output_path, ann_list)


def write_to_yolo_file(
    filename: str, yolo_path: str, ann_list: list[tuple[int, int, int, int, int]]
) -> None:
    """Write the annotations to a YOLO .txt file

    Args:
        filename (str): the name of the file to write to
        yolo_path (str): the path to the folder where the file should be written
        ann_list (list[tuple[int, int, int, int, int]]): the list of annotations to write
    """
    yolo_strings = [
        f"{ann[0]} {ann[1]} {ann[2]} {ann[3]} {ann[4]}\n" for ann in ann_list
    ]
    with open(os.path.join(yolo_path, filename), "w+", encoding="UTF-8") as file:
        for y_str in yolo_strings:
            if y_str not in file.read():
                file.write(y_str)


def get_yolo_bbs(
    data_frame: pd.DataFrame,
    img_name: str,
    category_numbers: dict[str, int],
    image_folder_path: str,
) -> list[tuple[int, int, int, int, int]]:
    """
    Get the YOLO annotations for a given image
    Args:
        data_frame: the dataframe containing the annotations
        img_name: the name of the image
        category_numbers: the dictionary containing the category numbers
        image_folder_path: the path to the folder containing the images

    Returns:
        list[tuple[int, int, int, int, int]]: the list of annotations
    """
    ann_list = []
    for _, annotation in data_frame[data_frame["Filename"] == img_name].iterrows():
        center_x = int(annotation["x"])
        center_y = int(annotation["y"])
        height = int(annotation["height"])
        width = int(annotation["width"])
        label = int(category_numbers[annotation["Annotation tag"]])

        image_path = os.path.join(os.path.abspath(image_folder_path), img_name)

        image_height, image_width, _ = cv2.imread(image_path).shape

        # Normalize the annotations
        center_x = center_x / image_width
        center_y = center_y / image_height
        width = width / image_width
        height = height / image_height

        # Clamp the values to be between 0 and 1
        center_x = max(0, min(center_x, 1))
        center_y = max(0, min(center_y, 1))
        width = max(0, min(width, 1))
        height = max(0, min(height, 1))

        tmp = (label, center_x, center_y, width, height)
        ann_list.append(tmp)
    return ann_list


def compute_yolo_bbs(data_frame: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the YOLO annotations from the AAU annotations (not normalized)
    Args:
        data_frame: the dataframe containing the annotations

    Returns:
        pd.DataFrame: the dataframe containing the annotations
    """
    tl_x = data_frame["Upper left corner X"]
    tl_y = data_frame["Upper left corner Y"]
    lr_x = data_frame["Lower right corner X"]
    lr_y = data_frame["Lower right corner Y"]

    # Find center point, height, and width
    width = lr_x - tl_x
    height = lr_y - tl_y

    center_x = tl_x + width / 2
    center_y = tl_y + height / 2

    data_frame["x"] = center_x
    data_frame["y"] = center_y
    data_frame["width"] = width
    data_frame["height"] = height
    return data_frame


def import_categories(file_name: str) -> tuple[dict[int, str], dict[str, int]]:
    """
    Import the category names from a file
    Args:
        file_name: the name of the file to import

    Returns:
        tuple[dict[int, str], dict[str, int]]: the dictionary containing the category names
    """
    category_labels = {}
    category_numbers = {}

    with open(file_name, encoding="UTF-8") as file:
        line_number = 1

        for line in file:
            entries = line.replace("\n", "")

            if len(entries) > 1:
                number = line_number
                label = entries

                category_labels[int(number)] = label
                category_numbers[label] = int(number)

            line_number += 1

    return category_labels, category_numbers


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Converts the ground truth annotations from AAU Bounding Box annotation "
                    "format to YOLO format "
    )
    ap.add_argument(
        "-imageFolder",
        "--imageFolder",
        type=str,
        help="Path to image folder",
        required=True,
    )
    ap.add_argument(
        "-annotationCSV",
        "--annotationCSV",
        type=str,
        help="Path to csv file with AAU Bounding Box annotations",
    )
    ap.add_argument(
        "-outputPath", "--outputPath", type=str, help="Output path for YOLO txt files"
    )
    ap.add_argument(
        "-categories", "--categories", type=str, help="Path to file with categories"
    )
    args = vars(ap.parse_args())

    aaut_to_yolo(args)
