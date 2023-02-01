"""Converts the ground truth annotations from AAU Bounding Box annotation format to YOLO format"""
import argparse
import os
import typing
import cv2
import pandas as pd
import pathlib


def aaut_to_yolo(parsed_args: dict[str, typing.Any]) -> None:
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
            img_name = "{}.png".format(os.path.splitext(filename)[0])
            txt_name = "{}.txt".format(os.path.splitext(filename)[0])
            # Check if the image has any annotations in the csv file
            if img_name in yolo_df["Filename"].values:
                # Get a list of annotations from the frame and write it to the yolo txt file
                ann_list = get_yolo_bbs(
                    yolo_df, img_name, category_numbers, image_folder_path
                )
                write_to_yolo_file(txt_name, output_path, ann_list)
    return


def write_to_yolo_file(
    filename: str, yolo_path: str, ann_list: list[tuple[int, int, int, int, int]]
) -> None:
    yolo_strings = [
        "{} {} {} {} {}\n".format(ann[0], ann[1], ann[2], ann[3], ann[4])
        for ann in ann_list
    ]
    with open(os.path.join(yolo_path, filename), "w+", encoding="UTF-8") as f:
        for ystr in yolo_strings:
            if ystr not in f.read():
                f.write(ystr)


def get_yolo_bbs(
    df: pd.DataFrame,
    img_name: str,
    category_numbers: dict[str, int],
    image_folder_path: str,
) -> list[tuple[int, int, int, int, int]]:
    ann_list = []
    for _, annotation in df[df["Filename"] == img_name].iterrows():
        x = int(annotation["x"])
        y = int(annotation["y"])
        height = int(annotation["height"])
        width = int(annotation["width"])
        label = int(category_numbers[annotation["Annotation tag"]])

        image_path = os.path.join(os.path.abspath(image_folder_path), img_name)

        image_file = cv2.imread(image_path)

        image_height, image_width, _ = image_file.shape

        x = x / image_width
        y = y / image_height
        width = width / image_width
        height = height / image_height

        tmp = (label, x, y, width, height)
        ann_list.append(tmp)
    return ann_list


def compute_yolo_bbs(df: pd.DataFrame) -> pd.DataFrame:
    tl_x = df["Upper left corner X"]
    tl_y = df["Upper left corner Y"]
    lr_x = df["Lower right corner X"]
    lr_y = df["Lower right corner Y"]

    # Find center point, height, and width
    width = lr_x - tl_x
    height = lr_y - tl_y

    center_x = tl_x + width / 2
    center_y = tl_y + height / 2

    df["x"] = center_x
    df["y"] = center_y
    df["width"] = width
    df["height"] = height
    return df


def import_categories(file_name: str) -> tuple[dict[int, str], dict[str, int]]:
    # Import category names list
    category_labels = dict()
    category_numbers = dict()

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
        description="Converts the ground truth annotations from AAU Bounding Box annotation format to YOLO format"
    )
    ap.add_argument(
        "-imageFolder",
        "--imageFolder",
        type=str,
        help="Path to image folder",
        required=True,
    )
    """
    ap.add_argument(
        "-yoloTxtFiles",
        "--yoloTxtFiles",
        type=str,
        help="Path to YOLO txt files with annotations",
    )
    """
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
