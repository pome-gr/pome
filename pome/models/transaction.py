import re

from flask.scaffold import F
from pome.models.encoder import PomeEncodable
from typing import Tuple, Union, List, Dict
from money.money import Money
from money.currency import Currency
from pathlib import Path

import urllib

import os

from pome import company, accounts_chart
from pome.currency import DECIMAL_PRECISION_FOR_CURRENCY

from werkzeug.utils import secure_filename

RECORDED_TX_FOLDER_NAME = os.path.join("transactions", "recorded")


class Amount(PomeEncodable):
    amount_regex = re.compile(
        "^[0-9]*(\.[0-9]{0," + str(DECIMAL_PRECISION_FOR_CURRENCY) + "})?$"
    )

    def __init__(self, currency_code: str, raw_amount_in_main_currency: str):
        if not bool(self.amount_regex.fullmatch(raw_amount_in_main_currency)):
            raise ValueError(
                f"Invalid payload amount {raw_amount_in_main_currency}. Decimal separator is '.' and maximum number of decimals allowed is set by the currency (EUR and USD are 2 decimals)."
            )
        self.raw_amount_in_main_currency: str = raw_amount_in_main_currency
        self.currency_code: str = currency_code

    def amount(self) -> Money:
        return Money(self.raw_amount_in_main_currency, Currency(self.currency_code))

    def formatted_amount(self) -> str:
        return self.amount().format(company.locale)

    @classmethod
    def from_payload(cls, payload: str):
        try:
            return cls(company.accounts_currency_code, payload)
        except ValueError as e:
            raise e


class TransactionAttachmentOnDisk(PomeEncodable):
    def __init__(self, filename: str, filepath: str):
        self.filename = filename
        self.filepath = filepath


class TransactionAttachmentPayload(PomeEncodable):
    def __init__(self, filename: str, b64_content: str):
        self.filename = filename
        self.b64_content = b64_content

    def save_on_disk(self, tx_path: str) -> TransactionAttachmentOnDisk:
        filepath = os.path.join(tx_path, self.filename)
        response = urllib.request.urlopen(self.b64_content)
        with open(filepath, "wb") as f:
            f.write(response.file.read())
        return TransactionAttachmentOnDisk(self.filename, filepath)

    @classmethod
    def from_payload(cls, payload):
        try:
            if not "filename" in payload:
                raise ValueError("Field `filename` was not set in attached file.")
            if not "b64_content" in payload:
                raise ValueError("Filed `b64_content` was not set in attached file.")
            return cls(secure_filename(payload["filename"]), payload["b64_content"])
        except ValueError as e:
            raise e


class TransactionLine(PomeEncodable):
    def __init__(self, account_dr_code: str, account_cr_code: str, amount: Amount):
        self.account_dr_code: str = account_dr_code
        self.account_cr_code: str = account_cr_code
        self.amount: Amount = amount

        if not accounts_chart.is_valid_account_code(self.account_dr_code):
            raise ValueError(f"Invalid dr account code {self.account_dr_code }")

        if not accounts_chart.is_valid_account_code(self.account_cr_code):
            raise ValueError(f"Invalid cr account code {self.account_cr_code}")

    def _post_load_json(self):
        self.amount = Amount.from_json_dict(self.amount)

    @classmethod
    def from_payload(cls, payload):
        try:
            if type(payload) != dict:
                raise ValueError(f"Invalid transaction line {payload}.")
            if "account_dr" not in payload:
                raise ValueError(f"Field `account_dr` was not set in {payload}.")
            if "account_cr" not in payload:
                raise ValueError(f"Field `account_cr` was not set in {payload}.")
            if "raw_amount_in_main_currency" not in payload:
                raise ValueError(
                    f"Field `raw_amount_in_main_currency` was not set in {payload}."
                )
            return cls(
                str(payload["account_dr"]),
                str(payload["account_cr"]),
                Amount.from_payload(payload["raw_amount_in_main_currency"]),
            )
        except ValueError as e:
            raise e


class Transaction(PomeEncodable):
    """Stores all the metadata associated to a transaction."""

    def __init__(
        self,
        date: Union[None, str],
        lines: List[TransactionLine],
        attachments: Union[
            List[TransactionAttachmentOnDisk], List[TransactionAttachmentPayload]
        ],
        narrative: str = "",
        comments: str = "",
        files_on_disk: bool = True,
        id: Union[None, str] = None,
    ):
        self.date: Union[None, str] = date
        self.lines: List[TransactionLine] = lines
        self.attachments: Union[
            List[TransactionAttachmentOnDisk], List[TransactionAttachmentPayload]
        ] = attachments
        self.narrative: str = narrative
        self.comments: str = comments
        self.id: Union[None, str] = id
        self.files_on_disk: bool = files_on_disk

        if not self.validate_date(self.date):
            raise ValueError(
                f"Invalid date {self.date}. A valid date is yyyy-mm-dd, for instance 2021-08-30."
            )

    def _post_load_json(self):
        self.lines = list(map(TransactionLine.from_json_dict, self.lines))
        self.attachments = list(
            map(TransactionAttachmentOnDisk.from_json_dict, self.attachments)
        )

    @classmethod
    def fetch_all_recorded_transactions(cls) -> Dict[str, "Transaction"]:
        to_return = {}
        for tx_folder in os.listdir(RECORDED_TX_FOLDER_NAME):
            tx_file = os.path.join(RECORDED_TX_FOLDER_NAME, tx_folder, "tx.json")
            if not os.path.exists(tx_file):
                continue
            to_return[tx_folder] = cls.from_json_file(tx_file)

        return to_return

    def commit_message(self) -> str:
        to_return = self.date + "\n"
        to_return += "=" * len(self.date) + "\n"
        to_return += "lines:\n"
        for line in self.lines:
            to_return += "  " + (
                "DR "
                + accounts_chart.account_codes[line.account_dr_code].pretty_name()
                + "\n"
                + "\tCR "
                + accounts_chart.account_codes[line.account_cr_code].pretty_name()
                + "\n"
                + "  "
                + line.amount.amount().format(company.locale)
                + "\n\n"
            )

        if self.narrative != "":
            to_return += "narrative:" + "\n"
            to_return += "  " + self.narrative + "\n"

        if self.comments != "":
            to_return += "\n" + "comments:" + "\n"
            to_return += "  " + self.comments + "\n"

        if len(self.attachments) != 0:
            to_return += "\n" + "attachments:" + "\n"
            for file in self.attachments:
                to_return += f"  - {file.filepath}\n"

        return to_return

    def assign_suitable_id(self) -> Union[None, str]:
        if self.id is not None:
            return self.id
        if self.date is None:
            return None
        self.id = self.date
        i = 1
        while os.path.exists(self.get_tx_path()):
            self.id = self.date + f"_{i}"
            i += 1
        return self.id

    def get_tx_path(self) -> Union[None, str]:
        if self.id is None:
            return None
        return os.path.join(RECORDED_TX_FOLDER_NAME, self.id)

    def save_on_disk(self):
        if self.get_tx_path() is None:
            return
        Path(self.get_tx_path()).mkdir(parents=True, exist_ok=True)
        with open(os.path.join(self.get_tx_path(), f"tx.json"), "w") as f:
            if not self.files_on_disk:
                for i in range(len(self.attachments)):
                    self.attachments[i] = self.attachments[i].save_on_disk(
                        self.get_tx_path()
                    )
                self.files_on_disk = True
            f.write(self.to_json())

    @classmethod
    def validate_date(cls, date_str):
        p = re.compile("^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$")
        return bool(p.fullmatch(date_str))

    @classmethod
    def from_payload(cls, json_payload):
        try:
            if not "date" in json_payload:
                raise ValueError(f"Field `date` was not set. Format is yyyy-mm-dd.")
            date = json_payload["date"]
            if not "lines" in json_payload:
                raise ValueError("No transaction lines specified.")
            lines = []
            for line in json_payload["lines"]:
                try:
                    tx_line = TransactionLine.from_payload(line)
                    lines.append(tx_line)
                except ValueError as e:
                    raise e
            if "narrative" in json_payload:
                narrative = str(json_payload["narrative"])
            if "comments" in json_payload:
                comments = str(json_payload["comments"])
            file_list = []
            if "files" in json_payload:
                if type(json_payload["files"]) != list:
                    raise ValueError("Invalid file payload.")
                for file in json_payload["files"]:
                    file_list.append(TransactionAttachmentPayload.from_payload(file))
            toReturn = cls(
                date, lines, file_list, narrative, comments, files_on_disk=False
            )
            return toReturn
        except ValueError as e:
            raise (e)
