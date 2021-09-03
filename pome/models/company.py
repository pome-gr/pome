from pome.models.address import Address
from pome.models.encoder import PomeEncodable


class Company(PomeEncodable):
    """Stores all the metadata associated to a company."""

    default_filename = "company.json"

    def __init__(
        self,
        name: str = "",
        registration_country_code: str = "",
        registration_id: str = "",
        date_of_incorporation: str = "",
        financial_year_end: str = "",
        annual_return_date: str = "",
        registered_address: Address = Address(),
        vat_number: str = "",
        accounts_currency_code: str = "",
        locale: str = "",
    ):
        self.name: str = name
        self.registration_country_code: str = registration_country_code
        self.registration_id: str = registration_id
        self.date_of_incorporation: str = date_of_incorporation
        self.financial_year_end: str = financial_year_end
        self.annual_return_date: str = annual_return_date
        self.registered_address: Address = registered_address
        self.vat_number: str = vat_number
        self.accounts_currency_code: str = accounts_currency_code
        self.locale: str = locale
