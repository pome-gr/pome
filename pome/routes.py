from pome import app, company
from flask import render_template, request


@app.route("/")
@app.route("/accounts")
def accounts():
    return render_template("index.html")


@app.route("/company")
def company():
    return render_template("company.html")


@app.route("/transaction/new")
def new_transaction():
    return render_template("transaction.html", transaction=None)


@app.route("/transaction/record", methods=["POST"])
def record_transaction():
    print(request.json)
    return "Not good", 400
