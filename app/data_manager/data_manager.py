"""Stores data about video and detections in local database"""
import sqlite3
import traceback
import sys
import typing


class DataManager:
    """_summary_"""

    def __init__(self) -> None:
        """establishes the connection with local sqlite database"""
        try:
            self.sqlite_connection = sqlite3.connect("SQLite_Python.db")
            print("Successfully Connected to SQLite")

        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)

    def create_tables(self) -> None:
        """creates tables in the database"""
        try:
            cursor = self.sqlite_connection.cursor()

            with open(
                "app/data_manager/sqlite_tables.sql",
                "r",
                encoding="ascii",
                errors="ignore",
            ) as sqlite_file:
                sql_script = sqlite_file.read()

            cursor.executescript(sql_script)
            print("SQLite script executed successfully")
            cursor.close()

        except sqlite3.Error as error:
            print("Error while creating a sqlite table", error)

    def add_video_data(self, video_id: int, title: str, date: str, time: str) -> None:
        """add a video to video table"""
        try:
            cursor = self.sqlite_connection.cursor()

            sqlite_insert_query = """INSERT INTO video
                          (id, title, date, videolength)  VALUES  (?, ?, ?, ?)"""

            data = (video_id, title, date, time)

            cursor.execute(sqlite_insert_query, data)
            self.sqlite_connection.commit()
            print("Record inserted successfully into table at ", cursor.rowcount)
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table")
            print("Exception class is: ", error.__class__)
            print("Exception is", error.args)
            print("Printing detailed SQLite exception traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def add_detection_data(
        self, video_id: int, detections: typing.List[typing.Tuple[str, str]]
    ) -> None:
        """_summary_"""
        try:
            cursor = self.sqlite_connection.cursor()

            sqlite_insert_query = """INSERT INTO detection
                          (id, videoid, starttime, endtime)
                          VALUES (?, ?, ?, ?);"""

            detections_list: typing.List[typing.Tuple[int, int, str, str]] = []
            for num, detection in enumerate(detections):
                ids = (video_id + num, video_id)
                detections_list.append(ids + detection)

            cursor.executemany(sqlite_insert_query, detections_list)
            self.sqlite_connection.commit()
            print(
                "Total",
                cursor.rowcount,
                "Records inserted successfully into detection table",
            )
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to insert multiple records into sqlite table", error)

    def get_data(
        self,
    ) -> typing.List[typing.Any]:
        """_summary_"""
        try:
            cursor = self.sqlite_connection.cursor()

            sqlite_select_query = """SELECT video.title, detection.id,
                                    detection.starttime, detection.endtime
                                    FROM detection
                                    INNER JOIN video ON video.id = detection.videoid"""
            cursor.execute(sqlite_select_query)
            records = cursor.fetchall()
            cursor.close()

            return records

        except sqlite3.Error as error:
            print("Failed to read data from sqlite table", error)
            return []

    def close_connection(self) -> None:
        """Closes the connection with sqlite"""
        if self.sqlite_connection:
            self.sqlite_connection.close()
            print("sqlite connection is closed")
