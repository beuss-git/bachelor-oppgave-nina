"""Main module for detection."""
import argparse
import sys
import os
import copy
import time
import math
from typing import List, Optional, Any, Dict
from queue import Queue
from threading import Thread
from tqdm import tqdm
import torch
import numpy as np
from yolov5.utils import dataloaders
from yolov5.models.experimental import attempt_load
from yolov5.utils.augmentations import letterbox
from yolov5.utils.general import check_img_size, non_max_suppression, scale_boxes
from yolov5.utils.torch_utils import select_device


class Yolov5:  # pylint: disable=too-many-instance-attributes
    """Yolov5 class for running inference on images."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        weights_path: str,
        device: str = "",
        img_size: int = 640,
        conf_thres: float = 0.4,
        iou_thres: float = 0.5,
        augment: bool = False,
        agnostic_nms: bool = False,
        classes: Optional[List[str]] = None,
        colors: Optional[List[List[int]]] = None,
    ) -> None:
        try:
            self.device = select_device(device)
        except Exception as err:
            raise RuntimeError("Failed to select device", err) from err

        self.weights_name = os.path.split(weights_path)[-1]

        try:
            self.model = attempt_load(weights_path, device=self.device)
        except Exception as err:
            raise RuntimeError("Failed to load model", err) from err

        self.names = (
            self.model.module.names
            if hasattr(self.model, "module")
            else self.model.names
        )
        if colors is None:
            self.colors = [
                [np.random.randint(0, 255) for _ in range(3)]
                for _ in range(len(self.names))
            ]
        else:
            self.colors = colors
        self.imgsz = check_img_size(img_size, s=self.model.stride.max())
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.augment = augment
        self.agnostic_nms = agnostic_nms
        self.classes = classes
        self.half = self.device.type != "cpu"
        if self.half:
            self.model.half()
        if self.device.type != "cpu":
            self.burn()

        # self.annotation_writer = AnnotationWriter()

    def __str__(self) -> str:
        out = [
            f"Model: {self.weights_name}",
            f"Image size: {self.imgsz}",
            f"Confidence threshold: {self.conf_thres}",
            f"IoU threshold: {self.iou_thres}",
            f"Augment: {self.augment}",
            f"Agnostic nms: {self.agnostic_nms}",
        ]
        if self.classes is not None:
            filter_classes = [self.names[each_class] for each_class in self.classes]
            out.append(f"Classes filter: {filter_classes}")
        out.append(f"Classes: {self.names}")

        return "\n".join(out)

    def burn(self) -> None:
        """Burn in the model for better performance when starting inference."""
        img = torch.zeros(
            (1, 3, self.imgsz, self.imgsz), device=self.device
        )  # init img
        _ = self.model(img.half() if self.half else img)  # run once

    def predict_batch(
        self,
        img0s: List[Any] | np.ndarray[Any, Any],
        max_objects: Optional[Dict[Any, Any]] = None,
    ) -> List[Any]:
        """Predict on a batch of images.

        Args:
            img0s: The list of images to predict on.
            max_objects: Max number of objects to return per image for each class.

        Returns:
            A list of predictions.
        """

        imgs = self.prepare_images(img0s)

        with torch.no_grad():
            # Run model
            inf_out, _ = self.model(
                imgs, augment=self.augment
            )  # inference and training outputs

            # Run NMS
            preds = non_max_suppression(
                inf_out, conf_thres=self.conf_thres, iou_thres=self.iou_thres
            )

        batch_output = []
        for det, img0, img in zip(preds, img0s, imgs):
            if det is not None and len(det):
                det[:, :4] = scale_boxes(img.shape[1:], det[:, :4], img0.shape).round()
            min_max_list = self.min_max_list(det)
            if min_max_list is not None and max_objects is not None:
                min_max_list = self.max_objects_filter(
                    min_max_list, max_objects, name_key="name"
                )

            batch_output.append(min_max_list)

        return batch_output

    def prepare_image(
        self, original_img: np.ndarray[Any, Any] | List[Any]
    ) -> torch.Tensor:
        """Prepare image for inference by normalizing and reshaping.

        Args:
            original_img: The image to prepare.

        Returns:
            The prepared image as a torch tensor.
        """
        new_img = torch.from_numpy(original_img).to(self.device)
        new_img = new_img.half() if self.half else new_img.float()
        new_img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if new_img.ndimension() == 3:
            new_img = new_img.unsqueeze(0)

        return new_img

    def reshape_copy_img(self, img: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        """Reshape and copy image.

        Args:
            img: The image to reshape and copy.

        Returns:
            The reshaped and copied image.
        """
        _img = letterbox(img, new_shape=self.imgsz)[0]
        _img = _img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
        new_img: np.ndarray[Any, Any] = np.ascontiguousarray(_img)  # uint8 to float32
        return new_img

    def prepare_images(
        self, img_s: List[np.ndarray[Any, Any]] | np.ndarray[Any, Any]
    ) -> torch.Tensor:
        """Prepare a batch of images for inference by normalizing and reshaping them.

        Args:
            img_s: The images to prepare.

        Raises:
            RuntimeError: If the type of the images is not supported.

        Returns:
            The prepared images as a torch tensor.
        """
        if isinstance(img_s, list):
            img_list = []
            for img in img_s:
                img_list.append(self.reshape_copy_img(img))
            img_to_send = self.pad_batch_of_images(img_list)
        elif isinstance(img_s, np.ndarray):
            img_to_send = self.reshape_copy_img((np.ndarray(img_s)))
        else:
            print(type(img_s), " is not supported")
            raise RuntimeError("Not supported type")

        return self.prepare_image(img_to_send)

    @staticmethod
    def pad_batch_of_images(
        img_list: List[Any], return_np: bool = True
    ) -> np.ndarray[Any, Any] | List[Any]:
        """Pad a batch of images to the same size.

        Args:
            img_list: The list of images to pad.
            return_np: Whether to return a numpy array or a list of images.

        Returns:
            The padded images as a numpy array or a list of images.
        """
        max_height = 0
        max_width = 0
        padded_img_list = []
        for img in img_list:
            _, height, width = img.shape
            max_height = max(max_height, height)
            max_width = max(max_width, width)

        for img in img_list:
            padded_img = np.full(
                (max_height, max_width, 3), (114, 114, 114), dtype=np.uint8
            )
            padded_img = padded_img.transpose(2, 0, 1)

            _, height, width = img.shape
            offset_width = (max_width - width) // 2
            offset_height = (max_height - height) // 2

            padded_img[
                :,
                offset_height : offset_height + height,
                offset_width : offset_width + width,
            ] = img
            padded_img_list.append(padded_img)

        if return_np:
            return np.array(padded_img_list)
        return padded_img_list

    def min_max_list(self, det: Any) -> Optional[List[Any]]:
        """Create a list of bounding boxes from the detection.

        Args:
            det: The detection.

        Returns:
            The list of bounding boxes.
        """
        min_max_list = []
        if det is not None:
            for i, class_id in enumerate(det[:, -1]):
                obj = {
                    "bndbox": {
                        "xmin": min(int(det[i][0]), int(det[i][2])),
                        "xmax": max(int(det[i][0]), int(det[i][2])),
                        "ymin": min(int(det[i][1]), int(det[i][3])),
                        "ymax": max(int(det[i][1]), int(det[i][3])),
                        "width": max(int(det[i][0]), int(det[i][2]))
                        - min(int(det[i][0]), int(det[i][2])),
                        "height": max(int(det[i][1]), int(det[i][3]))
                        - min(int(det[i][1]), int(det[i][3])),
                    },
                    "name": self.names[int(class_id)],
                    "class_id": int(class_id),
                    "conf": float(det[i][4]),
                    "color": self.colors[int(det[i][5])],
                }
                min_max_list.append(obj)

            return min_max_list

        return None

    @staticmethod
    def max_objects_filter(
        min_max_list: List[Any], max_dict: Dict[Any, Any], name_key: str = "name"
    ) -> List[Any]:
        """Filter a list of bounding boxes based on the maximum number of objects.

        Args:
            min_max_list: The list of bounding boxes.
            max_dict: The maximum number of objects per class.
            name_key: The name key for class names. Defaults to "name".

        Returns:
            The filtered list of bounding boxes.
        """
        filtered_list = []
        max_dict_copy = copy.deepcopy(max_dict)
        for obj in min_max_list:
            if max_dict_copy[obj[name_key]] > 0:
                max_dict_copy[obj[name_key]] -= 1
                filtered_list.append(obj)
            else:
                pass
                # print(f"rejected {obj[by]} conf {obj['conf']}")

        return filtered_list


def create_batches(
    image_list: List[np.ndarray[Any, Any]], batch_size: int = 16
) -> List[List[np.ndarray[Any, Any]]]:
    """Splits a list of images into batches based on batch_size

    Args:
        image_list: The list of images
        batch_size: The batch size. Defaults to 16.

    Returns:
        A list of batches
    """

    batches: List[List[np.ndarray[Any, Any]]] = []
    for i in range(0, len(image_list), batch_size):
        batches.append(image_list[i : i + batch_size])

    return batches


class ThreadedFrameGrabber:
    """Continuously grabs frames from a video in batches and puts them into a queue."""

    def __init__(
        self, input_path: str, batch_size: int = 16, max_batches_to_queue: int = 0
    ):
        """Initialize the BatchFrameGrabber.

        Args:
            input_path: The path to the video.
            batch_size: The batch size. Defaults to 16.
            max_batches_in_queue: The maximum number of batches to queue. Defaults to 0.
        """

        try:
            self.dataset = dataloaders.LoadImages(input_path, img_size=640)
        except Exception as err:
            raise RuntimeError(f"Failed to open {input_path}", err) from err

        self.frame_count = self.dataset.frames
        self.image_list: List[Any] = []
        self.batch_queue: Queue[List[Any]] = Queue(max_batches_to_queue)
        self.batch_size = batch_size

        self.thread = Thread(target=self.__run)
        self.thread.start()

        self.done = False

    def __run(self) -> None:
        """
        This function is run in a separate thread and continuously grabs frames from the video.
        """
        for _, _, im0s, _, _ in self.dataset:
            self.image_list.append(im0s)
            if len(self.image_list) >= self.batch_size:
                self.batch_queue.put(self.image_list)
                self.image_list = []

            # Wait for the queue to have space
            while self.batch_queue.full():
                time.sleep(0.1)
        self.done = True

    def get_next_batch(self) -> Optional[List[np.ndarray[Any, Any]]]:
        """Get the next batch of frames.

        Returns:
            The next batch of frames.
        """
        if not self.batch_queue.empty():
            return self.batch_queue.get()
        return None

    def is_done(self) -> bool:
        """Check if we have processed all frames.

        Returns:
            True if we have processed all frames, False otherwise.
        """
        return self.done

    def total_batch_count(self) -> int:
        """Get the total number of batches that will be processed.

        Returns:
            The total number of batches.
        """
        return int(math.ceil(self.frame_count / self.batch_size))


def process_batch(batch: List[np.ndarray[Any, Any]], model: Yolov5) -> float:
    """Process a batch of frames.

    Args:
        batch: Batch of frames
        model: The Yolov5 model

    Returns:
        The time it took to process the batch.
    """
    start_time = time.time()
    _ = model.predict_batch(batch)
    end_time = time.time()
    delta = end_time - start_time
    return delta


def process_video(
    video_path: str,
    weights_path: str,
    device: str,
    batch_size: int,
    max_batches_to_queue: int,
) -> bool:
    """Runs inference on a video.

    Args:
        video_path: The path to the video to process.
        weights_path: The path to the weights file.
        device: The device to run inference on.
        batch_size: The batch size.
        max_batches_to_queue: The maximum number of batches to queue.

    Returns:
        True if the video was processed successfully, False otherwise.
    """

    try:
        frame_grabber = ThreadedFrameGrabber(
            video_path, batch_size=batch_size, max_batches_to_queue=max_batches_to_queue
        )
    except RuntimeError as err:
        print("Failed to initialize frame grabber", err)
        return False

    try:
        model = Yolov5(weights_path=weights_path, device=device)
    except RuntimeError as err:
        print("Failed to initialize model", err)
        return False

    try:
        total_fps = 0.0

        with tqdm(
            total=frame_grabber.total_batch_count(), desc="Processing batches"
        ) as pbar:
            while not frame_grabber.is_done():
                batch = frame_grabber.get_next_batch()
                if batch is None:
                    # Wait for more batches to be available
                    time.sleep(0.1)
                    continue

                delta = process_batch(batch, model)

                batch_fps = len(batch) / delta
                total_fps += batch_fps
                pbar.update(1)
                pbar.set_description(f"Processing batches (FPS: {batch_fps:.2f})")

        print(f"Average FPS: {total_fps / frame_grabber.total_batch_count()}")
    except RuntimeError as err:
        print(err)
        return False
    return True


def main() -> int:
    """The main function.

    Returns:
        int: The exit code
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--video_path",
        type=str,
        required=True,
        help="The path to the video to process",
    )
    parser.add_argument(
        "--weights_path",
        type=str,
        required=True,
        help="The path to the weights to use",
    )

    parser.add_argument(
        "--device",
        type=str,
        required=False,
        default="cuda:0",
        help="The device to use. Defaults to cuda:0",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        required=False,
        default=32,
        help="The batch size to use. Defaults to 32",
    )

    parser.add_argument(
        "--max_batches_to_queue",
        type=int,
        required=False,
        default=4,
        help="Max number of batches to queue. Defaults to 4",
    )

    args = parser.parse_args()

    if process_video(
        args.video_path,
        args.weights_path,
        args.device,
        args.batch_size,
        args.max_batches_to_queue,
    ):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
