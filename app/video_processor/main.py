"""video_processor"""
from .video_processor import cut_video


def main() -> int:
    """Main entry point for the application script"""
    input_path = r"C:\Users\benja\Pictures\myggbukta.mp4"
    output_path = r"C:\Users\benja\Pictures\myggbukta_cut.mp4"
    cut_video(input_path, output_path, [(0, 10), (20, 30), (40, 50)])
    return 0
