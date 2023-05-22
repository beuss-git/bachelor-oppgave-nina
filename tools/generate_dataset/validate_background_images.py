# pylint: skip-file
# mypy: ignore-errors
"""
This script is used to validate the background images.
The background images are generated automatically, this script is used to validate that the images are valid by a human.
When the script is done, it will delete the marked images from the dataset.
"""
import os
import sys
from pathlib import Path
from typing import List

import cv2
import numpy as np

DATASET_FOLDER = Path(r"D:\dataset_temp\generated_test")
SUBFOLDERS_TO_EXCLUDE = [
    "backgrounds"
]  # The images in the backgrounds folder are already validated
MARKED_IMAGES_FILE = Path("marked_images.txt")  # File to store the marked images


def get_background_images(images: List[Path]) -> List[Path]:
    # Count the number of background frames by counting the number of empty annotation files and images without annotations
    background_images = []
    for image in images:
        if image.parent.name in SUBFOLDERS_TO_EXCLUDE:
            continue
        annotation_file = image.with_suffix(".txt")
        if not annotation_file.exists() or annotation_file.stat().st_size == 0:
            background_images.append(image)
    return background_images


def get_all_images(dataset_path: Path) -> List[Path]:
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
    return all_images


def display_images(images: List[Path]) -> List[Path]:
    print(f"Number of background images: {len(images)}")
    marked_images = []
    cv2.namedWindow("background_image", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "background_image", cv2.WND_PROP_TOPMOST, 1
    )  # Set the window as topmost
    i = 0
    while i < len(images):
        # Load the image using OpenCV
        img = cv2.imread(str(images[i]))

        # Resize the window to match the size of the image
        cv2.resizeWindow("background_image", img.shape[1], img.shape[0])

        # Display the image index and the image in the window
        cv2.putText(
            img,
            f"Image {i+1}/{len(images)}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
        # Display the image name
        cv2.putText(
            img,
            str(images[i]),
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
        cv2.imshow("background_image", img)

        print(f"\nDisplaying {images[i]}")
        while True:
            key = (
                cv2.waitKey(1) & 0xFF
            )  # Wait for a key event or for a short amount of time to elapse
            if key == ord("d"):
                marked_images.append(images[i])
                # Write marked images to disk immediately
                with open(MARKED_IMAGES_FILE, "a", encoding="utf-8") as f:
                    f.write(str(images[i]) + "\n")
                break
            elif key == ord("n"):
                i += 1
                break
            elif key == ord("b"):
                if i > 0:
                    i -= 1
                    break
                else:
                    print("Already on the first image")
            elif key == ord("q"):
                sys.exit(0)

        # Clear the image in the window to prevent flicker
        cv2.imshow("background_image", np.zeros((10, 10, 3), np.uint8))

    # Close the window
    cv2.destroyWindow("background_image")
    return marked_images


def delete_marked_images(marked_images: List[Path]):
    for image in marked_images:
        print(f"Deleting {image}...")
        os.remove(image)


def main() -> int:
    all_images = get_all_images(DATASET_FOLDER)
    background_images = get_background_images(all_images)
    marked_images = display_images(background_images)
    delete_marked_images(marked_images)
    return 0


if __name__ == "__main__":
    sys.exit(main())
