import os

from pome import app, company
from flask import render_template, request, send_file

from pome import git, settings, recorded_transactions
from pome.models import transaction
from pome.models.transaction import RECORDED_TX_FOLDER_NAME, Transaction

from git import GitCommandError


@app.route("/")
@app.route("/accounts")
def accounts():
    return render_template("index.html")


@app.route("/company")
def company():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500
    return render_template("company.html")


@app.route("/transactions/new")
def new_transaction():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500
    return render_template("new_transaction.html", transaction=None)


@app.route("/transactions/recorded/<tx_id>")
def show_transaction(tx_id):
    if not tx_id in recorded_transactions:
        return "", 404

    print(recorded_transactions[tx_id])
    return render_template(
        "show_transaction.html", transaction=recorded_transactions[tx_id]
    )


@app.route("/transactions/recorded/<tx_id>/<filename>")
def get_transaction_attachment(tx_id, filename):
    absolute_filepath = os.path.join(
        os.getcwd(), RECORDED_TX_FOLDER_NAME, tx_id, filename
    )

    resp = send_file(absolute_filepath, download_name=filename)
    return resp


@app.route("/transactions/record", methods=["POST"])
def record_transaction():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500

    try:
        tx = Transaction.from_payload(request.json)
        tx.assign_suitable_id()
        tx.save_on_disk()
        recorded_transactions[tx.id] = tx
        git.add(os.path.join(tx.get_tx_path(), "*"))
        print("Git add")
        git.commit("-m", f"Adding transaction {tx.id}", "-m", tx.commit_message())
        print("Git commit")
        print(tx.commit_message())
        if settings.git_communicate_with_remote:
            git.push()
            print("Git push")
    except ValueError as e:
        return str(e), 400
    except GitCommandError as e:
        return str(e), 400
    return "ok"
