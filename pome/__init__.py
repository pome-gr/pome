import os
import os
from flask import Flask
from pome.models.company import Company
from typing import Union

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # not working

app.jinja_env.globals["CWD"] = os.getcwd()

# Loading the company from file
company: Union[Company, None] = None
try:
    with open("company.json", "r") as f:
        company = Company.from_json(f.read())
except FileNotFoundError:
    company = None

app.jinja_env.globals["company"] = company

import pome.routes
