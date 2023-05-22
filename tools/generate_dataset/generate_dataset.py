# pylint: skip-file
# mypy: ignore-errors

"""Module to generate a dataset for training and testing."""

import multiprocessing as mp
import os
import random
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import yaml
from tqdm import tqdm

CVAT_EXPORTS_FOLDER = Path(r"path\to\cvat\exports")
DATASET_FOLDER = Path(r"path\to\output\dataset")
SOURCE_VIDEO_FOLDERS = [
    Path(r"X:\Myggbukta 2022"),
    Path(r"X:\DISK1 - Høyregga 17+18 og myggbukta 2020 mai NTNU"),
]
BACKGROUND_IMAGE_PERCENTAGE = 0.1
TRAIN_SPLIT = 0.8
PNG_QUALITY = 3  # 0-9 where 0 is the best quality
MAX_WORKERS = 8

CLASSES = [
    "Gjedde",
    "Gullbust",
    "Rumpetroll",
    "Stingsild",
    "Ørekyt",
    "Abbor",
    "Brasme",
    "Mort",
    "Vederbuk",
    "Frosk",
    "Annen fisk",
]


def get_video_filename(annotation_xml: Path) -> str:
    tree = ET.parse(annotation_xml)
    root: ET.Element = tree.getroot()
    assert root is not None, "Could not parse xml file"

    task = root.find("meta").find("task")
    return task.find("source").text


def extract_annotations(
    cvat_exports_folder: Path, output_folder: Path, processed_counter: mp.Value
) -> None:
    # NOTE: We do this because background images are randomly selected and we
    #       don't want to add more and more background images to the dataset if run multiple times
    #       also other parameters and the dataset itself might have changed.
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder, ignore_errors=True)

    annotation_folder = output_folder / "cvat_annotations"

    # Creates output folder and annotation folder
    os.makedirs(annotation_folder)

    def process_zip_file(
        zip_filepath: Path, id: int, total: int, processed_counter: mp.Value
    ) -> None:
        try:
            with zipfile.ZipFile(zip_filepath, "r") as zip_file:
                zip_file.extract(
                    "annotations.xml",
                    path=annotation_folder / f"{id:04d}",
                )
                annotation_path = annotation_folder / f"{id:04d}" / "annotations.xml"
                video_filename = get_video_filename(annotation_path)
                video_filename = os.path.splitext(video_filename)[0]

                with processed_counter.get_lock():
                    tqdm.write(f"Started processing {zip_filepath.name}")

                try:
                    generate_yolo_dataset(
                        output_folder / video_filename,
                        annotation_path,
                    )
                except FileNotFoundError as err:
                    print(err)
                    raise
            with processed_counter.get_lock():
                processed_counter.value += 1
                tqdm.write(
                    f"Finished processing {zip_filepath.name} ({processed_counter.value}/{total})"
                )
        except zipfile.BadZipFile as err:
            print(err)
            raise
        except Exception as err:
            print(err)
            raise

    # Create a ThreadPoolExecutor to parallelize the processing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        zip_filepaths = [
            cvat_exports_folder / zip_filename
            for zip_filename in os.listdir(cvat_exports_folder)
            if zip_filename.endswith(".zip")
        ]
        total_zip_files = len(zip_filepaths)

        for position, zip_filepath in enumerate(zip_filepaths):
            executor.submit(
                process_zip_file,
                zip_filepath,
                position + 1,
                total_zip_files,
                processed_counter,
            )


def parse_xml_annotation(
    xml_file: str,
) -> Tuple[
    str,
    Tuple[int, int],
    int,
    Dict[int, Dict[str, List[Tuple[float, float, float, float]]]],
]:
    tree = ET.parse(xml_file)
    root: ET.Element = tree.getroot()
    assert root is not None, "Could not parse xml file"

    task = root.find("meta").find("task")
    video_filename = task.find("source").text

    video_original_size = (
        float(task.find("original_size").find("width").text),
        float(task.find("original_size").find("height").text),
    )

    frame_count = int(task.find("size").text)

    # dictionary to store annotations, with frame number as key
    annotations: Dict[int, Dict[str, List[Tuple[float, float, float, float]]]] = {}

    # Add image annotations
    for image in root.findall("image"):
        frame_number = int(image.attrib["id"])
        annotations[frame_number] = {}
        for box in image.findall("box"):
            label = box.attrib["label"]
            occluded = box.attrib["occluded"]
            outside = box.attrib["outside"]
            # Skip occluded and outside boxes
            if occluded == "1" or outside == "1":
                continue

            xtl = float(box.attrib["xtl"])
            ytl = float(box.attrib["ytl"])
            xbr = float(box.attrib["xbr"])
            ybr = float(box.attrib["ybr"])
            if label not in annotations[frame_number]:
                annotations[frame_number][label] = []
            annotations[frame_number][label].append((xtl, ytl, xbr, ybr))

    # Add track annotations
    for track in root.findall("track"):
        label = track.attrib["label"]
        for box in track.findall("box"):
            frame_number = int(box.attrib["frame"])
            occluded = box.attrib["occluded"]
            outside = box.attrib["outside"]
            # Skip occluded and outside boxes
            if occluded == "1" or outside == "1":
                continue
            xtl = float(box.attrib["xtl"])
            ytl = float(box.attrib["ytl"])
            xbr = float(box.attrib["xbr"])
            ybr = float(box.attrib["ybr"])
            if frame_number not in annotations:
                annotations[frame_number] = {}
            if label not in annotations[frame_number]:
                annotations[frame_number][label] = []
            annotations[frame_number][label].append((xtl, ytl, xbr, ybr))

    return video_filename, video_original_size, frame_count, annotations


def generate_yolo_dataset(
    yolo_dataset_folder: Path,
    annotation_path: Path,
) -> None:
    os.makedirs(yolo_dataset_folder)

    (
        video_filename,
        video_resolution,
        frame_count,
        annotations,
    ) = parse_xml_annotation(annotation_path)

    def get_video_path(video_filename: str) -> Path:
        for source_video_folder in SOURCE_VIDEO_FOLDERS:
            search_name = os.path.splitext(video_filename)[0]
            # NOTE: we replace underscores with spaces due to handbrake naming
            search_name = re.sub(r"_", " ", search_name).upper()
            files = source_video_folder.glob("**/*.*")
            for file in files:
                if search_name in re.sub(r"_", " ", file.name).upper():
                    return file

        raise FileNotFoundError(
            f"Could not find {video_filename} in any of the source video folders"
        )

    video_path = get_video_path(video_filename)

    def extract_frames(video_path: Path) -> None:
        video = cv2.VideoCapture(str(video_path))

        frames_to_extract = list(filter(lambda n: n in annotations, range(frame_count)))

        for frame_number in frames_to_extract:
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            success, frame = video.read()
            if success:
                cv2.imwrite(
                    str(yolo_dataset_folder / f"{frame_number:06}.png"),
                    frame,
                    [int(cv2.IMWRITE_PNG_COMPRESSION), PNG_QUALITY],
                )
        video.release()

    # Iterate all the annotations and generate the yolo dataset
    # Each entry of annotations contain the frame number as key and a dictionary of labels as value, with the bounding boxes as value
    video_width, video_height = video_resolution

    for frame_number, frame_annotations in annotations.items():
        # Create annotation file
        annotation_file = yolo_dataset_folder / f"{frame_number:06}.txt"
        with open(annotation_file, "w", encoding="utf-8") as file:
            for label, boxes in frame_annotations.items():
                for box in boxes:
                    xtl, ytl, xbr, ybr = box
                    x_center = (xtl + xbr) / 2
                    y_center = (ytl + ybr) / 2
                    width = xbr - xtl
                    height = ybr - ytl

                    # Normalize the coordinates and size to be between 0 and 1
                    x_center /= video_width
                    y_center /= video_height
                    width /= video_width
                    height /= video_height

                    # Clamp the values to be between 0 and 1 (cvat annotations are sometimes OOB when starting new tracks)
                    x_center = max(0, min(1, x_center))
                    y_center = max(0, min(1, y_center))
                    width = max(0, min(1, width))
                    height = max(0, min(1, height))

                    file.write(
                        f"{CLASSES.index(label)} {x_center} {y_center} {width} {height}\n"
                    )

    # Extract annotation frames and background frames
    extract_frames(video_path)


def get_background_images(images: List[Path]) -> List[Path]:
    # Count the number of background frames by counting the number of empty annotation files and images without annotations
    background_images = []
    for image in images:
        annotation_file = image.with_suffix(".txt")
        if not annotation_file.exists() or annotation_file.stat().st_size == 0:
            background_images.append(image)
    return background_images


def adjust_background_images(images: List[Path]) -> List[Path]:
    background_images: List[Path] = get_background_images(images)

    # Remove all background images from the list of images so we don't use them twice
    images = set(images) - set(background_images)

    # Shuffle the manual background images
    random.shuffle(background_images)

    # Adjust background images to match BACKGROUND_IMAGE_PERCENTAGE
    background_image_count = int(len(images) * BACKGROUND_IMAGE_PERCENTAGE)
    if len(background_images) < background_image_count:
        print(
            f"WARNING: not enough background images, using {len(background_images)} instead of {background_image_count}"
        )
        background_image_count = len(background_images)

    background_image = background_images[:background_image_count]

    # NOTE: this doesn't actually make it so that the percentage of background images is exactly BACKGROUND_IMAGE_PERCENTAGE of the total
    #       it just adds the BACKGROUND_IMAGE_PERCENTAGE of the amount of annotated images to the total amount of images

    # Add the manual background images to the set of images
    images = list(images) + background_images

    print(f"Percentage of background images: {len(background_image) / len(images):.2f}")

    return list(images)


def split_train_val(dataset_path: Path, train_split: float) -> None:
    all_images: List[Path] = []

    # Collect all image paths from subfolders
    for folder in dataset_path.iterdir():
        if folder.is_dir():
            # Glob for .png or .jpg
            images = list(folder.glob("*.png"))
            images.extend(folder.glob("*.jpg"))

            # Make it relative to the dataset folder
            # images = [img.relative_to(dataset_path) for img in images]
            all_images.extend(images)

    all_images = adjust_background_images(all_images)

    # Shuffle the images and split them into train and val sets
    random.shuffle(all_images)

    train_size = int(len(all_images) * train_split)

    print(f"Total images: {len(all_images)}")
    print(f"Train size: {train_size}, Val size: {len(all_images) - train_size}")
    train_images = all_images[:train_size]
    val_images = all_images[train_size:]

    # Write the train.txt and val.txt files
    with open(dataset_path / "train.txt", "w", encoding="utf-8") as train_file:
        for img in train_images:
            train_file.write(f"{img}\n")

    with open(dataset_path / "val.txt", "w", encoding="utf-8") as val_file:
        for img in val_images:
            val_file.write(f"{img}\n")


if __name__ == "__main__":
    processed_counter = mp.Value("i", 0)
    try:
        extract_annotations(CVAT_EXPORTS_FOLDER, DATASET_FOLDER, processed_counter)
    except FileNotFoundError as e:
        print(e)
    split_train_val(DATASET_FOLDER, TRAIN_SPLIT)
