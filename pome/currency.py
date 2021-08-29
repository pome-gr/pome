from pome import company
from money.currency import Currency, CurrencyHelper
from money.money import Money

CURRENCY_SYMBOL = {
    "USD": "$",  # US Dollar
    "EUR": "€",  # Euro
    "CRC": "₡",  # Costa Rican Colón
    "GBP": "£",  # British Pound Sterling
    "ILS": "₪",  # Israeli New Sheqel
    "INR": "₹",  # Indian Rupee
    "JPY": "¥",  # Japanese Yen
    "KRW": "₩",  # South Korean Won
    "NGN": "₦",  # Nigerian Naira
    "PHP": "₱",  # Philippine Peso
    "PLN": "zł",  # Polish Zloty
    "PYG": "₲",  # Paraguayan Guarani
    "THB": "฿",  # Thai Baht
    "UAH": "₴",  # Ukrainian Hryvnia
    "VND": "₫",  # Vietnamese Dong
}

EXAMPLE_MONEY_INPUT = (
    "24."
    + CurrencyHelper().decimal_precision_for_currency(
        Currency(company.accounts_currency_code)
    )
    * "2"
)
# EXAMPLE_CURRENCY = (
#     "Enter "
#     + SUB_UNITS
#     + " for "
#     + Money(SUB_UNITS, Currency(company.accounts_currency_code)).format(company.locale)
# )
