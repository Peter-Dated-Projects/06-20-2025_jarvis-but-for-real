from flask import Blueprint, jsonify, request
from flask import current_app as app

import os

from backend import MongoDBInstance
from typing import Optional, Union, List, Dict, Any
from bson import json_util, ObjectId, Binary
import json

from models import conversation, user, segment


from mongoengine import NotUniqueError

# --------------------------------------------------------------------------- #
# blueprint
# -------------------------------------------------------------------------- #

storage_bp = Blueprint("storage_bp", __name__)


# --------------------------------------------------------------------------- #
# utility functions
# --------------------------------------------------------------------------- #


def get_db_objects(
    filter: dict, collection_name: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Get objects from the mongodb server and convert to JSON-serializable format

    Args:
        filter (dict): filter to apply to the query
        collection_name (str): name of the collection to query

    Returns:
        list: list of objects with serializable types
    """
    client = MongoDBInstance.get_database()
    if client is None:
        return None

    # perform ensured check
    if not ensured_endpoint(collection_name):
        print("Created new collection")

    collection = client[collection_name]
    if collection is None:
        return None

    objects = list(collection.find(filter))

    # Convert BSON to JSON-serializable format
    return json.loads(json_util.dumps(objects))


def get_db_object_count(filter_criteria: dict, collection_name: str) -> int:
    """
    Get the count of objects in a collection based on filter criteria.

    Args:
        filter_criteria (dict): The filter criteria to apply.
        collection_name (str): The name of the collection to query.

    Returns:
        int: The count of objects matching the filter criteria.
    """
    client = MongoDBInstance.get_database()
    if client is None:
        return 0

    collection = client[collection_name]
    if collection is None:
        return 0

    return collection.count_documents(filter_criteria)


def ensured_endpoint(collection_name: str):
    """

    Makes sure that a database and collection exist in the mongodb server
    Args:
        database_name (str): name of the database
        collection_name (str): name of the collection

    Returns:
        bool: True if the database and collection exist, False otherwise
    """

    client = MongoDBInstance.get_database()
    if client is None:
        return False

    # check if collection exists
    print(client)
    if collection_name not in client.list_collection_names():
        # create
        client.create_collection(collection_name)
        return False

    return True


def create_collection_if_not_exists(collection_name: str) -> Union[bool, str]:
    """
    Create a collection if it does not exist

    Args:
        collection_name (str): name of the collection to create

    Returns:
        bool: True if the collection was created, False if it already exists
        str: error message if the collection could not be created
    """
    client = MongoDBInstance.get_database()
    if client is None:
        return "No mongodb client found"

    if collection_name not in client.list_collection_names():
        try:
            client.create_collection(collection_name)
            return True
        except NotUniqueError as e:
            return f"Collection {collection_name} already exists: {e}"

    return False


def create_user_session_info_name(user_id: str, session_id: str) -> str:
    """
    Create a user-specific session info collection name based on the user ID and session ID.

    Args:
        user_id (str): The ID of the user.
        session_id (str): The ID of the session.

    Returns:
        str: The name of the user-specific session info collection.
    """
    return f"user_{user_id}_session_{session_id}_info"


# --------------------------------------------------------------------------- #
# storage functions
# --------------------------------------------------------------------------- #


@storage_bp.route("/status", methods=["GET"])
def status():
    """Check the status of the mongodb server."""
    try:
        client = MongoDBInstance()()
        client.admin.command("ping")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.error(f"MongoDB connection error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@storage_bp.route("/upload", methods=["POST"])
def upload():
    """Upload data to the mongodb server."""
    # get query data
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # check for collection name
    collection_name = data.get("collection")
    if not collection_name:
        return (
            jsonify({"status": "error", "message": "No collection name provided"}),
            400,
        )

    # check for object data
    object_data = data.get("object")
    if not object_data:
        return jsonify({"status": "error", "message": "No object data provided"}), 400

    # create collection if it doesnt exist
    client = MongoDBInstance.get_database()

    if client is None:
        return jsonify({"status": "error", "message": "No mongodb client found"}), 500

    if collection_name not in client.list_collection_names():
        client.create_collection(collection_name)

    # insert object into collection - if object is not None
    if object_data:
        collection = client[collection_name]

        print(object_data)

        if isinstance(object_data, list):
            # insert many
            result = collection.insert_many(object_data)
        else:
            # insert one
            result = collection.insert_one(object_data)

        if not result:
            return (
                jsonify({"status": "error", "message": "Failed to insert object"}),
                500,
            )

    return jsonify({"status": "ok"}), 200


@storage_bp.route("/delete", methods=["DELETE"])
def delete():
    """
    Delete all data from the mongodb server

    Sample Input:

    {
        "type": "object",
        "collection": "test",
        "object": "test",
        "filter": {
            "name": "test"
        }
    }


    """
    # get query data
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # get the mongodb client
    client = MongoDBInstance.get_database()
    if client is None:
        return jsonify({"status": "error", "message": "No mongodb client found"}), 500

    # check what we are deleting
    target_type = data.get("type")
    if not target_type:
        return (
            jsonify({"status": "error", "message": "No target type provided"}),
            400,
        )

    # retrieve collection name + filter criteria
    collection_name = data.get("collection")
    filter_criteria = data.get("filter")

    if target_type == "collection":
        if not collection_name:
            return (
                jsonify({"status": "error", "message": "No collection name provided"}),
                400,
            )
        # delete collection
        client.drop_collection(collection_name)
    elif target_type == "object":
        # delete object
        if filter_criteria and not isinstance(filter_criteria, dict):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Filter criteria must be a dictionary",
                    }
                ),
                400,
            )
        if not collection_name:
            return (
                jsonify({"status": "error", "message": "No collection name provided"}),
                400,
            )
        print(filter_criteria)

        # delete documents matching the filter directly
        result = client[collection_name].delete_many(
            filter_criteria if filter_criteria else {}
        )

        return (
            jsonify(
                {
                    "status": "ok",
                    "message": f"Deleted {result.deleted_count} objects",
                }
            ),
            200,
        )
    else:
        # invalid type
        return (
            jsonify({"status": "error", "message": "Invalid target type provided"}),
            400,
        )

    # temporary
    print(data)

    return jsonify({"status": "ok"}), 200


@storage_bp.route("/get_objects", methods=["POST"])
def get_objects():
    """Get object from the mongodb server."""
    # get query data
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # check for collection name
    collection_name = data.get("collection")
    if not collection_name:
        return (
            jsonify({"status": "error", "message": "No collection name provided"}),
            400,
        )

    # Make filter optional by providing a default empty dict
    filters = data.get("filter", {})

    # get the mongodb client
    client = MongoDBInstance.get_database()
    if client is None:
        return jsonify({"status": "error", "message": "No mongodb client found"}), 500

    # get the object from the collection
    try:
        results = get_db_objects(filters, collection_name)
        print(results)

        if results is None:
            return (
                jsonify({"status": "error", "message": "Failed to retrieve objects"}),
                500,
            )

        return jsonify({"status": "ok", "objects": results}), 200
    except Exception as e:
        app.logger.error(f"Error retrieving objects: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------------------------------------------- #
# specific functions
# --------------------------------------------------------------------------- #


@storage_bp.route("/get_conversations", methods=["GET"])
def get_conversations():
    """
    Get all conversations from the database for a specific user

    Returns:
        JSON: List of conversations

    Args:
    - user_id (str): ID of the user to get conversations for
    """

    # get user id
    user_id = request.args.get("user_id")
    if not user_id:
        return (
            jsonify({"status": "error", "message": "No user ID provided"}),
            400,
        )

    # get the mongodb client
    client = MongoDBInstance.get_database()
    if client is None:
        return jsonify({"status": "error", "message": "No mongodb client found"}), 500

    # get the user object
    _user_object = user.User.objects(id=ObjectId(user_id)).first()
    if _user_object is None:
        return (
            jsonify({"status": "error", "message": "User not found"}),
            404,
        )

    # grab all conversations that user is registered in
    _targets = _user_object.conversations
    if _targets is None:
        return (
            jsonify({"status": "error", "message": "No conversations found for user"}),
            404,
        )

    print(f"User {_user_object.email} has {len(_targets)} conversations")
    print(_targets)

    # retrieve conversation objects from the database
    _results = []
    for _target in _targets:
        # get the conversation object
        _conversation_object = conversation.Conversation.objects(
            id=ObjectId(_target.id)
        ).first()
        if _conversation_object is None:
            print(f"Conversation {str(_target.id)} not found")
            continue

        # convert to JSON-serializable format
        _string = json.loads(json_util.dumps(_conversation_object.to_mongo()))
        _results.append(_string)
    if _results is None:
        return (
            jsonify({"status": "error", "message": "No conversations found"}),
            404,
        )

    # return conversations
    return jsonify({"status": "ok", "conversations": _results}), 200


@storage_bp.route("/create_conversation", methods=["POST"])
def create_conversation():
    """
    Create a new conversation in the database

    {
        "user_id": {user id of the user creating the conversation},
        "data": {
            "title": {name of the conversation},
            "description": {description of the conversation},

            "audio_data": {null or binary data},
            "audio_duration": {duration of the audio in seconds},
            "compressed": {boolean indicating if the audio is compressed},
            "segment_ids": [{list of segment ids} | or null],

            "created_at": {timestamp of creation},
            "updated_at": {timestamp of last update},

            "participants": [{list of user ids} | or null for now]
        }
    }

    ."""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    user_id = data.get("user_id")
    conversation_data = data.get("data")
    if not user_id:
        return (
            jsonify({"status": "error", "message": "No user ID provided"}),
            400,
        )
    if not conversation_data:
        return (
            jsonify({"status": "error", "message": "No conversation data provided"}),
            400,
        )

    # get the mongodb client
    client = MongoDBInstance.get_database()
    if client is None:
        return jsonify({"status": "error", "message": "No mongodb client found"}), 500

    # grab user object
    _user_object = user.User.objects(id=ObjectId(user_id)).first()
    if _user_object is None:
        return (
            jsonify({"status": "error", "message": "User not found"}),
            404,
        )

    existing_conversations = len(_user_object.conversations)
    print(f"Existing conversations for user {user_id}: {existing_conversations}")

    # create a model instance of the conversation object
    _conversation_target = conversation.Conversation(
        title=conversation_data.get(
            "title", f"New Conversation {existing_conversations + 1}"
        ),
        description=conversation_data.get("description"),
        audio_data=Binary(conversation_data.get("audio_data", b"")),
        audio_duration=conversation_data.get("audio_duration", 0.0),
        compressed=conversation_data.get("compressed", False),
        segment_ids=conversation_data.get("segment_ids", []),
        created_at=conversation_data.get("created_at"),
        updated_at=conversation_data.get("updated_at"),
        participants=conversation_data.get("participants", []),
    )

    # Convert conversation object to string representation with all stored data
    print(f"Conversation data: {json_util.dumps(_conversation_target.to_mongo())}")

    result = _conversation_target.save()
    if not result:
        return (
            jsonify({"status": "error", "message": "Failed to create conversation"}),
            500,
        )

    # update user information
    _user_object.conversations.append(_conversation_target)
    _user_object.updated_at = conversation_data.get("updated_at")
    _user_object.save()
    if not _user_object:
        return (
            jsonify({"status": "error", "message": "Failed to update user"}),
            500,
        )

    return (
        jsonify(
            {
                "status": "ok",
                "_id": {"$oid": str(result.id)},
                "title": result.title,
                "description": result.description,
                "updated_at": {"$date": str(result.updated_at)},
            }
        ),
        200,
    )


@storage_bp.route("/get_conversation_messages", methods=["GET"])
def get_conversation_messages():
    print(request.args)
    pass


@storage_bp.route("/create_user", methods=["POST"])
def create_user():
    """
    Create a new user in the database

    {
        "data": {
            "first_name": {first name of the user},
            "last_name": {last name of the user},
            "email": {email of the user},
            "password": {password of the user},

            "address": {optional address of the user},

            "created_at": {timestamp of creation},
            "updated_at": {timestamp of last update},
            "is_active": {boolean indicating if the user is active}
        }
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # get the mongodb client
    client = MongoDBInstance.get_database()
    if client is None:
        return jsonify({"status": "error", "message": "No mongodb client found"}), 500

    # create collection if it doesn't exist
    collection_name = "users"
    if collection_name not in client.list_collection_names():
        client.create_collection(collection_name)

    # create a model instance of the user object
    _user_target = user.User(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
        password=data.get("password"),
        address=data.get("address"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        is_active=data.get("is_active", True),
    )

    # Convert user object to string representation with all stored data
    print(f"User data: {json_util.dumps(_user_target.to_mongo())}")

    _user_exists = user.User.objects(email=_user_target.email).first()

    # add an object into the user data
    if _user_exists is not None:
        print("Found Duplicate User")

        # find existing object
        print(_user_exists)
        _json = json_util.loads(json_util.dumps(_user_exists.to_mongo()))
        print(_json)

        test_id = str(_json["_id"])
        print(test_id)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Email already exists",
                    "code": "409",
                    "testid": test_id,
                }
            ),
            409,
        )

    result = _user_target.save()
    if not result:
        return (
            jsonify({"status": "error", "message": "Failed to create user"}),
            500,
        )

    return jsonify({"status": "ok", "id": str(result.id)}), 200
