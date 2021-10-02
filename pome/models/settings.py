from typing import Union
from pome.models.encoder import PomeEncodable


class Settings(PomeEncodable):

    default_filename = "pome_settings.json"

    def __init__(
        self,
        git_communicate_with_remote: bool = True,
        doc_filler_URL: str = "",
    ):
        self.git_communicate_with_remote: bool = git_communicate_with_remote
        self.doc_filler_URL: str = doc_filler_URL
