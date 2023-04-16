# pylint: skip-file
# mypy: ignore-errors
import concurrent.futures
import hashlib
import os
import pickle
import queue
from pathlib import Path

import cv2
import ffmpeg
import numpy as np
import tqdm
from imagehash import ImageHash, dhash, phash
from PIL import Image


def load_hashes(cache_file_path, batch_size=10):
    yolo_hashes = set()

    cache_file = Path(cache_file_path)
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            yolo_hashes = pickle.load(f)
        print("Loaded", len(yolo_hashes), "YOLO hashes")
    else:
        print("Processed videos file not found")

    return yolo_hashes


def overlay_and_show_images(image1, image2):
    alpha = 0.5  # alpha controls the transparency of image1 (0 <= alpha <= 1)
    beta = 1 - alpha  # beta controls the transparency of image2
    gamma = 3  # scalar added to each sum
    overlay = cv2.addWeighted(image1, alpha, image2, beta, gamma)
    cv2.imshow("Overlay", overlay)
    cv2.imwrite("overlay.jpg", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def create_hashes(dataset_path, dataset_path_2, batch_size=10):
    duplicate_images: list[tuple[str, str]] = []
    # hash, path
    yolo_hashes: dict[ImageHash, str] = {}
    # Find both .jpg or .PNG files
    image_files = list(Path(dataset_path).glob("*.jpg")) + list(
        Path(dataset_path).glob("*.PNG")
    )
    image_files += list(Path(dataset_path_2).glob("*.jpg")) + list(
        Path(dataset_path_2).glob("*.PNG")
    )
    # Randomize the order of the images
    np.random.shuffle(image_files)

    num_images = len(image_files)
    print("Found", num_images, "images in YOLO dataset")
    progress_bar = tqdm.tqdm(total=num_images, desc="Processing YOLO images")

    for i in range(0, num_images, batch_size):
        batch = image_files[i : i + batch_size]
        for image_path in batch:
            image = Image.open(image_path)
            # Check if
            the_hash = phash(image, hash_size=32, highfreq_factor=4)
            if the_hash in yolo_hashes:
                # Show the images and ask if they are the same
                # print("Found duplicate image")
                # print("Image 1:", yolo_hashes[the_hash])
                # print("Image 2:", image_path)
                # print("Hash: ", the_hash)
                # image1 = cv2.imread(str(yolo_hashes[the_hash]))
                # image2 = cv2.imread(str(image_path))
                # overlay_and_show_images(image1, image2)
                duplicate_images += [(yolo_hashes[the_hash], image_path)]
            else:
                yolo_hashes[the_hash] = image_path

        progress_bar.update(len(batch))

    progress_bar.close()
    return duplicate_images


def compare_hashes(hashes_a, hashes_b):
    print("Comparing hashes")
    matches = 0
    for hash_a in hashes_a:
        if hash_a in hashes_b:
            matches += 1

    print("Found", matches, "matches out of", len(hashes_a), "images")


def load_duplicate_images():
    with open("duplicate_images.pkl", "rb") as f:
        dup_images = pickle.load(f)
    return dup_images


dup_images = load_duplicate_images()

for dup_image in dup_images:
    # Check if file name is the same
    if Path(dup_image[0].name).stem != Path(dup_image[1].name).stem:
        print(dup_image)
