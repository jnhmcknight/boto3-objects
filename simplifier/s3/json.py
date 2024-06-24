
import json

from .core import Object


class JsonObject(Object):

    @classmethod
    def create(cls, bucket, key, contents, **kwargs):
        if not isinstance(contents, (str, bytes,)):
            contents = json.dumps(contents)

        return super().create(bucket, key, contents, **kwargs)

    @property
    def contents(self):
        return json.loads(super().contents)
