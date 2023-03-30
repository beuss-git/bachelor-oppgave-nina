"""Script to find the distribution of annotations in a yolo dataset."""
# pylint: disable=missing-function-docstring
import csv
from pathlib import Path

from tqdm import tqdm

NAMES_FILE_NAME = "obj.names"
# DATA_FOLDER_NAME = "obj_train_data"


DATASET_PATH = Path(r"D:\dataset_temp\spliced")


def load_names() -> list[str]:
    with (DATASET_PATH / NAMES_FILE_NAME).open("r", encoding="utf-8") as file:
        dataset_names = file.read().splitlines()
    return dataset_names


def get_annotation_distribution() -> list[tuple[str, int]]:
    annotations_dist: list[int] = [0 for _ in names]
    # Get subdirectories of DATASET_PATH
    subdirectories = [
        subdirectory for subdirectory in DATASET_PATH.iterdir() if subdirectory.is_dir()
    ]
    # Get all .txt files in the subdirectories
    filenames = [
        filename
        for subdirectory in subdirectories
        for filename in subdirectory.glob("*.txt")
    ]
    with tqdm(total=len(filenames), desc="Processing annotations") as progress_bar:
        for filename in filenames:
            with filename.open("r") as file:
                for line in file:
                    try:
                        class_id, _, _, _, _ = line.split()
                        annotations_dist[int(class_id)] += 1
                    except ValueError as err:
                        print(f"Error processing {filename}: {err}")

            progress_bar.update(1)
    return list(zip(names, annotations_dist))


def write_annotation_distribution_to_csv(
    annotations_dist: list[tuple[str, int]]
) -> None:
    with open("annotations_dist.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Num annotations"])
        writer.writerows(annotations_dist)


names = load_names()

annotations = get_annotation_distribution()

print(annotations)

write_annotation_distribution_to_csv(annotations)
