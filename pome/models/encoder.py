import json
from json import JSONEncoder


class PomeEncoder(JSONEncoder):
    """The json encoder used by pome.
    Keys are sorted and indent is applied in order to have human readable and diffable documents.
    """

    def __init__(self, **kwargs):
        super(PomeEncoder, self).__init__(**kwargs, sort_keys=True, indent=2)

    def default(self, o):
        return o.__dict__


class PomeEncodable(object):
    @classmethod
    def from_json(cls, json_s):
        to_return = cls()
        to_return.__dict__ = json.loads(json_s)
        return to_return

    def to_json(self):
        return PomeEncoder().encode(self)

    def __str__(self):
        return self.to_json()
