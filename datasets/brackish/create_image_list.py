"""Takes a path to an image folder and saves all absolute paths as separate lines in a txt file"""
import argparse
import os
import typing


def create_image_list(parsed_args: dict[str, typing.Any]) -> None:
    """
    Takes a path to an image folder and saves all absolute paths as separate lines in a txt file

    Input:
        args: Dict containing the following elements
            - inputFolder: Path to the input image folder
            - outputFile: Filepath to the output imagelist file
    """

    rootdir = parsed_args["inputFolder"]
    with open(parsed_args["outputFile"], "w", encoding="UTF-8") as file:
        for root, _, files in os.walk(rootdir):
            for filename in files:
                if os.path.splitext(filename)[-1] == ".png":
                    file.write(f"{os.path.join(os.path.abspath(root), filename)}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Takes a set root dir and creates a list of all images in this dir. Writing "
                    "with absolute path "
    )
    ap.add_argument(
        "-inputFolder",
        "--inputFolder",
        type=str,
        default="",
        help="Path to the main folder holding all images",
    )
    ap.add_argument(
        "-outputFile",
        "--outputFile",
        type=str,
        default="imagelist.txt",
        help="Path to the output file",
    )

    args = vars(ap.parse_args())

    create_image_list(args)
