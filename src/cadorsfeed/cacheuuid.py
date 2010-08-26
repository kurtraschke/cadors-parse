import uuid
from cadorsfeed.utils import db


def cacheuuid(key):
    key = "cacheuuid:" + key

    if not key in db:
        db[key] = uuid.uuid4().urn

    return db[key]
