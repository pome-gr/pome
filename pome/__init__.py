import os
import os
from flask import Flask
from pome.models import Company, AccountsChart
from typing import Union

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # not working

app.jinja_env.globals["CWD"] = os.getcwd()

# Loading the company from file
company: Union[Company, None] = Company.from_json_file("company.json")
app.jinja_env.globals["company"] = company

# Loading the account chart from file
accounts_chart: Union[AccountsChart, None] = AccountsChart.from_json_file(
    "accounts_chart.json"
)
app.jinja_env.globals["accounts_chart"] = accounts_chart

import pome.routes
