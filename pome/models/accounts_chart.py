from typing import Dict, List, Tuple, Union

from money.currency import Currency
from money.money import Money

from pome.misc import get_longest_matching_prefix
from pome.models.encoder import PomeEncodable


class BankDetails(PomeEncodable):
    def __init__(
        self,
        bank: str = "",
        IBAN: str = "",
        BIC: str = "",
        account_number: str = "",
        sort_code: str = "",
    ):
        self.bank: str = bank
        self.IBAN: str = IBAN
        self.BIC: str = BIC
        self.account_number: str = account_number
        self.sort_code: str = sort_code


class BankAccountDetails(PomeEncodable):
    def __init__(self, code: str = "", bank_details: BankDetails = BankDetails()):
        self.code: str = code
        self.bank_details: BankDetails = bank_details

    def _post_load_json(self):
        self.bank_details = BankDetails.from_json_dict(self.bank_details)


class Account(PomeEncodable):

    ACCOUNT_TYPES = [
        "INCOME",
        "EXPENSE",
        "ASSET",
        "LIABILITY",
        "EQUITY",
        "ASSET_OR_LIABILITY",
    ]

    def __init__(
        self,
        code: str = "",
        name: str = "",
        type: str = "",
        bank_account_details: Union[BankAccountDetails, None] = None,
    ):
        self.code: str = code
        self.name: str = name

        # Valid types are specified in Account.ACCOUNT_TYPES
        self.type: str = type

        self.bank_account_details = bank_account_details

    def pretty_name(self) -> str:
        return self.code + " - " + self.name

    def is_used(self) -> bool:
        return len(self.transactions_lines()) > 0

    def transactions_lines(self, filter=""):
        """Set filter to 'DR' or 'CR' to get only those type of transactions."""
        from pome import g
        from pome.models.transaction import Transaction, TransactionLine

        to_return: List[Tuple[Transaction, TransactionLine]] = []
        for tx_id in g.recorded_transactions:
            tx: Transaction = g.recorded_transactions[tx_id]
            for line in tx.lines:
                if line.account_dr_code == self.code:
                    if filter == "":
                        to_return.append((tx, line))
                    elif filter == "DR":
                        to_return.append((tx, line))
                if line.account_cr_code == self.code:
                    if filter == "":
                        to_return.append((tx, line))
                    elif filter == "CR":
                        to_return.append((tx, line))

        return sorted(to_return, key=lambda x: x[0].id)

    def balance(
        self, formatted=False, algebrised=False
    ) -> Union[Money, str, Tuple[Money, str]]:
        from pome import g
        from pome.models.transaction import Transaction

        sum_dr = Money("0", Currency(g.company.accounts_currency_code))
        sum_cr = Money("0", Currency(g.company.accounts_currency_code))
        for tx_id in g.recorded_transactions:
            tx: Transaction = g.recorded_transactions[tx_id]
            for line in tx.lines:
                if line.account_dr_code == self.code:
                    sum_dr += line.amount.amount()
                if line.account_cr_code == self.code:
                    sum_cr += line.amount.amount()

        balance = None
        if algebrised:
            if self.type in ["INCOME", "LIABILITY", "EQUITY"]:
                balance = sum_cr - sum_dr
            else:
                balance = sum_dr - sum_cr
        else:
            if sum_cr >= sum_dr:
                winning_side = "CR"
                balance = sum_cr - sum_dr
            else:
                winning_side = "DR"
                balance = sum_dr - sum_cr

        if not formatted:
            if algebrised:
                return balance
            else:
                return balance, winning_side

        if algebrised:
            return balance.format(g.company.locale)
        else:
            return balance.format(g.company.locale) + " " + winning_side

    def _post_load_json(self):
        if self.bank_account_details is not None:
            self.bank_account_details = BankAccountDetails.from_json_dict(
                self.bank_account_details
            )


class AccountsChartSection(PomeEncodable):
    def __init__(self, prefix: str = "", name: str = ""):
        self.prefix: str = prefix
        self.name: str = name


class AccountsChart(PomeEncodable):

    default_filename = "accounts_chart.json"

    def __init__(
        self,
        sections: List[AccountsChartSection] = [],
        accounts_csv_file: Union[None, str] = None,
        accounts: List[Account] = [],
        bank_accounts_details: List[BankAccountDetails] = [],
    ):
        self.sections: List[AccountsChartSection] = sections
        self.accounts_csv_file: Union[None, str] = accounts_csv_file
        self.accounts: List[Account] = accounts
        self.bank_accounts_details: List[BankAccountDetails] = bank_accounts_details

        self.account_codes = None
        pass

    def are_all_accounts_used(self) -> bool:
        for acc in self.accounts:
            if not acc.is_used():
                return False
        return True

    def at_least_one_account_used_in_section(self, section_prefix: str) -> bool:
        if section_prefix not in self.section_account_code_map:
            return False
        for acc in self.section_account_code_map[section_prefix]:
            if self.account_codes[acc].is_used() == True:
                return True
        return False

    def is_valid_account_code(self, code: str):
        if self.account_codes is None:
            raise ValueError("Account codes map is not set in account chart object.")
        return code in self.account_codes

    def _load_accounts_from_csv_file(self, csv_file: str):
        try:
            with open(csv_file, "r") as f:
                csv_content = f.read()

            self.accounts = []

            for csv_line in csv_content.split("\n"):
                if csv_line.strip() == "":
                    continue
                csv_entries = csv_line.split(";")
                if len(csv_entries) != 3:
                    # TODO: make error appear on frontend?
                    print(f"Account csv entry invalid: {csv_line}. Ignored.")
                    continue
                code, name, type_ = list(map(str.strip, csv_entries))
                self.accounts.append(Account(code, name, type_))

        except FileNotFoundError:
            self.accounts_csv_file_error = True
            print(f"Accounts file not found! `{csv_file}`")

    def _make_acounts_code_map(self):
        self.account_codes: Dict[str, Account] = {}
        for acc in self.accounts:
            if acc.code not in self.account_codes:
                self.account_codes[acc.code] = acc
            else:
                # TODO: make error appear on frontend
                print(
                    f"Warning. Account code {acc.code} is not unique: it is at least shared by:\n {self.account_codes[acc.code]} and {acc}. Pome will only keep {self.account_codes[acc.code]}."
                )

    def _check_accounts_type(self):
        for code in self.account_codes:
            acc = self.account_codes[code]
            if acc.type not in Account.ACCOUNT_TYPES:
                # TODO: make error appear on frontend
                print(
                    f"Warning. Account type {acc.type} for account {acc} is not valid. Valid types are: {Account.ACCOUNT_TYPES}"
                )

    def prefix_level(self, prefix: str) -> int:
        """Returns the level of an account prefix in the account chart tree."""
        level = 0
        for i in range(len(prefix)):
            prefix_of = prefix[: i + 1]
            if prefix_of in self.section_prefixes_map:
                level += 1
        return level - 1

    def _make_section_account_code_map(self):
        self.section_prefixes_map = {}
        for section in self.sections:
            if not section.prefix in self.section_prefixes_map:
                self.section_prefixes_map[section.prefix] = section
            else:
                print(
                    f"Warning. Two sections shares the same prefix {section.prefix}, only the first one in order will be considered."
                )

        self.section_account_code_map = {}
        for code in self.account_codes:
            acc = self.account_codes[code]
            longest_matching_prefix = get_longest_matching_prefix(
                code, self.section_prefixes_map.keys()
            )
            if longest_matching_prefix is None:
                print(
                    f"Warning. Account {acc} belongs to no section, it wont be printed."
                )
                continue
            if not longest_matching_prefix in self.section_account_code_map:
                self.section_account_code_map[longest_matching_prefix] = []
            self.section_account_code_map[longest_matching_prefix].append(acc.code)

        for section_prefix in self.section_account_code_map:
            self.section_account_code_map[section_prefix].sort()

    def _post_load_json(self):
        self.sections = list(map(AccountsChartSection.from_json_dict, self.sections))
        self.accounts = list(map(Account.from_json_dict, self.accounts))
        self.bank_accounts_details = list(
            map(BankAccountDetails.from_json_dict, self.bank_accounts_details)
        )

        if self.accounts_csv_file is not None:
            self._load_accounts_from_csv_file(self.accounts_csv_file)

        self._make_acounts_code_map()
        self._check_accounts_type()

        self._make_section_account_code_map()

        return
