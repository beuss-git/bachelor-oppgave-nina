"""Video processor module. Contains functions for processing videos."""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import ffmpeg

from app.video_processor import Detection


def __run_ffmpeg(
    args: List[str],
    pipe_stdin: bool = False,
    pipe_stdout: bool = False,
    pipe_stderr: bool = False,
    quiet: bool = False,
) -> Tuple[bytes, bytes]:
    stdin_stream = subprocess.PIPE if pipe_stdin else None
    stdout_stream = subprocess.PIPE if pipe_stdout or quiet else None
    stderr_stream = subprocess.PIPE if pipe_stderr or quiet else None
    with subprocess.Popen(
        args, stdin=stdin_stream, stdout=stdout_stream, stderr=stderr_stream
    ) as process:
        out, err = process.communicate()
        retcode = process.poll()
        if retcode:
            raise ffmpeg.Error("ffmpeg", out, err)
    return out, err


def color_to_hex(color: Tuple[int, int, int]) -> str:
    """Converts a color tuple to a hex string."""
    return f"0x{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def draw_detections(
    video_stream: ffmpeg.nodes.Stream,
    detections: Dict[int, List[Detection]],
    start_frame: int,
    end_frame: int,
) -> ffmpeg.nodes.Stream:
    """Draw the detections on the video stream."""
    frame_offset = start_frame
    for frame_number, frame_detections in detections.items():
        # Simplify the above expression
        if start_frame <= frame_number <= end_frame:
            adjusted_frame_number = frame_number - frame_offset
            for detection in frame_detections:
                # NOTE: We round the coordinates and dimensions to the nearest even number to
                #       avoid "flickering" when they are not perfectly aligned with the pixel grid
                x_pos = round(detection.xmin / 2) * 2
                y_pos = round(detection.ymin / 2) * 2
                width = round((detection.xmax - detection.xmin) / 2) * 2
                height = round((detection.ymax - detection.ymin) / 2) * 2

                video_stream = video_stream.drawbox(
                    x=x_pos,
                    y=y_pos,
                    width=width,
                    height=height,
                    color=color_to_hex((255, 105, 180)),
                    thickness=2,
                    enable=f"eq(n,{adjusted_frame_number})",
                ).drawtext(
                    text=f"{detection.label}: {detection.confidence:.2f}",
                    x=detection.xmin + 2,
                    y=detection.ymin + 10,
                    fontsize=12,
                    fontcolor="white",
                    enable=f"eq(n,{adjusted_frame_number})",
                )
    return video_stream


def cut_video(
    input_path: Path,
    output_path: Path,
    frame_ranges: List[Tuple[int, int]],
    predictions: Dict[int, List[Detection]] | None = None,
) -> None:
    """Cuts the video to the given frame ranges.

    Args:
        input_path: The path to the input video.
        output_path: The path to the output video.
        frame_ranges: The frame ranges to keep.
        predictions: The detections to draw on the video. (optional)
    """

    input_file: ffmpeg = ffmpeg.input(str(input_path))

    streams = []

    for start_frame, end_frame in frame_ranges:
        # Trim the video to the frame range
        trimmed_stream = input_file.trim(
            start_frame=start_frame, end_frame=end_frame
        ).filter("setpts", "PTS-STARTPTS")

        if predictions is not None:
            # Draw the detections on the video
            trimmed_stream = draw_detections(
                trimmed_stream, predictions, start_frame, end_frame
            )

        streams.append(trimmed_stream)

    command = ffmpeg.concat(*streams).output(str(output_path)).overwrite_output()

    args = command.compile()

    # NOTE: The filter_complex argument is too long to be passed as a command line argument.
    # ffmpeg-python doesn't support filter_complex_script so we need to manually invoke it.

    # find the index of the -filter_complex argument
    filter_complex_index = args.index("-filter_complex")

    # replace the -filter_complex argument with -filter_complex_script
    args[filter_complex_index] = "-filter_complex_script"

    # write the filter_complex string to a file
    with open("filter_complex.txt", "w", encoding="utf-8") as file:
        file.write(args[filter_complex_index + 1])

    # replace the filter_complex string with the path to the file
    args[filter_complex_index + 1] = "filter_complex.txt"

    # run ffmpeg with the arguments
    __run_ffmpeg(args)

    # Delete the filter_complex file
    os.remove("filter_complex.txt")
