"""Video processor module. Contains functions for processing videos."""
from typing import List, Tuple
import ffmpeg


def cut_video(
    input_path: str, output_path: str, frame_ranges: List[Tuple[int, int]]
) -> None:
    """Cuts the video to the given frame ranges.

    Args:
        input_path: The path to the input video.
        output_path: The path to the output video.
        frame_ranges: The frame ranges to keep.
    """

    input_file = ffmpeg.input(input_path)
    (
        ffmpeg.concat(
            *[
                input_file.trim(start_frame=start_frame, end_frame=end_frame)
                # Reset the timestamps to avoid freezing on the first frame of the next clip
                # See https://ffmpeg.org/ffmpeg-filters.html#setpts_002c-asetpts
                .filter("setpts", "PTS-STARTPTS")
                for [start_frame, end_frame] in frame_ranges
            ]
        )
        .output(output_path)
        .overwrite_output()
        .run()
    )
