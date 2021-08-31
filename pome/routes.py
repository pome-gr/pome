import os

from pome import app, company
from flask import render_template, request

from pome import git, settings
from pome.models.transaction import Transaction


@app.route("/")
@app.route("/accounts")
def accounts():
    return render_template("index.html")


@app.route("/company")
def company():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500
    return render_template("company.html")


@app.route("/transaction/new")
def new_transaction():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500
    return render_template("transaction.html", transaction=None)


@app.route("/transaction/record", methods=["POST"])
def record_transaction():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500

    try:
        tx = Transaction.from_payload(request.json)
        tx.assign_suitable_id()
        tx.save_on_disk()
        git.add(os.path.join(tx.get_tx_path(), "*"))
        git.commit("-m", f"Adding transaction {tx.id}", "-m", tx.commit_message())
        print("Transaction commited\n", tx.commit_message())
        if settings.git_communicate_with_remote:
            git.push()
    except ValueError as e:
        return str(e), 400
    return "ok"
