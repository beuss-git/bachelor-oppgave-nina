"""Stores data about video and detections in local database"""
import os
import sqlite3
import sys
import traceback
import typing
from datetime import datetime
from pathlib import Path

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

    def add_video_data(self, video_id: Path, title: str) -> None:
        """Adds a video into the video table

        Args:
            video_id (int): Unique id of the input video
            title (str): Filename of video
            date (str): date the video was captured in YYYY-MM-DD
            time (str): length of the video in HH:MM:SS
        """

        try:
            # creates cursor
            cursor = self.sqlite_connection.cursor()

            # gets videolength from metadata
            metadata = self.get_metadata(video_id)
            duration = "00:00:00"
            if metadata is not None:
                duration = datetime.fromtimestamp(float(metadata["duration"])).strftime(
                    "%H:%M:%S"
                )

            # sets up query and data that will be in the query
            sqlite_insert_query = """INSERT INTO video
                          (id, title, date, videolength)  VALUES  (?, ?, ?, ?)"""
            data = (
                str(video_id),
                title,
                datetime.fromtimestamp(os.path.getctime(video_id)).strftime("%Y-%m-%d"),
                duration,
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
                          (id, videoid, starttime, endtime)
                          VALUES (?, ?, ?, ?);"""

            # Setting up list of detections with video id and detection id
            detections_list: typing.List[typing.Tuple[str, str, str, str]] = []
            for num in enumerate(detections):
                ids = (str(video_id) + "-" + str(num), str(video_id))
                detections_list.append(ids + ("12:00:00", "13:00:00"))

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
                                    WHERE video.id"""

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
        """_summary_

        Args:
            path (str): _description_
            filename (str): _description_
            metadata (typing.List[str]): _description_

        Returns:
            typing.Any: _description_
        """
        try:
            file_metadata = ffmpeg.probe(str(path))

            return file_metadata["format"]

        except ffmpeg.Error as error:
            logger.error("Error occured: %s", error.stderr.decode("utf8"))
            return None

    # def get_timestamps(
    #    self, ranges: typing.List[typing.Tuple[int, int]]
    # ) -> typing.List[typing.Tuple[str, str]]:

    #    """_summary_

    #    Args:
    #        ranges (typing.List[typing.Tuple[int, int]]): _description_

    #    Returns:
    #        typing.List[typing.Tuple[str, str]]: _description_
    #    """
    #    return []

    def close_connection(self) -> None:
        """Closes the connection with sqlite"""

        if self.sqlite_connection:
            self.sqlite_connection.close()
            print("sqlite connection is closed")
