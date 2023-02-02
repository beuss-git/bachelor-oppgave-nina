"""
Takes an imagelist as input and splits it into training/validation/test splits,
according to the provided percentages.
Outputs separate txt files for each split containing the image paths to the images in the splits.
"""
import argparse
import typing
import numpy as np


def create_dataset_split(parsed_args: dict[str, typing.Any]) -> None:
    """
    Takes an imagelist as input and splits it into training/validation/test splits,
     according to the provided percentages.
    Outputs separate txt files for each split containing
     the image paths to the images in the splits.

    Input:
        args: Dict containing the following elements
            - inputFile: Path to the input imagelist
            - seed: Seed for the numpy random number generator
            - trnSplit: Percentage of data used for training set (value between 0 and 1)
            - valSplit: Percentage of data used for validation set (value between 0 and 1)
            - tstSplit: Percentage of data used for test set (value between 0 and 1)
    """

    # Set Numpy RNG if seed is provided
    if parsed_args["seed"]:
        np.random.seed(parsed_args["seed"])

    # Read data split values
    trn_split = parsed_args["trnSplit"]
    val_split = parsed_args["valSplit"]
    tst_split = parsed_args["tstSplit"]

    # Check that the data_splits actually add up to 1.0
    data_split_sum = trn_split + val_split + tst_split
    assert data_split_sum == 1.0, f"INVALID DATA SPLIT, {data_split_sum}"

    # Read input imagelist
    with open(parsed_args["inputFile"], "r", encoding="UTF-8") as text_file:
        filenames = text_file.read().split("\n")

    # Remove empty line in the end of imagelist file if present
    if filenames[-1] == "":
        filenames = filenames[:-1]
    number_of_files = len(filenames)

    # Check that there are no duplicate frames
    assert number_of_files == len(
        set(filenames)
    ), "Dublicate filenames in the provided imagelist"

    filenames_arr = np.asarray(filenames)

    # Randomize the files, without replacement
    indecies = list(np.random.choice(number_of_files, number_of_files, replace=False))

    # Check that there are no duplicate indecies
    assert number_of_files == len(set(indecies)), "Dublicate indecies generated"

    # Determine the amount of iamge for each split
    trn_amount = int(number_of_files * trn_split)
    val_amount = int(number_of_files * val_split)
    tst_amount = number_of_files - trn_amount - val_amount

    print(f"Trn: {trn_amount}\nVal: {val_amount}\nTst: {tst_amount}")

    # Save the filenames for each split into txt files

    with open("train.txt", "w", encoding="UTF-8") as file:
        for ind in indecies[:trn_amount]:
            file.write(f"{filenames_arr[ind]}\n")

    with open("valid.txt", "w", encoding="UTF-8") as file:
        for ind in indecies[trn_amount : trn_amount + val_amount]:
            file.write(f"{filenames_arr[ind]}\n")

    with open("test.txt", "w", encoding="UTF-8") as file:
        for ind in indecies[trn_amount + val_amount :]:
            file.write(f"{filenames_arr[ind]}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Takes a an annotation csv file and analyze it"
    )
    ap.add_argument(
        "-inputFile",
        "--inputFile",
        type=str,
        default="imagelist.txt",
        help="Path to the image list file",
    )
    ap.add_argument(
        "-seed", "--seed", type=int, default=1234567890, help="Seed for the numpy RNG"
    )
    ap.add_argument(
        "-trnSplit",
        "--trnSplit",
        type=float,
        default=0.8,
        help="Percentage of data used for training. Should be between 0 and 1",
    )
    ap.add_argument(
        "-valSplit",
        "--valSplit",
        type=float,
        default=0.1,
        help="Percentage of data used for validation. Should be between 0 and 1",
    )
    ap.add_argument(
        "-tstSplit",
        "--tstSplit",
        type=float,
        default=0.1,
        help="Percentage of data used for testing. Should be between 0 and 1",
    )

    args = vars(ap.parse_args())

    create_dataset_split(args)
