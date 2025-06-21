# do a little test with postgresql
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime


# ------------------------------------------------------------------ #
# PostgreSQL CRUD operations
# ------------------------------------------------------------------ #


class JarvisBrainPSQL:
    def __init__(
        self,
        db_name: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: str = "5432",
    ):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """
        Establish a connection to the PostgreSQL database.
        """
        try:
            self.connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            self.connection.autocommit = True  # Enable autocommit mode
            print("Connection to PostgreSQL established successfully.")
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    def close(self):
        """
        Close the connection to the PostgreSQL database.
        """
        if self.connection:
            self.connection.close()
            print("Connection to PostgreSQL closed.")

    # ------------------------------------------------------------------ #
    # crud operations

    def insert_message(self, date: datetime, message: str):
        """
        Insert a message into the 'messages' table.
        """
        insert_sql = sql.SQL("INSERT INTO messages (date, message) VALUES (%s, %s);")
        with self.connection.cursor() as cursor:
            cursor.execute(insert_sql, (date, message))
            print("Message inserted successfully.")

    def fetch_all_messages(self, filter: str = None):
        """
        Fetch all rows from the 'messages' table in the PostgreSQL database.
        If a filter is provided, it will be applied to the query.

        :param filter: Optional filter condition to apply to the query.

                :return: List of rows fetched from the table.
        """
        select_sql = sql.SQL("SELECT * FROM messages")
        if filter:
            select_sql += sql.SQL(" WHERE {}").format(sql.SQL(filter))
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            return rows

    # this is a dangerous operation, use with caution
    def purge_db(self):
        """
        Purge the 'messages' table by deleting all rows.
        """
        delete_sql = sql.SQL("DELETE FROM messages;")
        with self.connection.cursor() as cursor:
            cursor.execute(delete_sql)
            print("All messages deleted successfully.")
