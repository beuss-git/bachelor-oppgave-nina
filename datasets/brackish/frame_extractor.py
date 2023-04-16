"""Takes a set of videos and extracts the frames into separate folders"""
import argparse
import os
import pathlib
import subprocess
import typing

image_types = [".png", ".jpg", ".jpeg"]
video_types = [".avi", ".mp4"]


def extract_frames(parsed_args: dict[str, typing.Any]) -> None:
    """
    Takes a set of videos and extracts the frames into separate folders
    Args:
        parsed_args:
    """
    main_dir = parsed_args["inputFolder"]
    output_dir = parsed_args["outputFolder"]

    for sub_dir, _, files in os.walk(main_dir):
        for filename in files:
            if os.path.splitext(filename)[1].lower() in video_types:
                video_file = os.path.join(os.path.abspath(sub_dir), filename)

                if output_dir != "":
                    file_folder = output_dir
                else:
                    file_folder = os.path.splitext(video_file)[0]
                pathlib.Path(os.path.abspath(file_folder)).mkdir(
                    exist_ok=True, parents=True
                )

                fileprefix = os.path.join(file_folder, os.path.splitext(filename)[0])

                cmd_command = [
                    "ffmpeg",
                    "-i",
                    video_file,
                    "-vf",
                    "scale=960:540",
                    "-sws_flags",
                    "bicubic",
                    f"{fileprefix}-%04d.png",
                    "-hide_banner",
                ]

                subprocess.call(cmd_command)

                # Create a .txt file with the names of all the image files in the respective folder
                dir_content = os.listdir(file_folder)
                for inner_filename in dir_content:
                    if os.path.splitext(inner_filename)[1] in image_types:
                        with open(
                            f"{os.path.join(file_folder, 'inputList.txt')}",
                            "a",
                            encoding="UTF-8",
                        ) as file:
                            file.write(f"{inner_filename}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Takes a set of videos and extracts the frames into separate folders"
    )
    ap.add_argument(
        "-in",
        "--inputFolder",
        type=str,
        required=True,
        help="Path to the main folder containing all the videos",
    )
    ap.add_argument(
        "-out",
        "--outputFolder",
        type=str,
        required=False,
        help="Path the image output folder. NOTE: if no outputfolder argument is provided, "
        "the images will be placed in folders corresponding to their respective video-names; "
        "if an argument IS given, all images will be placed in a folder with the provided "
        "argument name.",
        default="",
    )

    args = vars(ap.parse_args())

    extract_frames(args)
