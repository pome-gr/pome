from pome.models.address import Address
from pome.models.encoder import PomeEncodable
from pome.models.validation import validate_date
from typing import Union


class AccountingPeriod(PomeEncodable):
    def __init__(self, begin: str, end: str):
        self.begin = begin
        self.end = end

        if not validate_date(self.begin):
            raise ValueError(
                f"Invalid date {self.begin}. A valid date is yyyy-mm-dd, for instance 2021-08-30."
            )

        if not validate_date(self.end):
            raise ValueError(
                f"Invalid date {self.end}. A valid date is yyyy-mm-dd, for instance 2021-08-30."
            )


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
        current_accounting_period: Union[AccountingPeriod, None] = None,
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
        self.current_accounting_period = current_accounting_period

    def _post_load_json(self):
        if self.current_accounting_period:
            self.current_accounting_period = AccountingPeriod.from_json_dict(
                self.current_accounting_period
            )
