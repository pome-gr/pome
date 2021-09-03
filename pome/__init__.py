import os
from typing import Dict, Set, Union

from flask import Flask

from pome.models import AccountsChart, Company, Settings

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # not working

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

    def sync_from_disk(self):
        from pome.models.transaction import Transaction

        self.settings = Settings.from_disk(True)

        self.company = Company.from_disk()
        app.jinja_env.globals["company"] = self.company

        self.accounts_chart = AccountsChart.from_disk()
        app.jinja_env.globals["accounts_chart"] = self.accounts_chart

        self.recorded_transactions = Transaction.fetch_all_recorded_transactions()


g = GlobalState()
g.sync_from_disk()


def global_pull():
    try:
        print("Git pull")
        git.pull()
    except GitCommandError as e:
        app.jinja_env.globals["GIT_PULL_ERROR"] = e.stderr


if g.settings.git_communicate_with_remote:
    global_pull()

from pome.currency import (CURRENCY_SYMBOL, DECIMAL_PRECISION_FOR_CURRENCY,
                           EXAMPLE_MONEY_INPUT)

app.jinja_env.globals["CURRENCY_SYMBOL"] = CURRENCY_SYMBOL
app.jinja_env.globals["EXAMPLE_MONEY_INPUT"] = EXAMPLE_MONEY_INPUT
app.jinja_env.globals["DECIMAL_PRECISION_FOR_CURRENCY"] = DECIMAL_PRECISION_FOR_CURRENCY

import pome.routes
import pome.test_routes
