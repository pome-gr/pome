from pome import app, company
from pome.models.address import Address
from pome.models.company import Company
from flask import render_template


@app.route("/")
@app.route("/accounts")
def accounts():
    return render_template("index.html")


@app.route("/company")
def company():
    return render_template("company.html")
