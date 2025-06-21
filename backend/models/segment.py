from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    IntField,
    DateTimeField,
    ReferenceField,
    ListField,
    BinaryField,
)


# --------------------------------------------------------------------------- #
# segment model
# --------------------------------------------------------------------------- #


class Segment(Document):
    meta = {
        "collection": "segments",
    }

    # information about segments
    start_time = IntField(required=True)
    end_time = IntField(required=True)
    text = StringField(required=True)

    created_at = StringField(default=datetime.utcnow)
    updated_at = StringField(default=datetime.utcnow)

    user = ReferenceField("User", required=True)
    recording = ReferenceField("Recording", required=True)
