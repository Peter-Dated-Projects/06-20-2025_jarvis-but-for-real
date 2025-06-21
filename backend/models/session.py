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

# ----------------------------------------------------------------------------- #
# session model
# ----------------------------------------------------------------------------- #


class Session(Document):
    meta = {
        "collection": "sessions",
    }

    # information about the conversation
    segments = ListField(ReferenceField("Segment"), default=[])
