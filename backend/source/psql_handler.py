# do a little test with postgresql
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Import the Message model and repository
from models.message import Message, MessageRepository


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
        self.repository = None

    def connect(self):
        """
        Establish a connection to the PostgreSQL database and initialize the repository.
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

            # Initialize the repository with connection params
            connection_params = {
                "dbname": self.db_name,
                "user": self.user,
                "password": self.password,
                "host": self.host,
                "port": self.port,
            }
            self.repository = MessageRepository(connection_params)

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
        Insert a message into the 'messages' table using the Message model.
        """
        try:
            # Create a Message object
            message_obj = Message(message=message, date=date)

            # Use the repository to save it
            self.repository.create(message_obj)
            print("Message inserted successfully.")
            return message_obj
        except Exception as e:
            print(f"Error inserting message: {e}")
            raise

    def fetch_all_messages(
        self,
        filters: str = None,
        sort_by: str = "date",
        sort_order: str = "DESC",
        limit: int = None,
    ):
        """
        Fetch all rows from the 'messages' table using the Message model.

        :param filters: Optional filter conditions to apply to the query (SQL WHERE clause)
        :param sort_by: Column to sort by, defaults to 'date'
        :param sort_order: Sort order ('ASC' or 'DESC'), defaults to 'DESC'
        :param limit: Optional limit on the number of results
        :return: List of rows fetched from the table.
        """
        try:
            # For flexibility with all parameters, use a raw SQL approach
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Start with the base query
                query = "SELECT * FROM messages"

                # Add filters if provided
                if filters:
                    query += f" WHERE {filters}"

                # Add sorting
                if sort_by:
                    # Sanitize sort_by to prevent SQL injection
                    sort_by = sql.Identifier(sort_by).as_string(cursor)
                    # Ensure sort_order is either ASC or DESC
                    sort_order = "ASC" if sort_order.upper() == "ASC" else "DESC"
                    query += f" ORDER BY {sort_by} {sort_order}"

                # Add limit if provided
                if limit is not None and limit > 0:
                    query += f" LIMIT {limit}"

                cursor.execute(query)
                rows = cursor.fetchall()
                return rows

        except Exception as e:
            print(f"Error fetching messages: {e}")
            raise

    def get_message_by_id(self, message_id: int):
        """
        Get a message by its ID.

        :param message_id: The ID of the message to retrieve.
        :return: The message if found, None otherwise.
        """
        try:
            message = self.repository.get_by_id(message_id)
            if message:
                return message.to_dict()
            return None
        except Exception as e:
            print(f"Error fetching message by ID: {e}")
            raise

    def update_message(self, message_id: int, new_message: str):
        """
        Update an existing message.

        :param message_id: The ID of the message to update.
        :param new_message: The new message content.
        :return: The updated message if successful, None otherwise.
        """
        try:
            # Get the existing message
            message = self.repository.get_by_id(message_id)
            if not message:
                print(f"Message with ID {message_id} not found.")
                return None

            # Update the message content
            message.message = new_message

            # Save the updated message
            updated_message = self.repository.update(message)
            print(f"Message with ID {message_id} updated successfully.")
            return updated_message.to_dict()
        except Exception as e:
            print(f"Error updating message: {e}")
            raise

    # this is a dangerous operation, use with caution
    def purge_db(self):
        """
        Purge the 'messages' table by deleting all rows.
        """
        try:
            # For dangerous operations like this, use direct SQL for efficiency
            delete_sql = sql.SQL("DELETE FROM messages;")
            with self.connection.cursor() as cursor:
                cursor.execute(delete_sql)
                print("All messages deleted successfully.")
        except Exception as e:
            print(f"Error purging database: {e}")
            raise

    def delete_message(self, message_id: int):
        """
        Delete a message by its ID.

        :param message_id: The ID of the message to delete.
        :return: True if deletion was successful, False otherwise.
        """
        try:
            success = self.repository.delete(message_id)
            if success:
                print(f"Message with ID {message_id} deleted successfully.")
            else:
                print(f"Message with ID {message_id} not found.")
            return success
        except Exception as e:
            print(f"Error deleting message: {e}")
            raise
