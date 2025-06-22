from flask_socketio import SocketIO

from typing import List, Dict


# ---------------------------------------------------------------------------- #
# constants
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
# utility function
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


# client handler
class ClientHandlerObject:
    __INSTANCE = None

    def __init__(self):
        self.streaming_id = None
        self.file_path = None

    @staticmethod
    def get_instance() -> "ClientHandlerObject":
        if not ClientHandlerObject.__INSTANCE:
            ClientHandlerObject.__INSTANCE = ClientHandlerObject()
        return ClientHandlerObject.__INSTANCE

    @staticmethod
    def is_connected() -> bool:
        """
        Check if the client handler is connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        return ClientHandlerObject.__INSTANCE.streaming_id is not None
