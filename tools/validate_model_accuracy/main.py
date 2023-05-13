# pylint: skip-file
# mypy: ignore-errors

import json
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import List, Tuple

import cv2
from sklearn.metrics import precision_recall_fscore_support
from torch import Tensor

from app.detection import detection
from app.detection.batch_yolov8 import BatchYolov8

WEIGHTS = Path(
    # r"C:\Users\benja\Documents\repos\bachelor-oppgave-nina\runs\detect\train3\weights\best.pt"
    # r"\\wsl.localhost\Ubuntu\home\beuss\dev\train_v8\runs\detect\train9\weights\best.pt"
    r"C:\Users\benja\Documents\repos\bachelor-oppgave-nina\data\models\v8s-640-classes-augmented-backgrounds.pt"
)
DEVICE = "cuda:0"
GROUND_TRUTH_VIDEO_DATA = Path(r"ground_truth_data.json")

FRAME_BUFFER = 30


@dataclass
class Range:
    start: int
    end: int


@dataclass
class VideoData:
    video_path: Path
    ranges: List[Range]
    fps: int
    video_end: int


# NOTE: if not on edge and only a couple of frames, discard
def detected_frames_to_ranges(
    frames: List[int], frame_buffer: int
) -> List[Tuple[int, int]]:
    """Convert a list of detected frames to a list of ranges.
        Due to detection inaccuracies we need to allow for some dead frames
        without detections within a valid range.

    Args:
        frames: A list of detected frames.
        frame_buffer: The number of frames we allow to be without detection
                        before we consider it a new range.
    """

    if len(frames) == 0:
        return []

    frame_ranges: List[Tuple[int, int]] = []
    start_frame = frames[0]
    end_frame = frames[0]

    for frame in frames[1:]:
        if frame <= end_frame + frame_buffer:
            # Extend the range
            end_frame = frame
        else:
            # Start a new range
            frame_ranges.append((start_frame, end_frame))
            start_frame = frame
            end_frame = frame

    # Add the last range
    frame_ranges.append((start_frame, end_frame))

    return frame_ranges


# TODO: calculate detection accuracy over all the frames


def calculate_detection_accuracy(
    frames_with_fish: List[int], ground_truth_ranges: List[Tuple[int, int]]
) -> Tuple[float, float, float]:
    predicted_ranges = detected_frames_to_ranges(
        frames_with_fish, frame_buffer=FRAME_BUFFER
    )
    predicted_frames = set(
        [frame for (start, end) in predicted_ranges for frame in range(start, end + 1)]
    )
    true_positives = len(
        predicted_frames.intersection(
            set(
                [
                    frame
                    for (start, end) in ground_truth_ranges
                    for frame in range(start, end + 1)
                ]
            )
        )
    )
    false_positives = len(
        predicted_frames.difference(
            set(
                [
                    frame
                    for (start, end) in ground_truth_ranges
                    for frame in range(start, end + 1)
                ]
            )
        )
    )
    false_negatives = len(
        set(
            [
                frame
                for (start, end) in ground_truth_ranges
                for frame in range(start, end + 1)
            ]
        ).difference(predicted_frames)
    )
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        [1] * true_positives + [0] * false_positives + [0] * false_negatives,
        [1] * true_positives + [1] * false_negatives + [0] * false_positives,
        average="binary",
    )
    return precision, recall, f1_score


def calculate_temporal_overlap(
    predicted_ranges: List[Tuple[int, int]],
    ground_truth_ranges: List[Tuple[int, int]],
    iou_threshold: float = 0.5,
) -> float:
    print(f"GR: {len(ground_truth_ranges)}")
    print(f"PR: {len(predicted_ranges)}")

    def calculate_iou(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        start_a: int = a[0]
        end_a: int = a[1]
        start_b: int = b[0]
        end_b: int = b[1]
        intersection_start: int = max(start_a, start_b)
        intersection_end: int = min(end_a, end_b)
        intersection: int = max(0, intersection_end - intersection_start + 1)

        union: int = (end_a - start_a + 1) + (end_b - start_b + 1) - intersection
        if union == 0 or intersection == 0:
            return 0.0
        return intersection / union

    matched_ranges = 0
    for ground_truth_range in ground_truth_ranges:
        for predicted_range in predicted_ranges:
            iou = calculate_iou(ground_truth_range, predicted_range)
            # NOTE: Should allow for lower threshold if no other ranges are detected for the ground truth range.
            #       This should only add the current IOU
            if iou >= iou_threshold:
                matched_ranges += 1
                break

    if len(ground_truth_ranges) == 0:
        return 1

    # Returns % of ground truth ranges that were matched
    # TODO: account for too many predicted ranges
    return matched_ranges / len(ground_truth_ranges)


def load_video_data() -> List[VideoData]:
    """This function loads the video data from the json file.
    It expects the following format:
    {
        "videos": [
            {
                "video_name": [
                    {
                        "start": int,
                        "end": int,
                        "seconds": bool
                    }
                    ...
                ]
                "video_end": int (optional)
            }
        ]
    }
    """

    with open(GROUND_TRUTH_VIDEO_DATA, "r", encoding="utf-8") as file:
        data = json.load(file)

    video_data: List[VideoData] = []
    for video in data["videos"]:
        video_name = video["path"]
        video_path = Path(video_name)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")

        if "video_end" in video:
            video_end = int(video["video_end"])
        else:
            video_end = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fps = cap.get(cv2.CAP_PROP_FPS)

        ranges = []
        for video_range in video["ranges"]:
            seconds = video_range["seconds"]

            ranges.append(
                Range(
                    start=int(
                        video_range["start"] * fps if seconds else video_range["start"]
                    ),
                    end=int(
                        video_range["end"] * fps if seconds else video_range["end"]
                    ),
                )
            )

        # assert that all ranges have a start smaller than the end and that they are within the video
        assert all(
            [
                range.start < range.end
                and range.start <= video_end
                and range.end <= video_end
                for range in ranges
            ]
        )

        video_data.append(VideoData(video_path, ranges, fps, video_end))

    return video_data


def main() -> int:
    print("Loading model...")
    # TODO: unload model on end
    model = BatchYolov8(WEIGHTS, DEVICE, conf_thres=0.5)

    videos = load_video_data()

    for video in videos:
        ground_truth_ranges = [(r.start, r.end) for r in video.ranges]

        frames_with_fish, _ = detection.process_video(
            model=model,
            video_path=video.video_path,
            batch_size=16,
            max_batches_to_queue=4,
            output_path=None,
            # output_path=Path(r"C:\Users\benja\Pictures\test_v2_binary_3.mp4"),
            end_frame=video.video_end,
            stop_event=threading.Event(),
        )

        precision, recall, f1_score = calculate_detection_accuracy(
            frames_with_fish, ground_truth_ranges
        )
        print(video.video_path)
        print(
            f"Detection accuracy: Precision={precision:.2f}, Recall={recall:.2f}, F1-score={f1_score:.2f}"
        )

        predicted_ranges = detected_frames_to_ranges(
            frames_with_fish, frame_buffer=FRAME_BUFFER
        )
        temporal_overlap = calculate_temporal_overlap(
            predicted_ranges, ground_truth_ranges
        )
        print(f"Temporal overlap for video: {temporal_overlap:.2f}")
        # break

    return 0


def main_output_vid() -> int:
    print("Loading model..")
    model = BatchYolov8(WEIGHTS, DEVICE, conf_thres=0.5)

    detection.process_video(
        model=model,
        video_path=Path(
            # r"X:\Myggbukta 2022\MYGGBUKTA2022-[2022-08-13_05-29-48]-025.mp4"
            r"X:\DISK1 - Høyregga 17+18 og myggbukta 2020 mai NTNU\myggbukta 2020 mai\GOPRO 29.05.2020\GH010059.MP4"
        ),
        batch_size=32,
        max_batches_to_queue=4,
        output_path=None,
        stop_event=threading.Event()
        # output_path=Path(r"C:\Users\benja\Pictures\test_5_binary.mp4"),
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
