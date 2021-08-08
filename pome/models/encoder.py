import json
from json import JSONEncoder


class PomeEncoder(JSONEncoder):
    """The json encoder used by pome.
    Keys are sorted and indent is applied in order to have human readable and diffable documents.
    """

    def __init__(self, **kwargs):
        super(PomeEncoder, self).__init__(**kwargs, indent=2)

    def default(self, o):
        return o.__dict__


class PomeEncodable(object):
    @classmethod
    def from_json_dict(cls, json_dict):
        to_return = cls(**json_dict)
        to_return._post_load_json()
        return to_return

    @classmethod
    def from_json_file(cls, filename):
        try:
            with open(filename, "r") as f:
                return cls.from_json_dict(json.loads(f.read()))
        except FileNotFoundError:
            return None

    def _post_load_json(self):
        """Function to execute once the object has been de-serialised from json."""
        pass

    def to_json(self):
        return PomeEncoder().encode(self)

    def __str__(self):
        return self.to_json()
