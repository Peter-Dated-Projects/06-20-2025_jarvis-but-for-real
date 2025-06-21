from datetime import datetime
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor


class Message:
    """
    Message model representing a stored message in the PostgreSQL database.

    Attributes:
        id (int): Unique identifier for the message (auto-generated)
        date (datetime): Timestamp when the message was created
        message (str): The message content, max length 16392 characters
    """

    def __init__(
        self, message: str, date: Optional[datetime] = None, id: Optional[int] = None
    ):
        """
        Initialize a Message object.

        Args:
            message (str): The message content
            date (datetime, optional): Message timestamp. Defaults to current time if None.
            id (int, optional): Message ID from database. Defaults to None for new messages.
        """
        self.id = id
        self.date = date if date else datetime.now()

        # Validate message length
        if len(message) > 16392:
            raise ValueError(
                f"Message exceeds maximum length of 16392 characters (got {len(message)})"
            )
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert Message object to dictionary."""
        return {"id": self.id, "date": self.date, "message": self.message}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create Message object from dictionary."""
        return cls(
            id=data.get("id"), date=data.get("date"), message=data.get("message")
        )


class MessageRepository:
    """
    Repository for interacting with messages in the PostgreSQL database.
    """

    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the repository with database connection parameters.

        Args:
            connection_params: Dictionary containing database connection parameters
        """
        self.connection_params = connection_params

    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(**self.connection_params)

    def create(self, message: Message) -> Message:
        """
        Save a new message to the database.

        Args:
            message: The Message object to save

        Returns:
            Message: The saved Message with ID assigned
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "INSERT INTO messages (date, message) VALUES (%s, %s) RETURNING id",
                    (message.date, message.message),
                )
                result = cursor.fetchone()
                message.id = result["id"]
                conn.commit()
                return message

    def get_by_id(self, message_id: int) -> Optional[Message]:
        """
        Get a message by its ID.

        Args:
            message_id: The ID of the message to retrieve

        Returns:
            Message or None: The message if found, None otherwise
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM messages WHERE id = %s", (message_id,))
                result = cursor.fetchone()
                if result:
                    return Message.from_dict(result)
                return None

    def get_all(self) -> List[Message]:
        """
        Get all messages from the database.

        Returns:
            List[Message]: List of all messages
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM messages ORDER BY date ASC")
                results = cursor.fetchall()
                return [Message.from_dict(row) for row in results]

    def update(self, message: Message) -> Message:
        """
        Update an existing message.

        Args:
            message: The Message object to update

        Returns:
            Message: The updated Message
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE messages SET date = %s, message = %s WHERE id = %s",
                    (message.date, message.message, message.id),
                )
                conn.commit()
                return message

    def delete(self, message_id: int) -> bool:
        """
        Delete a message by its ID.

        Args:
            message_id: The ID of the message to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM messages WHERE id = %s", (message_id,))
                row_count = cursor.rowcount
                conn.commit()
                return row_count > 0


# Example usage:
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Database connection parameters
    db_params = {
        "dbname": os.getenv("POSTGRES_DB", "jarvis_brain"),
        "user": os.getenv("POSTGRES_USER", "JARVIS"),
        "password": os.getenv("POSTGRES_PASSWORD", "jarvis_password"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    # Create repository
    repo = MessageRepository(db_params)

    # Example: Create a new message
    new_message = Message("Hello, JARVIS! This is a test message.")
    saved_message = repo.create(new_message)
    print(f"Created message with ID: {saved_message.id}")

    # Example: Get all messages
    all_messages = repo.get_all()
    print(f"Found {len(all_messages)} messages:")
    for msg in all_messages:
        print(
            f"[{msg.date}] {msg.message[:50]}..."
            if len(msg.message) > 50
            else msg.message
        )
