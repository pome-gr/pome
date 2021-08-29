from typing import List, Union
from pome.models.encoder import PomeEncodable
from pome.misc import get_longest_matching_prefix


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
        "COST",
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
    def __init__(
        self,
        sections: List[AccountsChartSection] = [],
        accounts_csv_file: Union[None, str] = None,
        accounts: List[Account] = [],
        bank_accounts_details: List[BankAccountDetails] = [],
    ):
        self.sections: List[AccountsChartSection] = sections
        self.accounts_csv_file: str = accounts_csv_file
        self.accounts: List[Account] = accounts
        self.bank_accounts_details: List[BankAccountDetails] = bank_accounts_details
        pass

    def _load_accounts_from_csv_file(self, csv_file: str):
        try:
            with open(csv_file, "r") as f:
                csv_content = f.read()

            self.accounts = []

            for csv_line in csv_content.split("\n"):
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
        self.account_codes = {}
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
