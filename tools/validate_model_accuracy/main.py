# pylint: skip-file
# mypy: ignore-errors
import json
import pickle
import sys
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import Event
from typing import Any, List, Tuple

import cv2
import matplotlib as mpl
import numpy as np
import qdarktheme
from adjustText import adjust_text
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from app.detection import detection
from app.detection.batch_yolov8 import BatchYolov8
from app.widgets.detection_window import DetectionWorker

mpl.rcParams["xtick.labelsize"] = 8
save_weight = True


class ShowFigure(Enum):
    precision_recall_curve = 0
    timeline = 1
    iou_confidence = 2


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


@dataclass
class PrecisionRecallCurve:
    precisions: List[float]
    recalls: List[float]


@dataclass
class IOUThreshold:
    ground_truth_frames: List[Tuple[int, int]]
    predicted_frames: List[Tuple[int, int]]
    temporal_overlaps: List[float]
    average_ious: List[float]


@dataclass
class SaveFile:
    video_names: List[str]
    iou_threshold: IOUThreshold
    pr_curve: PrecisionRecallCurve
    iou_confidence: List[List[Tuple[float, float]]]


@dataclass
class FigureWeightClassifier:
    weight_name: str
    weight_color: str


CURRENT_FIGURE: ShowFigure = ShowFigure.timeline

THRESHOLD = 0.5
WEIGHTS = Path(
    # r"C:\Users\benja\Documents\repos\bachelor-oppgave-nina\runs\detect\train3\weights\best.pt"
    # r"\\wsl.localhost\Ubuntu\home\beuss\dev\train_v8\runs\detect\train9\weights\best.pt"
    r"G:\GITLAB\Bachelor\bachelor-oppgave-nina\data\models\v8s-640-classes-augmented-backgrounds.pt"
)
DEVICE = "cuda:0"
GROUND_TRUTH_VIDEO_DATA = Path(r"ground_truth_data.json")

FRAME_BUFFER = 30


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
    frames_with_fish: List[int],
    ground_truth_ranges: List[Tuple[int, int]],
) -> Tuple[float, float, float]:
    predicted_ranges = detected_frames_to_ranges(
        frames_with_fish, frame_buffer=FRAME_BUFFER
    )
    ground_truth_frames = set(
        [
            frame
            for (start, end) in ground_truth_ranges
            for frame in range(start, end + 1)
        ]
    )
    predicted_frames = set(
        [frame for (start, end) in predicted_ranges for frame in range(start, end + 1)]
    )

    true_positives = len(predicted_frames.intersection(ground_truth_frames))
    false_positives = len(predicted_frames.difference(ground_truth_frames))
    false_negatives = len(ground_truth_frames.difference(predicted_frames))

    """     precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
    ) """
    recall = (true_positives) / (true_positives + false_negatives)
    precision = (true_positives) / (true_positives + false_positives)
    f1_score = (2 * precision * recall) / (precision + recall)

    print(f"precision: {precision}\n recall: {recall}\n f1_score: {f1_score}\n")
    return precision, recall, f1_score


def calculate_temporal_overlap(
    predicted_ranges: List[Tuple[int, int]],
    ground_truth_ranges: List[Tuple[int, int]],
    iou_threshold: float = 0,
    print_ranges=False,
) -> Tuple[float, List[float]]:
    if print_ranges:
        print(f"GR: {len(ground_truth_ranges)}")
        print(f"PR: {len(predicted_ranges)}")
    matched_iou_threshold: List[float] = []

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
            if iou > iou_threshold:
                matched_iou_threshold.append(iou)
                matched_ranges += 1
                break

    if len(ground_truth_ranges) == 0:
        return 1, matched_iou_threshold

    # Returns % of ground truth ranges that were matched
    # TODO: account for too many predicted ranges
    return matched_ranges / len(ground_truth_ranges), matched_iou_threshold


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
            ranges.append(
                Range(
                    start=int(video_range["start"]),
                    end=int(video_range["end"]),
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

    results: List[FigureWeightClassifier] = [
        FigureWeightClassifier("background_results", "r"),
        FigureWeightClassifier("default_aug_results", "g"),
        FigureWeightClassifier("oreskyt_results", "b"),
        FigureWeightClassifier("def_results", "c"),
    ]
    current_weight = results[0]

    save_file: SaveFile = SaveFile(
        [],
        IOUThreshold([], [], [], []),
        PrecisionRecallCurve([], []),
        [],
    )

    file_data: List[Tuple[FigureWeightClassifier, SaveFile]] = []
    if save_weight:
        model = BatchYolov8(
            WEIGHTS,
            DEVICE,
            conf_thres=0.0000001
            if CURRENT_FIGURE == ShowFigure.iou_confidence
            else 0.5,
        )
        videos = load_video_data()

        for video in videos:
            ground_truth_ranges = [(r.start, r.end) for r in video.ranges]

            frames_with_fish, tensor = detection.process_video(
                model=model,
                video_path=video.video_path,
                batch_size=8,
                max_batches_to_queue=3,
                output_path=None,
                # output_path=Path(r"C:\Users\benja\Pictures\test_v2_binary_3.mp4"),
                end_frame=video.video_end,
                stop_event=threading.Event(),
            )

            precision, recall, _ = calculate_detection_accuracy(
                frames_with_fish, ground_truth_ranges
            )

            print(video.video_path)

            predicted_ranges = detected_frames_to_ranges(
                frames_with_fish, frame_buffer=FRAME_BUFFER
            )
            temporal_overlap, matched_iou = calculate_temporal_overlap(
                predicted_ranges, ground_truth_ranges, print_ranges=True
            )
            """  iou_thresholds = sum(
              [
                  (
                      sum(
                          [],
                          [
                              matched_iou,
                          ],
                      )
                  ),
                  iou_thresholds,
              ],
              [],
          ) """
            save_file.iou_confidence.append(
                get_confidence_iou(ground_truth_ranges, tensor)
            )
            save_file.video_names.append(video.video_path.stem)
            save_file.pr_curve.precisions.append(precision)
            save_file.pr_curve.recalls.append(recall)
            save_file.iou_threshold.average_ious.append(
                sum(matched_iou) / len(matched_iou) if len(matched_iou) > 0 else 0
            )
            save_file.iou_threshold.temporal_overlaps.append(temporal_overlap)
            save_file.iou_threshold.predicted_frames.append(predicted_ranges)
            save_file.iou_threshold.ground_truth_frames.append(ground_truth_ranges)

            print(f"Temporal overlap for video: {temporal_overlap:.2f}")

            # break

            # save_weight = False

        with open(current_weight.weight_name, "wb") as file:
            pickle.dump(save_file, file)

    for item in results:
        if item == current_weight:
            with open(item.weight_name, "rb") as file:
                file_data.append((item, pickle.load(file)))

    class MyWindow(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            self.setLayout(layout)

            canvas = FigureCanvas(fig)  # create canvas
            layout.addWidget(canvas)  # add canvas to layout

    match CURRENT_FIGURE:
        case ShowFigure.precision_recall_curve:
            fig = Figure(linewidth=15)
            ground_t_ax = fig.add_subplot()
            ground_t_ax.grid(which="both", axis="both", alpha=0.5)
            ground_t_ax.set_ylabel("Precision")
            ground_t_ax.set_xlabel("Recall")
            ground_t_ax.set_title("Precision-Recall Curve")
            texts = []

            for fwc, file in file_data:
                prc = file.pr_curve
                loaded_recalls = prc.recalls
                loaded_precisions = prc.precisions
                loaded_video_names = file.video_names
                ground_t_ax.scatter(
                    loaded_recalls, loaded_precisions, s=20, c=fwc.weight_color
                )
                # print(f"{average_iou_thresholds}\n{precisions}")
                for x, y, s in zip(
                    loaded_recalls, loaded_precisions, loaded_video_names
                ):
                    texts.append(
                        ground_t_ax.text(
                            x,
                            y,
                            s,
                            fontsize=5,
                            color=fwc.weight_color,
                        )
                    )

            adjust_text(
                texts,
                arrowprops=dict(arrowstyle="->", color=fwc.weight_color, lw=0.5),
            )
            ground_t_ax.legend()
        case ShowFigure.timeline:
            for fwc, file in file_data:
                fig = Figure(linewidth=3)
                fig.set_figheight(2)
                fig.set_figwidth(16)
                fig.subplots_adjust(bottom=0.4)
                ground_t_ax = fig.add_subplot()
                pred_ax = fig.add_axes(ground_t_ax.get_position(), frameon=False)
                print("showing timeline")
                ground_t_ax.set_title("Threshold")
                ground_t_ax.set_xlabel("\nIOU threshold (showing frames)", labelpad=3)
                ground_t_ax.invert_yaxis
                pred_ax.invert_yaxis
                ground_t_ax.yaxis.set_visible(False)
                pred_ax.yaxis.set_visible(False)
                frame_ranges = (
                    file.iou_threshold.ground_truth_frames
                    + file.iou_threshold.predicted_frames
                )

                all_frame_ranges = frame_ranges[0].copy()

                for coords in frame_ranges[1]:
                    all_frame_ranges.append(coords)

                (start_val, end_val) = (0, 0)
                for start, end in all_frame_ranges:
                    start_val = start if start < start_val else start_val
                    end_val = end if end > end_val else end_val

                g_t_begin = np.array([x for (x, _) in frame_ranges[0]])
                g_t_end = np.array([y for (_, y) in frame_ranges[0]])
                p_f_begin = np.array([x for (x, _) in frame_ranges[1]])
                p_f_end = np.array([y for (_, y) in frame_ranges[1]])
                gt_color = ("c", 0.8)
                pf_color = ("y", 0.6)
                pred_ax.barh(
                    1,
                    p_f_end - p_f_begin,
                    left=p_f_begin,
                    alpha=pf_color[1],
                    color=pf_color[0],
                )
                ground_t_ax.barh(
                    1,
                    g_t_end - g_t_begin,
                    left=g_t_begin,
                    alpha=gt_color[1],
                    color=gt_color[0],
                )
                pred_ax.set_xlim(start_val, end_val)
                ground_t_ax.set_xlim(start_val, end_val)
                gt = np.unique(np.concatenate((g_t_begin, g_t_end)))
                pf = np.unique(np.concatenate((p_f_begin, p_f_end)))

                ground_t_ax.set_xticks(gt)
                ground_t_ax.set_xticklabels(gt, color=gt_color[0])
                pred_ax.set_xticks(pf)
                pred_ax.set_xticklabels(pf, color=pf_color[0])
                pred_ax.set_xticklabels(
                    [
                        label.get_text() if i % 2 != 0 else "|\n" + label.get_text()
                        for i, label in enumerate(pred_ax.xaxis.get_majorticklabels())
                    ]
                )
                ground_t_ax.set_xticklabels(
                    [
                        label.get_text() if i % 2 != 0 else "|\n" + label.get_text()
                        for i, label in enumerate(
                            ground_t_ax.xaxis.get_majorticklabels()
                        )
                    ]
                )
                pred_ax.set_xticklabels(
                    [
                        label.get_text() if i % 1 != 0 else "|\n" + label.get_text()
                        for i, label in enumerate(pred_ax.xaxis.get_majorticklabels())
                    ]
                )
        case ShowFigure.iou_confidence:
            for fwc, file in file_data:
                conf: List[float] = []
                all_iou: List[List[float]] = []

                for iou_conf in (videos := file.iou_confidence):
                    conf = [x for (x, _) in iou_conf]
                    iou = [y for (_, y) in iou_conf]
                    all_iou.append(iou)
                average_iou = []
                for i in range(0, len(conf)):
                    append_iou = []
                    for iou in all_iou:
                        append_iou.append(iou[i])
                    average_iou.append((sum(append_iou) / len(append_iou)))

                """ for i in range(0, len(all_conf)): """
                fig = Figure(linewidth=15)

                ax = fig.add_subplot()
                ax.set_title("Average IOU- Confidence curve")
                ax.plot(conf, average_iou, color="purple")
                ax.set_xlabel("Confidence")
                ax.set_ylabel("Average IOU")
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    window = MyWindow()
    window.show()
    return app.exec()


def get_confidence_iou(
    ground_truth_ranges: List[Tuple[int, int]], tensor: List[Any]
) -> list[Tuple[float, float]]:
    predictions = DetectionWorker.tensors_to_predictions(tensor)
    plotted_confidence_iou: List[Tuple[float, float]] = []
    for num in range(0, 10):
        i = num / 10
        frames_with_fish_conf = []
        for frame, prediction in predictions.items():
            for detection in prediction:
                if detection.confidence > (i):
                    frames_with_fish_conf.append(frame)
        predicted_ranges = detected_frames_to_ranges(
            frames_with_fish_conf, frame_buffer=FRAME_BUFFER
        )
        _, matched_iou = calculate_temporal_overlap(
            predicted_ranges, ground_truth_ranges
        )
        plotted_confidence_iou.append(
            (
                i,
                sum(matched_iou) / len(matched_iou)
                if len(matched_iou) > 0
                else float(0),
            )
        )
    return plotted_confidence_iou


def main_output_vid() -> int:
    print("Loading model..")
    model = BatchYolov8(WEIGHTS, DEVICE, conf_thres=0.5)

    detection.process_video(
        model=model,
        video_path=Path(
            # r"X:\Myggbukta 2022\MYGGBUKTA2022-[2022-08-13_05-29-48]-025.mp4"
            r"X:\DISK1 - Høyregga 17+18 og myggbukta 2020 mai NTNU\myggbukta 2020 mai\GOPRO 29.05.2020\GH010059.MP4"
        ),
        batch_size=16,
        max_batches_to_queue=4,
        # output_path=None,
        stop_event=threading.Event(),
        output_path=Path(r"C:\Users\Daniel Hao\Pictures\test_5_binary.mp4"),
        # end_frame=,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
