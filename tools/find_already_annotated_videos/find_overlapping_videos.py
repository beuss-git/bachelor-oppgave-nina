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
from imagehash import dhash, phash
from PIL import Image


def extract_images_from_video(video_path, output_folder):
    video_name = video_path.stem
    cap = cv2.VideoCapture(str(video_path))

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for i in range(frame_count):
        ret, frame = cap.read()
        if ret:
            output_file_path = os.path.join(
                output_folder, f"{video_name}_frame_{i:04d}.jpg"
            )
            cv2.imwrite(output_file_path, frame)
        else:
            print(f"Failed to read frame {i} from {video_path}")

    cap.release()


def extract_images_from_video_ffmpeg(video_path, output_folder):
    video_name = video_path.stem

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    output_file_pattern = os.path.join(output_folder, f"{video_name}_frame_%04d.jpg")

    try:
        (
            ffmpeg.input(str(video_path))
            .output(output_file_pattern, format="image2", vcodec="mjpeg")
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(
            f"Error occurred while extracting frames from {video_path}: {e.stderr.decode()}"
        )


def md5_hash(image_path):
    with open(image_path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


hash_func = phash


def load_hashes(yolo_dataset_path, cache_file_path, batch_size=10):
    yolo_hashes = set()

    cache_file = Path(cache_file_path)
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            yolo_hashes = pickle.load(f)
        print("Loaded", len(yolo_hashes), "YOLO hashes")
    else:
        # Find both .jpg or .PNG files
        image_files = list(Path(yolo_dataset_path).glob("*.jpg")) + list(
            Path(yolo_dataset_path).glob("*.PNG")
        )
        num_images = len(image_files)
        print("Found", num_images, "images in YOLO dataset")
        progress_bar = tqdm.tqdm(total=num_images, desc="Processing YOLO images")

        for i in range(0, num_images, batch_size):
            batch = image_files[i : i + batch_size]
            for image_path in batch:
                image = Image.open(image_path)
                yolo_hashes.add(
                    hash_func(image, hash_size=16)
                )  # You can use dhash() if preferred

            progress_bar.update(len(batch))

        progress_bar.close()
        print("Found", len(yolo_hashes), "unique images in YOLO dataset")
        with open(cache_file_path, "wb") as f:
            pickle.dump(yolo_hashes, f)
        print("Saved hashes to", cache_file_path)

    return yolo_hashes


def load_processed_videos(file_path):
    processed_videos = set()
    cache_file = Path(file_path)
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            processed_videos = pickle.load(f)
        print("Loaded", len(processed_videos), "processed videos")
    else:
        print("Processed videos file not found")
    return processed_videos


def save_processed_videos(processed_videos, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(processed_videos, f)


def process_video(video_path, yolo_hashes, progress_bars_queue):
    try:
        progress_bar = progress_bars_queue.get()

        video_name = video_path.stem
        cap = cv2.VideoCapture(str(video_path))

        fps = 1
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_original = int(cap.get(cv2.CAP_PROP_FPS))
        interval = fps_original // fps

        progress_bar.total = frame_count // interval
        progress_bar.n = 0
        progress_bar.set_description_str(f"Processing {video_name}")
        progress_bar.refresh()
        progress_bar.reset()

        for i in range(0, frame_count, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()

            if ret:
                # _, frame_buffer = cv2.imencode(".jpg", frame)
                # frame_hash = hashlib.md5(frame_buffer.tobytes()).hexdigest()
                frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame_hash = hash_func(frame_pil, hash_size=16)

                if frame_hash in yolo_hashes:
                    progress_bars_queue.put(progress_bar)
                    return True

            progress_bar.update()

        cap.release()
        progress_bars_queue.put(progress_bar)
        return False
    except Exception as e:
        print(f"Error occurred while processing {video_path}: {e}")
        return False


def find_annotated_videos(video_folder, processed_videos, output_file, max_workers=4):
    annotated_videos = set()
    # Keep track of processed videos to avoid processing the same video multiple times
    video_files = list(
        Path(video_folder).rglob("*.mp4")
    )  # Adjust the extension if necessary
    # Remove files in "RECYCLE.BIN" folders
    video_files = [
        video_path for video_path in video_files if "RECYCLE.BIN" not in str(video_path)
    ]
    # Remove if in processed_videos
    video_files = [
        video_path for video_path in video_files if video_path not in processed_videos
    ]
    # Randomize the order of videos
    # np.random.shuffle(video_files)

    print("Found", len(video_files), "videos in folder")

    progress_bars = [
        tqdm.tqdm(total=0, position=i, leave=False) for i in range(max_workers)
    ]
    progress_bars_queue = queue.Queue()

    for progress_bar in progress_bars:
        progress_bars_queue.put(progress_bar)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_video, video_path, yolo_hashes, progress_bars_queue
            ): video_path
            for video_path in video_files
        }

        overall_progress = tqdm.tqdm(
            total=len(video_files), desc="Overall progress", position=max_workers
        )

        for future in concurrent.futures.as_completed(futures):
            video_path = futures[future]
            if future.result():
                annotated_videos.add(video_path.stem)
                # Write the video name to a file
                with open(output_file, "a") as f:
                    f.write(video_path.stem + " " + str(video_path) + "\n")

            processed_videos.add(video_path)

            save_processed_videos(processed_videos, processed_videos)
            overall_progress.update(1)
            overall_progress.set_description_str(
                "Overall progress (" + str(len(annotated_videos)) + " annotated videos)"
            )

    for progress_bar in progress_bars:
        progress_bar.close()

    overall_progress.close()
    return annotated_videos


video_folder = r"path/to/videos"  # Videos to check
reference_images = r"path/to/reference/images"  # Reference images to check against
reference_images_hashes = "hashes.pkl"  # Cache file for reference images
processed_videos = "processed_videos.pkl"  # Cache file for processed videos (to avoid processing the same video multiple times)
output_file = "annotated_videos.txt"  # Output file with annotated videos

annotated_videos = set()

yolo_hashes = load_hashes(reference_images, reference_images_hashes)

processed_videos = load_processed_videos(processed_videos)

annotated_videos = find_annotated_videos(
    video_folder, processed_videos, output_file, max_workers=4
)

print("Annotated videos:", annotated_videos)
