"""Video processor module. Contains functions for processing videos."""
from typing import List, Tuple
import os
import subprocess
import ffmpeg


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
    # Save the concat filter to a file and run filter_complex_script on that
    command = (
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
    )

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
