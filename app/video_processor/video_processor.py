"""Video processor module. Contains functions for processing videos."""
from pathlib import Path
from typing import Any, Dict, List, Tuple

import av
import av.datasets
import av.packet
import av.video
import cv2
import numpy as np
from tqdm import tqdm

from app.logger import get_logger
from app.video_processor import Detection

logger = get_logger()


def color_to_hex(color: Tuple[int, int, int]) -> str:
    """Converts a color tuple to a hex string."""
    return f"0x{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def draw_detections(
    frame: np.ndarray[Any, Any], detections: List[Detection]
) -> np.ndarray[Any, Any]:
    """
    Draws bounding boxes and labels on a frame for the specified detections.

    Args:
        frame: The frame to draw on.
        detections: A list of detections to draw.

    Returns:
        The frame with bounding boxes and labels drawn on it.
    """
    for detection in detections:
        x_pos = round(detection.xmin / 2) * 2
        y_pos = round(detection.ymin / 2) * 2
        width = round((detection.xmax - detection.xmin) / 2) * 2
        height = round((detection.ymax - detection.ymin) / 2) * 2

        cv2.rectangle(
            frame, (x_pos, y_pos), (x_pos + width, y_pos + height), (255, 0, 0), 2
        )

        text = f"{detection.label}: {detection.confidence:.2f}"
        (text_width, text_height), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        cv2.rectangle(
            frame,
            (x_pos, y_pos - text_height - 2),
            (x_pos + text_width, y_pos),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            frame,
            text,
            (x_pos, y_pos - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    return frame


def frame_to_timestamp(frame: int, video_stream: av.video.stream) -> int:
    """
    Convert a frame number to a timestamp using the time base and frame rate of a video stream.

    Args:
        frame (int): The frame number.
        video_stream (av.video.stream): The input video stream.

    Returns:
        int: The timestamp in microseconds.
    """
    return int((frame * av.time_base) / video_stream.average_rate)


def timestamp_to_frame(timestamp: float, video_stream: av.video.stream) -> int:
    """
    Convert a timestamp to a frame number using the time base and frame rate of a video stream.

    Args:
        timestamp (float): The timestamp in microseconds.
        video_stream (av.video.stream): The input video stream.

    Returns:
        int: The frame number.
    """
    return int(
        (timestamp - video_stream.start_time)
        * float(video_stream.time_base)
        * float(video_stream.average_rate)
    )


def process_packet(  # pylint: disable=too-many-arguments
    packet: av.packet,
    current_frame: int | None,
    start: int,
    end: int,
    video_stream: av.video.stream,
    output_container: av.container.output,
    output_stream: av.video.stream,
    predictions: Dict[int, List[Detection]] | None,
    pbar: tqdm,
) -> Tuple[int, bool]:
    """
    Process a packet of video frames, encode the frames,
    and mux the resulting packets into an output container.

    Args:
        packet (av.packet): The input packet of video frames.
        current_frame (int | None): The current frame number.
        start (int): The starting frame number for the segment.
        end (int): The ending frame number for the segment.
        video_stream (av.video.stream): The input video stream.
        output_container (av.container.output): The output container.
        output_stream (av.video.stream): The output video stream.
        predictions (Dict[int, List[Detection]] | None): Optional detections for each frame.
        pbar (tqdm): A progress bar to update.

    Returns:
        Tuple[int, bool]: The current frame number and a flag indicating
                          whether processing should continue.
    """
    for frame in packet.decode():
        if current_frame is None:
            current_frame = timestamp_to_frame(frame.pts, video_stream)
        else:
            current_frame += 1

        if current_frame > end:
            return current_frame, False

        if current_frame >= start:
            frame_image = frame.to_ndarray(format="bgr24")

            if predictions is not None:
                frame_detections = predictions.get(current_frame, [])
                frame_image = draw_detections(frame_image, frame_detections)

            output_frame = av.VideoFrame.from_ndarray(frame_image, format="bgr24")

            packet = output_stream.encode(output_frame)
            if packet is not None:
                output_container.mux(packet)
                pbar.update(1)

    if current_frame is None:
        return 0, True

    return int(current_frame), True


def process_frame_ranges(  # pylint: disable=too-many-arguments
    frame_ranges: List[Tuple[int, int]],
    input_container: av.container.input,
    video_stream: av.video.stream,
    output_container: av.container.output,
    output_stream: av.video.stream,
    predictions: Dict[int, List[Detection]] | None,
) -> None:
    """
    Process a list of frame ranges, seek to the appropriate timestamps,
    and process each packet of video frames.

    Args:
        frame_ranges (List[Tuple[int, int]]): A list of (start, end) frame ranges.
        input_container (av.container.input): The input container.
        video_stream (av.video.stream): The input video stream.
        output_container (av.container.output): The output container.
        output_stream (av.video.stream): The output video stream.
        predictions (Dict[int, List[Detection]] | None): Optional detections for each frame.
    """
    with tqdm(
        total=sum(end - start for start, end in frame_ranges), desc="Processing frames"
    ) as pbar:
        for start, end in frame_ranges:
            timestamp = frame_to_timestamp(start, video_stream)
            input_container.seek(timestamp)

            current_frame = None
            for packet in input_container.demux(video_stream):
                current_frame, continue_processing = process_packet(
                    packet,
                    current_frame,
                    start,
                    end,
                    video_stream,
                    output_container,
                    output_stream,
                    predictions,
                    pbar,
                )
                if not continue_processing:
                    break


def cut_video(
    input_path: Path,
    output_path: Path,
    frame_ranges: List[Tuple[int, int]],
    predictions: Dict[int, List[Detection]] | None = None,
) -> None:
    """
    Cut a video into segments specified by a list of frame ranges,
    and optionally annotate the frames with detections.

    Args:
        input_path (Path): The path to the input video file.
        output_path (Path): The path to the output video file.
        frame_ranges (List[Tuple[int, int]]): A list of (start, end) frame ranges.
        predictions (Dict[int, List[Detection]] | None, optional):
            A dictionary mapping frame numbers to lists of Detection objects. Defaults to None.

    Raises:
        FileNotFoundError: If the input file does not exist.
        av.AVError: If there is an error opening or processing the input file,
                    or encoding/muxing the output file.

    Returns:
        None
    """
    input_container = av.open(str(input_path))
    video_stream = input_container.streams.video[0]
    video_stream.thread_type = "AUTO"

    output_container = av.open(str(output_path), mode="w")
    codec_name = video_stream.codec_context.name
    fps = video_stream.average_rate.numerator / video_stream.average_rate.denominator
    output_stream = output_container.add_stream(codec_name, str(fps))
    output_stream.width = video_stream.codec_context.width
    output_stream.height = video_stream.codec_context.height
    output_stream.pix_fmt = video_stream.codec_context.pix_fmt

    process_frame_ranges(
        frame_ranges,
        input_container,
        video_stream,
        output_container,
        output_stream,
        predictions,
    )

    packet = output_stream.encode(None)
    if packet is not None:
        output_container.mux(packet)

    output_container.close()
    input_container.close()
