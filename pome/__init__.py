import os
from flask import Flask
from pome.models import Company, AccountsChart, Settings

from typing import Union, Dict

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # not working

from git import Repo, InvalidGitRepositoryError, GitCommandError, Git

app.jinja_env.globals["GIT_OK"] = True
app.jinja_env.globals["GIT_PULL_ERROR"] = ""
git: Union[None, Git] = None
try:
    repo = Repo(".")
    git = repo.git
except InvalidGitRepositoryError:
    app.jinja_env.globals["GIT_OK"] = False
    git = None


def global_pull():
    try:
        print("Git pull")
        git.pull()
    except GitCommandError as e:
        app.jinja_env.globals["GIT_PULL_ERROR"] = e.stderr


settings = Settings.from_json_file("pome_settings.json", True)
if settings.git_communicate_with_remote:
    global_pull()

app.jinja_env.globals["CWD"] = os.getcwd()

# Loading the company from file
company: Union[Company, None] = Company.from_json_file("company.json")
app.jinja_env.globals["company"] = company


# Loading the account chart from file
accounts_chart: Union[AccountsChart, None] = AccountsChart.from_json_file(
    "accounts_chart.json"
)
app.jinja_env.globals["accounts_chart"] = accounts_chart

from pome.currency import (
    CURRENCY_SYMBOL,
    EXAMPLE_MONEY_INPUT,
    DECIMAL_PRECISION_FOR_CURRENCY,
)

app.jinja_env.globals["CURRENCY_SYMBOL"] = CURRENCY_SYMBOL
app.jinja_env.globals["EXAMPLE_MONEY_INPUT"] = EXAMPLE_MONEY_INPUT
app.jinja_env.globals["DECIMAL_PRECISION_FOR_CURRENCY"] = DECIMAL_PRECISION_FOR_CURRENCY

from pome.models.transaction import Transaction

recorded_transactions: Dict[
    str, Transaction
] = Transaction.fetch_all_recorded_transactions()

print(len(recorded_transactions))

import pome.routes
