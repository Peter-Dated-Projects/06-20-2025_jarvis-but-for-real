# do a little test with postgresql
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime


from backend.source.psql_handler import JarvisBrainPSQL


from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# ------------------------------------------------------------------ #
# testing script


def print_all_messages(instance: JarvisBrainPSQL):
    """
    Connect to PostgreSQL and print all rows from the messages table
    """

    # add a message into the "messages" table
    instance.insert_message(datetime.now(), "Hello, world!")

    # fetch all messages from the "messages" table
    messages = instance.fetch_all_messages()

    for message in messages:
        print(f"Date: {message['date']}, Message: {message['message']}")


if __name__ == "__main__":

    # Database connection parameters - update these as needed
    DB_NAME = os.getenv("POSTGRES_DB", "jarvis_brain")
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")

    # Connection string
    instance = JarvisBrainPSQL(
        db_name=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    instance.connect()

    # run function
    print_all_messages(instance)
