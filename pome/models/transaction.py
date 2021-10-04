import os
import re
import urllib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Union

from money.currency import Currency
from money.money import Money
from werkzeug.utils import secure_filename

from pome import g
from pome.models.encoder import PomeEncodable
from pome.models.validation import validate_date

RECORDED_TX_FOLDER_NAME = os.path.join("transactions", "recorded")


class Amount(PomeEncodable):
    def __init__(self, currency_code: str, raw_amount_in_main_currency: str):
        # Putting this there to avoid circular imports
        from pome.currency import DECIMAL_PRECISION_FOR_CURRENCY

        amount_regex = re.compile(
            "^[0-9]*(\.[0-9]{0," + str(DECIMAL_PRECISION_FOR_CURRENCY) + "})?$"
        )
        if not bool(amount_regex.fullmatch(raw_amount_in_main_currency)):
            raise ValueError(
                f"Invalid payload amount {raw_amount_in_main_currency}. Decimal separator is '.' and maximum number of decimals allowed is set by the currency (EUR and USD are 2 decimals)."
            )
        self.raw_amount_in_main_currency: str = raw_amount_in_main_currency
        self.currency_code: str = currency_code

    def amount(self, formatted=False) -> Union[Money, str]:
        to_ret = Money(self.raw_amount_in_main_currency, Currency(self.currency_code))
        if not formatted:
            return to_ret
        return to_ret.format(g.company.locale)

    @classmethod
    def from_Money(cls, money: Money):
        return cls(str(money.currency.value), str(money.amount))

    @classmethod
    def from_payload(cls, payload: str):
        try:
            return cls(g.company.accounts_currency_code, payload)
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
    def __init__(
        self,
        account_dr_code: Union[str, None],
        account_cr_code: Union[str, None],
        amount: Amount,
    ):
        self.account_dr_code: Union[str, None] = account_dr_code
        self.account_cr_code: Union[str, None] = account_cr_code
        self.amount: Amount = amount

        if (
            not self.account_dr_code is None
            and not g.accounts_chart.is_valid_account_code(self.account_dr_code)
        ):
            raise ValueError(f"Invalid dr account code {self.account_dr_code }")

        if (
            not self.account_cr_code is None
            and not g.accounts_chart.is_valid_account_code(self.account_cr_code)
        ):
            raise ValueError(f"Invalid cr account code {self.account_cr_code}")

    def _post_load_json(self):
        self.amount = Amount.from_json_dict(self.amount)

    @classmethod
    def from_payload(cls, payload):
        try:
            if type(payload) != dict:
                raise ValueError(f"Invalid transaction line {payload}.")
            print(payload)
            if "account_dr" not in payload and "account_dr_code" not in payload:
                raise ValueError(f"Field `account_dr` was not set in {payload}.")
            if "account_cr" not in payload and "account_dr_code" not in payload:
                raise ValueError(f"Field `account_cr` was not set in {payload}.")

            raw_amount_in_main_currency = None
            if "raw_amount_in_main_currency" not in payload:

                if (
                    "amount" in payload
                    and "raw_amount_in_main_currency" in payload["amount"]
                ):
                    raw_amount_in_main_currency = payload["amount"][
                        "raw_amount_in_main_currency"
                    ]
                else:
                    raise ValueError(
                        f"Field `raw_amount_in_main_currency` was not set in {payload}."
                    )
            else:
                raw_amount_in_main_currency = payload["raw_amount_in_main_currency"]
            return cls(
                str(
                    payload["account_dr"]
                    if "account_dr" in payload
                    else payload["account_dr_code"]
                ),
                str(
                    payload["account_cr"]
                    if "account_cr" in payload
                    else payload["account_cr_code"]
                ),
                Amount.from_payload(raw_amount_in_main_currency),
            )
        except ValueError as e:
            raise e


class Transaction(PomeEncodable):
    """Stores all the metadata associated to a transaction."""

    default_filename = "tx.json"

    def __init__(
        self,
        date: Union[None, str],
        lines: List[TransactionLine],
        attachments: Union[
            List[TransactionAttachmentOnDisk], List[TransactionAttachmentPayload]
        ],
        narrative: str = "",
        comments: str = "",
        date_recorded: Union[None, str] = None,
        id: Union[None, str] = None,
    ):
        self.date: Union[None, str] = date

        self.lines: List[TransactionLine] = lines
        self.attachments: Union[
            List[TransactionAttachmentOnDisk], List[TransactionAttachmentPayload]
        ] = attachments
        self.date_recorded: Union[None, str] = date_recorded
        self.narrative: str = narrative
        self.comments: str = comments
        self.id: Union[None, str] = id

        if not self.date is None and not validate_date(self.date):
            raise ValueError(
                f"Invalid date {self.date}. A valid date is yyyy-mm-dd, for instance 2021-08-30."
            )

        if not self.date_recorded is None and not validate_date(
            self.date_recorded, True
        ):
            raise ValueError(
                f"Invalid record date {self.date_recorded}. A valid date record date is ISO8601, for instance 2008-08-30T01:45:36.123Z."
            )

    @classmethod
    def get_transactions_id_sorted_by_date_recorded(cls, transactions):
        return [
            tx.id
            for tx in sorted(list(transactions.values()), key=lambda x: x.date_recorded)
        ]

    @classmethod
    def order_recorded(cls, transactions):
        sorted_transactions = cls.get_transactions_id_sorted_by_date_recorded(
            transactions
        )

        def f(tx_id):
            return sorted_transactions.index(tx_id) + 1

        return f

    def _post_load_json(self):
        self.lines = list(map(TransactionLine.from_json_dict, self.lines))
        self.attachments = list(
            map(TransactionAttachmentOnDisk.from_json_dict, self.attachments)
        )

    def total_amount(self, formatted=False) -> Union[Money, str]:
        to_return = Money("0", Currency(g.company.accounts_currency_code))
        for line in self.lines:
            to_return += line.amount.amount()

        if not formatted:
            return to_return
        return to_return.format(g.company.locale)

    @classmethod
    def fetch_all_recorded_transactions(cls) -> Dict[str, "Transaction"]:
        to_return = {}
        try:
            for tx_folder in os.listdir(RECORDED_TX_FOLDER_NAME):
                tx_file = os.path.join(
                    RECORDED_TX_FOLDER_NAME, tx_folder, cls.default_filename
                )
                if not os.path.exists(tx_file):
                    continue
                to_return[tx_folder] = cls.from_json_file(tx_file)

                if tx_folder != to_return[tx_folder].id:
                    raise ValueError(
                        f"Transaction id `{to_return[tx_folder].id}` stored in `{tx_file}` does not match folder name {tx_folder}`"
                    )
        except FileNotFoundError as e:
            return {}

        return to_return

    def commit_message(self) -> str:
        to_return = self.date + "\n"
        to_return += "=" * len(self.date) + "\n"
        to_return += "lines:\n"
        for line in self.lines:
            to_return += "  " + (
                "DR "
                + g.accounts_chart.account_codes[line.account_dr_code].pretty_name()
                + "\n"
                + "\tCR "
                + g.accounts_chart.account_codes[line.account_cr_code].pretty_name()
                + "\n"
                + "  "
                + line.amount.amount().format(g.company.locale)
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

    def assign_suitable_id(self, not_in_that_list=[]) -> Union[None, str]:
        if self.id is not None:
            return self.id
        if self.date is None:
            return None
        self.id = self.date
        i = 1
        while os.path.exists(self.get_tx_path()) or (self.id in not_in_that_list):
            self.id = self.date + f"_{i}"
            i += 1
        return self.id

    def get_tx_path(self, absolute: bool = False) -> Union[None, str]:
        if self.id is None:
            return None
        if not absolute:
            return os.path.join(RECORDED_TX_FOLDER_NAME, self.id)
        else:
            return os.path.join(os.getcwd(), RECORDED_TX_FOLDER_NAME, self.id)

    def save_on_disk(self):
        if self.get_tx_path() is None:
            return
        Path(self.get_tx_path()).mkdir(parents=True, exist_ok=True)
        with open(os.path.join(self.get_tx_path(), self.default_filename), "w") as f:
            for i in range(len(self.attachments)):
                if isinstance(self.attachments[i], TransactionAttachmentPayload):
                    self.attachments[i] = self.attachments[i].save_on_disk(
                        self.get_tx_path()
                    )
            f.write(self.to_json())

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
            narrative = ""
            if "narrative" in json_payload:
                narrative = str(json_payload["narrative"])
            comments = ""
            if "comments" in json_payload:
                comments = str(json_payload["comments"])
            file_list = []
            if "files" in json_payload:
                if type(json_payload["files"]) != list:
                    raise ValueError("Invalid file payload.")
                for file in json_payload["files"]:
                    file_list.append(TransactionAttachmentPayload.from_payload(file))

            date_recorded = datetime.utcnow().isoformat() + "+00:00"
            if "date_recorded" in json_payload:
                date_recorded = json_payload["date_recorded"]
            toReturn = cls(
                date,
                lines,
                file_list,
                narrative,
                comments,
                date_recorded=date_recorded,
            )
            return toReturn
        except ValueError as e:
            raise (e)
