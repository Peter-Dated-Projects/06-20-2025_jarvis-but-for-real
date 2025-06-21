from flask_socketio import SocketIO

# Add postgres imports
import psycopg2
import os


# ---------------------------------------------------------------------------- #
# constants
# ---------------------------------------------------------------------------- #

CACHE_STREAMING_KEY = "streaming_key"
CACHE_AUDIO_DATA = "audio_data"
CACHE_FILE_PATH = "file_path"
CACHE_FILE_URL = "file_url"


# ---------------------------------------------------------------------------- #
# classes
# ---------------------------------------------------------------------------- #


# socketio factory
class SocketIOInstance:
    __INSTANCE = None

    @staticmethod
    def get_instance():
        if not SocketIOInstance.__INSTANCE:
            SocketIOInstance.__INSTANCE = SocketIO(cors_allowed_origins="*")
        return SocketIOInstance.__INSTANCE


# audio buffers factory
class AudioBuffersInstance:
    __INSTANCE = None

    @staticmethod
    def get_instance():
        if not AudioBuffersInstance.__INSTANCE:
            AudioBuffersInstance.__INSTANCE = {}
        return AudioBuffersInstance.__INSTANCE


# postgresql factory
class PostgresInstance:
    __CONN = None

    @staticmethod
    def get_instance():
        """
        Return a singleton PostgreSQL connection.
        Expects DATABASE_URL env var in the form:
          postgresql://user:password@host:port/database
        """
        if not PostgresInstance.__CONN:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise RuntimeError("DATABASE_URL environment variable is not set")
            PostgresInstance.__CONN = psycopg2.connect(dsn=db_url)
            PostgresInstance.__CONN.autocommit = True
        return PostgresInstance.__CONN
