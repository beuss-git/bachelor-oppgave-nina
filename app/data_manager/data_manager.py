"""Stores data about video and detections in local database"""
import sqlite3
import traceback
import sys
import typing


class DataManager:
    """Class for interacting with local sqlite database"""

    def __init__(self) -> None:
        """establishes the connection with local sqlite database"""

        try:
            # Creates a connection with the db file
            self.sqlite_connection = sqlite3.connect("SQLite_Python.db")
            print("Successfully Connected to SQLite")

        except sqlite3.Error as error:
            # If error occurs log the error
            print("Error while connecting to sqlite", error)

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

    def add_video_data(self, video_id: str, title: str, date: str, time: str) -> None:
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

            # sets up query and data that will be in the query
            sqlite_insert_query = """INSERT INTO video
                          (id, title, date, videolength)  VALUES  (?, ?, ?, ?)"""
            data = (video_id, title, date, time)

            # executes query to add the data into the table
            cursor.execute(sqlite_insert_query, data)
            self.sqlite_connection.commit()
            print("Record inserted successfully into table at ", cursor.rowcount)
            cursor.close()

        except sqlite3.Error as error:
            # If error occurs log the error
            print("Failed to insert data into sqlite table")
            print("Exception class is: ", error.__class__)
            print("Exception is", error.args)
            print("Printing detailed SQLite exception traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def add_detection_data(
        self, video_id: str, detections: typing.List[typing.Tuple[str, str]]
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
            for num, detection in enumerate(detections):
                ids = (video_id + str(num), video_id)
                detections_list.append(ids + detection)

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

    def close_connection(self) -> None:
        """Closes the connection with sqlite"""

        if self.sqlite_connection:
            self.sqlite_connection.close()
            print("sqlite connection is closed")
