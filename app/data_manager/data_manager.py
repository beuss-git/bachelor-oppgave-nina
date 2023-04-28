"""Stores data about video and detections in local database"""
import datetime
import os
import sqlite3
import sys
import traceback
import typing
from pathlib import Path
from types import TracebackType
from typing import Type

import ffmpeg

from app.logger import get_logger

logger = get_logger()


class DataManager:
    """Class for interacting with local sqlite database"""

    def __init__(self) -> None:
        """establishes the connection with local sqlite database"""

        try:
            # Creates a connection with the db file
            self.sqlite_connection = sqlite3.connect("SQLite_Python.db")
            print("Successfully Connected to SQLite")

            table_exists = self.tables_check()

            if table_exists:
                self.create_tables()

        except sqlite3.Error as error:
            # If error occurs log the error
            print("Error while connecting to sqlite", error)

    def __enter__(self) -> "DataManager":
        """Returns the data manager object"""
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,  # pylint: disable=unused-argument
        exc_value: BaseException | None,  # pylint: disable=unused-argument
        trace_back: TracebackType | None,  # pylint: disable=unused-argument
    ) -> None:
        """Closes the connection with the database"""
        if self.sqlite_connection:
            self.sqlite_connection.close()

    def tables_check(self) -> bool:
        """Checking if tables aleady exist in the database

        Returns:
            bool: Returns true if there is no tables in the database
        """
        try:
            # creates a cursor
            cursor = self.sqlite_connection.cursor()

            # checks if there are tables in the database
            list_of_tables = cursor.execute(
                """SELECT name FROM sqlite_master WHERE type='table'
            AND name IN ('video', 'detection'); """
            ).fetchall()

            # returns true if there isnt any tables found in the database
            if list_of_tables == []:
                print("Tables not found!")
                return True

            print("Tables found!")
            cursor.close()
            return False

        except sqlite3.Error as error:
            # Log error if anything fails in the process
            print("Error while checking for sqlite table", error)
            return False

    def create_tables(self) -> None:
        """creates tables in the database based on the sqlite_tables file"""

        try:
            # creates a cursor
            cursor = self.sqlite_connection.cursor()

            # opens the sql file with the tables that are going to be created
            with open(
                "app/data_manager/sqlite_tables.sql",
                "r",
                encoding="ascii",
                errors="ignore",
            ) as sqlite_file:
                sql_script = sqlite_file.read()

            # executes the sql script to create the tables
            cursor.executescript(sql_script)
            print("SQLite script executed successfully")
            cursor.close()

        except sqlite3.Error as error:
            # Log error if anything fails in the process
            print("Error while creating a sqlite table", error)

    def add_video_data(
        self, video_id: Path | None, title: str, output_video: Path | None
    ) -> None:
        """Adds a video into the video table

        Args:
            video_id (Path | None): The path of the video
            title (str): Filename of video
            output_video (Path | None): The path of the output video
        """

        try:
            # creates cursor
            cursor = self.sqlite_connection.cursor()

            if video_id is None:
                return

            if output_video is None:
                return

            video_exist = self.video_check(str(video_id))
            if video_exist:
                # sets up query and data that will be in the query
                sqlite_insert_query = """INSERT INTO video
                            (id, title, date, totaldetections, videolength, outputvideolength)
                            VALUES  (?, ?, ?, ?, ?, ?)"""
                data = (
                    str(video_id),
                    title,
                    datetime.datetime.fromtimestamp(
                        os.path.getctime(video_id)
                    ).strftime("%Y-%m-%d"),
                    0,
                    self.get_video_duration(video_id),
                    self.get_video_duration(
                        output_video / f"{video_id.stem}_processed.mp4"
                    ),
                )
                #
                # executes query to add the data into the table
                cursor.execute(sqlite_insert_query, data)
                self.sqlite_connection.commit()
                logger.info(
                    "Record inserted successfully into table at %s", cursor.rowcount
                )
            cursor.close()

        except sqlite3.Error as error:
            # If error occurs log the error
            logger.error("Failed to insert data into sqlite table")
            logger.error("Exception class is: %s", error.__class__)
            logger.error("Exception is %s", error.args)
            logger.error("Printing detailed SQLite exception traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            logger.error(traceback.format_exception(exc_type, exc_value, exc_tb))

    def video_check(self, video_id: str) -> bool:
        """Checks if a video already exists within the database"""
        try:
            # creates a cursor
            cursor = self.sqlite_connection.cursor()

            # checks if there are tables in the database
            video = cursor.execute(
                """SELECT title FROM video WHERE id='""" + video_id + """'; """
            ).fetchall()

            # returns true if there isnt any tables found in the database
            if video == []:
                print("Video not found!")
                return True

            print("Video already exists in database!")
            cursor.close()
            return False

        except sqlite3.Error as error:
            # Log error if anything fails in the process
            print("Error while checking for sqlite table", error)
            return False

    def get_video_duration(self, path: Path | None) -> str:
        """Returns the duration of a video based on metadata

        Args:
            path (Path | None): path to the video

        Returns:
            str: string with duration in the format HH:MM:SS
        """

        duration = "00:00:00"
        if path is not None:
            # gets videolength from metadata
            metadata = self.get_metadata(path)
            if metadata is not None:
                duration = str(datetime.timedelta(seconds=float(metadata["duration"])))
                # .strftime("%H:%M:%S")
        return duration

    def add_detection_data(
        self, video_id: Path, detections: typing.List[typing.Tuple[int, int]]
    ) -> None:
        """Adds data about detections for one video

        Args:
            video_id (int): Unique id of the video for foreign key
            detections (List[Tuple[str, str]]): list of fish detections represented as a
                                                tuple with start frame and end frame

        """
        try:
            # create a cursor
            cursor = self.sqlite_connection.cursor()

            # sets up query
            sqlite_insert_query = """INSERT INTO detection
                          (videoid, starttime, endtime)
                          VALUES (?, ?, ?);"""

            timestamped_detections = self.get_timestamps(video_id, detections)

            # Setting up list of detections with video id and detection id
            detections_list: typing.List[typing.Tuple[str, str, str]] = []
            for detection in timestamped_detections:
                detections_list.append((str(video_id),) + detection)

            # execute query to add data to table
            cursor.executemany(sqlite_insert_query, detections_list)
            self.sqlite_connection.commit()
            print(
                "Total",
                cursor.rowcount,
                "Records inserted successfully into detection table",
            )
            cursor.close()

        except sqlite3.Error as error:
            # If error occurs log the error
            print("Failed to insert multiple records into sqlite table", error)

    def get_video_data(self, video_search: typing.List[str]) -> typing.List[typing.Any]:
        """Returns data about the video

        Returns:
            typing.List[typing.Any]: The list of data from the video data table
        """

        try:
            # creates cursor
            cursor = self.sqlite_connection.cursor()

            # setting up selection query
            sqlite_select_query = """SELECT title, date, videolength,
                                    outputvideolength FROM video
                                    WHERE title """

            # sets up the last part of the query based on the searches wanted
            addition_query = """ """
            if len(video_search) > 1:
                addition_query = " IN " + (str(tuple(video_search)))
            else:
                addition_query = "='" + str(video_search[0]) + "'"

            # executes selection query and saves the data in records
            cursor.execute(sqlite_select_query + addition_query)
            records = cursor.fetchall()
            cursor.close()

            # returns all data gained from the query
            return records

        except sqlite3.Error as error:
            # If error occurs the error is logged and it returns an empty list
            print("Failed to read data from sqlite table", error)
            return []

    def get_data(self, video_search: typing.List[str]) -> typing.List[typing.Any]:
        """Returns all the data necessary to write a report

        Args:
            video_search (List[str]): A list of videoIds which are used to find data about
                                      detections the given videos

        Returns:
            Typing.List[typing.Any]: A list of all selected elements from the database,
                                     where an element consists of video title, detection id,
                                     detection starttime and detection end time
        """

        try:
            # creates cursor
            cursor = self.sqlite_connection.cursor()

            # setting up selection query
            sqlite_select_query = """SELECT video.title, detection.id,
                                    detection.starttime, detection.endtime
                                    FROM detection
                                    RIGHT JOIN video ON video.id = detection.videoid
                                    WHERE video.title"""

            # sets up the last part of the query based on the searches wanted
            addition_query = """ """
            if len(video_search) > 1:
                addition_query = " IN " + (str(tuple(video_search)))
            else:
                addition_query = "='" + str(video_search[0]) + "'"

            # executes selection query and saves the data in records
            cursor.execute(sqlite_select_query + addition_query)
            records = cursor.fetchall()
            cursor.close()

            # returns all data gained from the query
            return records

        except sqlite3.Error as error:
            # If error occurs the error is logged and it returns an empty list
            print("Failed to read data from sqlite table", error)
            return []

    def get_metadata(self, path: Path) -> typing.Any:
        """Gets the video's metadata

        Args:
            path (Path): path to the video

        Returns:
            typing.Any: A variable with all of the video's metadata
        """
        try:
            file_metadata = ffmpeg.probe(str(path))

            return file_metadata["format"]

        except ffmpeg.Error as error:
            logger.error("Error occured: %s", error.stderr.decode("utf8"))
            return None

    def get_timestamps(
        self, path: Path, ranges: typing.List[typing.Tuple[int, int]]
    ) -> typing.List[typing.Tuple[str, str]]:
        """Gets the timestamps for when a frame occurs in the video

        Args:
            path (Path): path to the video
            ranges (typing.List[typing.Tuple[int, int]]): list of frame ranges found with
                                                          fish detected where the frames are
                                                          represented as ints

        Returns:
            typing.List[typing.Tuple[str, str]]: list of frame ranges with fish converted into
                                                 timestamps
        """
        try:
            # probes for frame rate in video metadata
            file_metadata = ffmpeg.probe(str(path), select_streams="v")
            frame_rate: str = file_metadata["streams"][0]["r_frame_rate"]

            # parcing metadata from str to float
            temp = frame_rate.split("/")
            first = int(temp[0])
            second = int(temp[1])
            framerate = first / second

            # iterated through the frame ranges to convert into timestamps
            timestamps: typing.List[typing.Tuple[str, str]] = []
            for start, end in ranges:
                start_stamp = start / framerate
                end_stamp = end / framerate
                timestamps.append(
                    (
                        str(datetime.timedelta(seconds=start_stamp)),
                        str(datetime.timedelta(seconds=end_stamp)),
                    )
                )

            return timestamps

        except ffmpeg.Error as error:
            logger.error("Error occured: %s", error.stderr.decode("utf8"))
            return []
