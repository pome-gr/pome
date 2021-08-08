from pome.models.encoder import PomeEncodable


class Address(PomeEncodable):
    """Representation of a postal address."""

    def __init__(
        self,
        line_1: str = "",
        line_2: str = "",
        line_3: str = "",
        city: str = "",
        postal_code: str = "",
        country_code: str = "",
    ):
        self.line_1: str = line_1
        self.line_2: str = line_2
        self.line_3: str = line_3
        self.city: str = city
        self.postal_code: str = postal_code
        self.country_code: str = country_code
