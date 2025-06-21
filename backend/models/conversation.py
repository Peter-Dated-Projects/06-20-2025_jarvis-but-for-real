from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    IntField,
    DateTimeField,
    ListField,
    BinaryField,
    ReferenceField,
    DecimalField,
    BooleanField,
)

# --------------------------------------------------------------------------- #
# conversation model
# --------------------------------------------------------------------------- #


class Conversation(Document):
    meta = {
        "collection": "default_conversations",
    }

    type = StringField(
        required=True, default="conversation"
    )  # type of conversation, text or audio

    # information about conversations
    title = StringField(required=True)
    description = StringField()

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # keep track of number of users in the conversation
    participants = ListField(ReferenceField("User"))
    sessions = ListField(ReferenceField("Session"), default=[])
