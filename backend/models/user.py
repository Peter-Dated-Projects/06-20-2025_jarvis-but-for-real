from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    EmailField,
    IntField,
    ListField,
    ReferenceField,
    BooleanField,
)
from bson import json_util
import json


# --------------------------------------------------------------------------- #
# user model
# --------------------------------------------------------------------------- #


class User(Document):
    meta = {
        "collection": "users",
    }

    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)

    # defaulted items
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)

    # non required items
    address = StringField()

    # speech to text information
    conversations = ListField(ReferenceField("Conversation"))
