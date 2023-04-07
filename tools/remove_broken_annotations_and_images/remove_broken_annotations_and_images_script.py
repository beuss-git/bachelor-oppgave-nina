"""This a script meant to remove broken annotations and images from given paths"""
import copy
import json
import os
from typing import Any

COCO_PATH = "COCO_DEFAULT"  # which path to use for dataset fix

FILES = [
    r"instances_default.json",  # which file names to look for
    r"image_info_default.json",
    r"panoptic_default.json",
]

DATASET = {
    "COCO_DEFAULT": [  # default coco dataset paths for lookup
        # image path
        r"D:\\Annotation\\nin_dataset_coco\\images\\default\\",
        # original instances (pref for annotations)
        r"G:\\GITLAB\\Bachelor\\datasetfix\\dataset_default\\",
    ],
    "COCO_BROKEN": [  # broken coco dataset paths for lookup
        # image path
        r"D:\\Annotation\\dataset_coco -- broken\\images\\default\\",
        # original instances (pref for annotations)
        r"G:\\GITLAB\\Bachelor\\datasetfix\\dataset_broken\\",
    ],
}
IMG_PATH = DATASET[COCO_PATH][0]
ANNO_PATH = DATASET[COCO_PATH][1]


def remove_img_annot(
    inn: dict[Any, Any], size_img_new: int, size_anno_new: int
) -> tuple[dict[Any, Any], int, int]:
    """removes broken images and their linked annotations

    Args:
        inn (dict): dictionary of images to query
        size_img_new (int): returns new size of image amount stored
        size_anno_new (int):  returns new size of annotation amount stored

    Returns:
        dict: _description_
    """
    print("removing bad images and linked annotations...")
    remove_img = []
    for index in inn["images"]:
        if index["file_name"] not in entries:
            id_list.append(index["id"])
            remove_img.append(index)

    inn["images"] = [i for i in inn["images"] if i not in remove_img]

    remove_anno = []
    for index in inn["annotations"]:
        if index["image_id"] in id_list:
            remove_anno.append(index)

    inn["annotations"] = [i for i in inn["annotations"] if i not in remove_anno]
    size_img_new += len(inn["images"])
    size_anno_new += len(inn["annotations"])
    print("done!\n")
    return inn, size_img_new, size_anno_new


id_list: list[int] = []  # init list for storing image_id's
old_size_img, old_size_anno = 0, 0
new_size_img, new_size_anno = 0, 0
new_data = {}
entries = os.listdir(IMG_PATH)
for i in FILES:
    with open(ANNO_PATH + i, encoding="utf-8") as f:
        print(f"Loading Annotations for {i}...")
        data = json.load(f)
        old_size_img += len(data["images"])
        old_size_anno += len(data["annotations"])
        new_data[i] = copy.deepcopy(data)
        f.close()
        print("done!\n")

for i in FILES:  # removes broken images and annotations
    (new_data[i], new_size_img, new_size_anno) = remove_img_annot(
        new_data[i], new_size_img, new_size_anno
    )

for i in FILES:  # creates new files
    print(f"Creating new {i} file...")
    json_object = json.dumps(new_data[i])
    with open(
        __file__[: __file__.rindex("\\") + 1] + i, "w", encoding="utf-8"
    ) as outfile:
        outfile.write(json_object)
    print("done!\n")

print(  # prints out information about sizes
    f"({old_size_img}, {old_size_anno}) = {(v := old_size_img+old_size_anno)}"
    + f"  -> ({new_size_img}, {new_size_anno})"
    + f"\n = {(v := new_size_img+new_size_anno)} "
)
