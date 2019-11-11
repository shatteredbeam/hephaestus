import sqlite3
import math
from datetime import datetime
from sqlite3 import Error
from loguru import logger


class Database:
    """
    Database Connector for SQLite File.
    """

    def __init__(self, db_file='db\\database.db'):
        self._cursor = None
        self._database = None

        # Connect to database
        try:
            self._database = sqlite3.connect(db_file)
        except Error as error:
            logger.exception(error)
            self._connected = False
        else:
            self._cursor = self._database.cursor()
            self._connected = True

        # If we're connected, check for an existing linkage table

        if self._connected:
            logger.info("Connected to database")
            cursor = self._cursor
            cursor.execute(''' SELECT count(name) FROM sqlite_master 
                    WHERE type='table' AND name='linkage' ''')

            if cursor.fetchone()[0] == 1:
                logger.info("Found existing table")
                cursor.execute("vacuum")
            else:
                logger.info("Linkage table NOT FOUND.  Creating a new one...")
                create_table = "CREATE TABLE IF NOT EXISTS linkage " \
                               "(uuid text PRIMARY KEY, added_date text," \
                               "link text, view_count integer, data blob)"

                try:
                    cursor.execute(create_table)
                except Error as error:
                    logger.exception(error)
                else:
                    logger.info("Succesfully created new linkage table")

        else:
            logger.exception("Database not connected.")

        self._database.commit()

    def add_view(self, uuid):
        query = 'UPDATE linkage SET view_count = view_count + 1 WHERE uuid = ?'
        cursor = self._cursor

        try:
            cursor.execute(query, (uuid,))
        except Error as error:
            logger.exception(Error)
            raise

        self._database.commit()

    def insert(self, uuid, blob):
        time_added = datetime.now()
        new_row = (str(uuid), str(time_added), 0, sqlite3.Binary(blob.getvalue()))
        insert_query = f"INSERT INTO 'linkage' ('uuid', 'added_date', 'view_count', 'data') " \
                       f"VALUES (?,?,?,?)"

        cursor = self._cursor

        try:
            cursor.execute(insert_query, new_row)
        except Error as error:
            logger.exception(error)
        else:
            logger.info(f"{uuid} added | ({math.floor(blob.tell() / 1024)}kb) ")

        self._database.commit()

    def query(self, uuid):
        search_query = f"SELECT uuid, added_date, data FROM linkage WHERE uuid=?"

        try:
            cursor = self._cursor
            cursor.execute(search_query, (uuid,))
        except Error as error:
            logger.exception(error)
            raise
        else:
            results = cursor.fetchone()
            return results

    def delete(self, uuid):
        delete_query = f"DELETE FROM linkage WHERE uuid={uuid}"

        try:
            cursor = self._cursor
            cursor.execute(delete_query)
        except Error as error:
            logger.exception(error)
        else:
            logger.info(f"{uuid} deleted from database")

        self._database.commit()
