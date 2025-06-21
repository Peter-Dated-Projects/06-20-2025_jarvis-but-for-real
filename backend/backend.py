from flask_socketio import SocketIO


from typing import List

# Add postgres imports
import psycopg2
import os

from source.whispercore_handler import WhisperCoreHandler

from flask import Flask
import flask_cors
from flask import current_app as app

from dotenv import load_dotenv

from source.psql_handler import JarvisBrainPSQL

# ---------------------------------------------------------------------------- #
# constants
# ---------------------------------------------------------------------------- #


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

    @staticmethod
    def add_cache(streaming_id: str, cache_object: "AudioStreamCache"):
        """Add a new audio stream cache."""
        AudioBuffersInstance.get_instance()[streaming_id] = cache_object

    @staticmethod
    def get_cache(streaming_id: str) -> "AudioStreamCache":
        """Get an audio stream cache by its streaming ID."""
        return AudioBuffersInstance.get_instance().get(streaming_id, None)

    @staticmethod
    def is_valid_streaming_key(streaming_id: str) -> bool:
        """Check if the streaming ID is valid."""
        return streaming_id in AudioBuffersInstance.get_instance()

    @staticmethod
    def clean_cache(streaming_id: str):
        """Clean the audio stream cache for a given streaming ID."""
        if streaming_id in AudioBuffersInstance.get_instance():
            del AudioBuffersInstance.get_instance()[streaming_id]
        else:
            print(f"Streaming ID {streaming_id} not found in cache.")


# whispercore multi-model factory
class WhisperCoreManyModel:
    __INSTANCE = None


# whispercore single-model factory
class WhisperCoreSingleModel:
    __INSTANCE = None

    def __init__(self):
        self._models = {}

    def add_model(self, model_path: str):
        """Add a model instance to the single model factory."""
        self._models[model_path] = WhisperCoreHandler(model_path)

    def remove_model(self, model_path: str):
        """Remove a model instance from the single model factory."""
        if model_path in self._models:
            del self._models[model_path]
        else:
            print(f"Model {model_path} not found in factory.")

    def has_model(self, model_path: str) -> bool:
        """Check if a model instance exists in the single model factory."""
        return model_path in self._models

    def get_model(self, model_path: str):
        """Get a model instance by its path."""
        return self._models.get(model_path, None)

    @staticmethod
    def get_instance():
        if not WhisperCoreSingleModel.__INSTANCE:
            # Initialize the single model instance here
            # This is a placeholder, replace with actual model initialization
            WhisperCoreSingleModel.__INSTANCE = WhisperCoreSingleModel()
        return WhisperCoreSingleModel.__INSTANCE


# jarvis brain factory
class JarvisBrainFactory:
    __INSTANCE = None

    @staticmethod
    def get_instance():
        if not JarvisBrainFactory.__INSTANCE:
            # Database connection parameters
            DB_NAME = os.getenv("POSTGRES_DB")
            DB_USER = os.getenv("POSTGRES_USER")  # Use JARVIS as default
            DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
            DB_HOST = os.getenv("POSTGRES_HOST")
            DB_PORT = os.getenv("POSTGRES_PORT")
            if not all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT]):
                raise ValueError("Database connection parameters are not set.")

            # Initialize the PSQL handler
            JarvisBrainFactory.__INSTANCE = JarvisBrainPSQL(
                db_name=DB_NAME,
                db_user=DB_USER,
                db_password=DB_PASSWORD,
                db_host=DB_HOST,
                db_port=DB_PORT,
            )

            # connect
            JarvisBrainFactory.__INSTANCE.connect()
        return JarvisBrainFactory.__INSTANCE


# ---------------------------------------------------------------------------- #
# Data structures
# ---------------------------------------------------------------------------- #


class AudioStreamCache:

    # sockets are full-duplex / bidirectional
    # good
    def __init__(self, streaming_id: str, file_path: str, target_model_path: str):
        self._streaming_id = streaming_id
        self._file_path = file_path

        # target model
        self._target_model = target_model_path
        self._whispercore_handler = WhisperCoreSingleModel.get_instance().get_model(
            target_model_path
        )

        # for when finished
        self._file_url = None

        # create an instance of the real time audio handler
        self._real_time_handler = None

    def add_audio_chunk(self, chunk: bytes):
        self._whispercore_handler.add_audio_chunk(chunk)

    def get_audio_data(self) -> List[bytes]:
        return self._whispercore_handler.get_audio_data()
