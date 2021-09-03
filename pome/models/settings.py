from pome.models.encoder import PomeEncodable


class Settings(PomeEncodable):

    default_filename = "pome_settings.json"

    def __init__(self, git_communicate_with_remote: bool = True):
        self.git_communicate_with_remote: bool = git_communicate_with_remote
