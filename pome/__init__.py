import os
from typing import Dict, Set, Union

from flask import Flask

from pome._version import __version__
from pome.models import AccountsChart, Bill, Company, Settings, Invoice

app = Flask(__name__)
app.secret_key = b'\x9dq\x0bbE\xbaA{\xb4V`\xcaq\xb7\xcf"\x8b\xb8q\xe0\x13b\xb0\xb6'
app.config["TEMPLATES_AUTO_RELOAD"] = True  # not working

app.jinja_env.globals["POME_VERSION"] = __version__

from git import Git, GitCommandError, InvalidGitRepositoryError, Repo

app.jinja_env.globals["GIT_OK"] = True
app.jinja_env.globals["GIT_PULL_ERROR"] = ""
git: Union[None, Git] = None
try:
    repo = Repo(".")
    git = repo.git
except InvalidGitRepositoryError:
    app.jinja_env.globals["GIT_OK"] = False
    git = None
app.jinja_env.globals["CWD"] = os.getcwd()


class GlobalState(object):
    def __init__(self):
        self.settings: Union[Settings, None] = None
        self.company: Union[Company, None] = None
        self.accounts_chart: Union[AccountsChart, None] = None
        self.recorded_transactions: Union[Dict[str, "Transaction"], None] = None
        self.recorded_bills: Union[Dict[str, Bill], None] = None

    def sync_settings_from_disk(self):
        """Settings need to be load before everything else in order to interact with git."""
        self.settings = Settings.from_disk(True)

    def sync_from_disk(self):
        # Avoiding circular imports
        from pome.models.transaction import Transaction

        self.settings = Settings.from_disk(True)

        self.company = Company.from_disk()
        app.jinja_env.globals["company"] = self.company

        self.accounts_chart = AccountsChart.from_disk()
        app.jinja_env.globals["accounts_chart"] = self.accounts_chart

        self.recorded_transactions = Transaction.fetch_all_recorded_transactions()

        self.recorded_bills = Bill.fetch_all_recorded_bills()
        self.recorded_invoices = Invoice.fetch_all_recorded_invoices()


g = GlobalState()
g.sync_settings_from_disk()


def global_pull():
    try:
        print("Git pull")
        return git.pull()
    except GitCommandError as e:
        app.jinja_env.globals["GIT_PULL_ERROR"] = e.stderr


if git is not None:
    global_pull()

print("Sync state from disk")
g.sync_from_disk()

from pome.currency import (
    CURRENCY_SYMBOL,
    DECIMAL_PRECISION_FOR_CURRENCY,
    EXAMPLE_MONEY_INPUT,
)

app.jinja_env.globals["CURRENCY_SYMBOL"] = CURRENCY_SYMBOL
app.jinja_env.globals["EXAMPLE_MONEY_INPUT"] = EXAMPLE_MONEY_INPUT
app.jinja_env.globals["DECIMAL_PRECISION_FOR_CURRENCY"] = DECIMAL_PRECISION_FOR_CURRENCY

import pome.routes
import pome.test_routes
