import argparse
import os
import typing
import pathlib


def create_image_list(args: dict[str, typing.Any]) -> None:
    root_dir = args["inputFolder"]
    output_dir = os.path.abspath(args["outputFolder"])
    # Create output dir if it doesn't exist
    pathlib.Path(output_dir).mkdir(exist_ok=True, parents=True)

    (_, _, curr_txt_files) = next(os.walk(output_dir))

    for _, _, files in os.walk(root_dir):
        for filename in files:
            filename_parts = os.path.splitext(filename)
            if filename_parts[-1] == ".png":
                txt_file = os.path.join(output_dir, filename_parts[0] + ".txt")

                if os.path.basename(txt_file) not in curr_txt_files:
                    with open(txt_file, "w", encoding="UTF-8"):
                        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Creates empty YOLO detection files for frames with no detections in it"
    )
    ap.add_argument(
        "-inputFolder",
        "--inputFolder",
        type=str,
        help="Path to the main folder holding all images",
    )
    ap.add_argument(
        "-outputFolder",
        "--outputFolder",
        type=str,
        help="Path to the output folder for the yolo .txt files",
    )

    args = vars(ap.parse_args())

    create_image_list(args)
