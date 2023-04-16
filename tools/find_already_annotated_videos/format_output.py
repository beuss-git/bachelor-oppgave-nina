# pylint: skip-file
# mypy: ignore-errors
import re
from pathlib import Path

with open("annotated_videos.txt", "r") as f:
    annotated_videos = f.readlines()


# Remove duplicates
annotated_videos = list(set(annotated_videos))

print("Found", len(annotated_videos), "annotated videos")

annotated_videos = sorted(annotated_videos)
processed_videos: list[tuple[str, str]] = []
for video in annotated_videos:
    # The string is formated as "video_name path_to_video"
    # We want to split the string at the drive letter
    # There can be spaces in the video name and path
    parts = re.split(r"([A-Za-z]:)", video)
    text_part = parts[0].strip()
    path_part = "".join(parts[1:]).strip()
    # print(f"Text part: {text_part}\nPath part: {path_part}\n")

    path = Path(path_part)

    video_title = path.stem
    video_folder = path.parent
    # Exclude the drive letter
    video_folder = str(video_folder)[3:]

    # print(video, end="")
    # print(video_title + "," + str(video_folder))
    processed_videos += [(video_title, video_folder)]


for (video_title, video_folder) in processed_videos:

    print(video_title + "," + video_folder)
