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
# recording model
# --------------------------------------------------------------------------- #


class Recording(Document):

    meta = {
        "collection": "recordings",
    }

    # information about the recording
    audio_data = BinaryField(required=True)
    audio_duration = DecimalField(required=True)
    compressed = BooleanField(default=False)
