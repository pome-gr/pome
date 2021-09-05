from money.currency import Currency, CurrencyHelper

from pome import g

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

DECIMAL_PRECISION_FOR_CURRENCY = CurrencyHelper().decimal_precision_for_currency(
    Currency(g.company.accounts_currency_code)
)

EXAMPLE_MONEY_INPUT = "0." + DECIMAL_PRECISION_FOR_CURRENCY * "0"
# EXAMPLE_CURRENCY = (
#     "Enter "
#     + SUB_UNITS
#     + " for "
#     + Money(SUB_UNITS, Currency(company.accounts_currency_code)).format(company.locale)
# )
