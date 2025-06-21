# do a little test with postgresql
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime


from backend.backend import JarvisBrainFactory
from backend.source.psql_handler import JarvisBrainPSQL


from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# ------------------------------------------------------------------ #
# testing script


def test_psql_functionality(instance: JarvisBrainPSQL):
    """
    Test all PostgreSQL functionality with the JarvisBrainPSQL handler
    """
    print("\n" + "=" * 60)
    print("TESTING POSTGRESQL FUNCTIONALITY")
    print("=" * 60)

    # Step 1: Insert a new message
    print("\n1. INSERTING NEW MESSAGE")
    print("-" * 30)
    new_message = instance.insert_message(
        datetime.now(), "Hello, JARVIS! This is a test message."
    )
    print(
        f"Inserted message with ID: {new_message.id if hasattr(new_message, 'id') else 'unknown'}"
    )

    # Step 2: Fetch all messages
    print("\n2. FETCHING ALL MESSAGES")
    print("-" * 30)
    messages = instance.fetch_all_messages()
    print(f"Found {len(messages)} messages:")
    for message in messages:
        print(
            f"ID: {message['id']} | Date: {message['date']} | Message: {message['message']}"
        )

    # Step 3: Get a specific message by ID
    if messages:
        print("\n3. FETCHING MESSAGE BY ID")
        print("-" * 30)
        message_id = messages[0]["id"]
        message = instance.get_message_by_id(message_id)
        if message:
            print(
                f"Message found: ID: {message['id']} | Date: {message['date']} | Message: {message['message']}"
            )
        else:
            print(f"No message found with ID {message_id}")

    # Step 4: Update a message
    if messages:
        print("\n4. UPDATING A MESSAGE")
        print("-" * 30)
        message_id = messages[0]["id"]
        updated_message = instance.update_message(
            message_id, "This message has been updated!"
        )
        if updated_message:
            print(
                f"Updated message: ID: {updated_message['id']} | Date: {updated_message['date']} | Message: {updated_message['message']}"
            )
        else:
            print(f"Failed to update message with ID {message_id}")

        # Verify the update by fetching it again
        message = instance.get_message_by_id(message_id)
        print(f"Verification - Message now reads: {message['message']}")

    # Step 5: Delete a message (optional - comment out if you want to keep the data)
    if len(messages) > 1:
        print("\n5. DELETING A MESSAGE")
        print("-" * 30)
        # Delete the second message to keep at least one in the database
        message_id = messages[1]["id"]
        success = instance.delete_message(message_id)
        if success:
            print(f"Successfully deleted message with ID {message_id}")
        else:
            print(f"Failed to delete message with ID {message_id}")

        # Verify the deletion
        messages_after = instance.fetch_all_messages()
        print(f"Messages after deletion: {len(messages_after)}")

    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Database connection parameters
    DB_NAME = os.getenv("POSTGRES_DB", "jarvis_brain")
    DB_USER = os.getenv("POSTGRES_USER", "JARVIS")  # Use JARVIS as default
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "jarvis_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")

    print(f"Connecting to PostgreSQL database: {DB_NAME} as user: {DB_USER}")

    try:
        # Connection string
        instance = JarvisBrainFactory.get_instance()
        instance.connect()

        # Run comprehensive tests
        test_psql_functionality(instance)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "instance" in locals() and instance:
            instance.close()
