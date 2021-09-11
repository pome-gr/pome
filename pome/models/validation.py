import re

regex_date = re.compile("^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$")
regex_ISO8601 = re.compile(
    "^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$"
)


def validate_date(date_str, ISO8601=False) -> bool:
    p = regex_date if not ISO8601 else regex_ISO8601
    return bool(p.fullmatch(date_str))
