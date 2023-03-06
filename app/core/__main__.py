"""Video Processor main"""
import sys
import logging

from pathlib import Path
from .core import Core


def main() -> int:
    """Main entry point for the application script"""
    logger = logging.getLogger(__name__)

    try:
        input_path = (
            r"C:\Users\Lars\Documents\NTNU\Semester-6\test-videos\myggbuktav2.mp4"
        )
        # output_path = r"C:\Users\Lars\Documents\NTNU\Semester-6\test-videos\myggbukta_cut.mp4"
        core = Core(
            device="cuda:0",
            weights_path=Path(
                r"C:\Users\Lars\Documents\NTNU\Semester-6\test-videos\yolov8s.pt"
            ),
        )
        core.process_video(Path(input_path))
        # cut_video(input_path, output_path, [(0, 10), (20, 30), (40, 50)])
    except RuntimeError as err:
        logger.error("Failed to process video, could not find input path", exc_info=err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
