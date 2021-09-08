import os
from typing import Any, List

from flask import Markup, abort, flash, render_template, request, send_file
from git import GitCommandError

from pome import app, g, git, global_pull
from pome.misc import get_recursive_json_hash
from pome.models.transaction import RECORDED_TX_FOLDER_NAME, Transaction

LAST_HASH = get_recursive_json_hash()


@app.before_request
def check_if_sync_needed():
    if "static" in request.url:
        return
    global LAST_HASH
    the_hash = get_recursive_json_hash()
    if the_hash != LAST_HASH:
        print("Change detected, sync from disk")
        g.sync_from_disk()
    LAST_HASH = the_hash


@app.route("/")
@app.route("/accounts")
def accounts():
    return render_template("index.html")


@app.route("/accounts/<account_code>")
def account(account_code):
    if not account_code in g.accounts_chart.account_codes:
        abort(404)
    return render_template(
        "account.html", account=g.accounts_chart.account_codes[account_code]
    )


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
    if not tx_id in g.recorded_transactions:
        return abort(404)

    return render_template(
        "show_transaction.html",
        transaction=g.recorded_transactions[tx_id],
        order_recorded=Transaction.order_recorded(g.recorded_transactions)(tx_id),
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
        g.recorded_transactions[tx.id] = tx
        git.add(os.path.join(tx.get_tx_path(), "*"))
        print("Git add")
        git.commit("-m", f"Adding transaction {tx.id}", "-m", tx.commit_message())
        print("Git commit")
        print(tx.commit_message())
        if g.settings.git_communicate_with_remote:
            git.push()
            print("Git push")
    except ValueError as e:
        return str(e), 400
    except GitCommandError as e:
        return str(e), 400
    return tx.id


@app.route("/journal", methods=["GET"])
def journal():
    transactions: List[Any] = sorted(
        list(g.recorded_transactions.items()), key=lambda x: x[1].date_recorded
    )[::-1]

    return render_template(
        "journal.html",
        transactions=transactions,
        order_recorded=Transaction.order_recorded(g.recorded_transactions),
    )


@app.route("/pull", methods=["PUT"])
def pull():
    try:
        msg = global_pull()
        check_if_sync_needed()
        flash(Markup(f"Git pull successful!<br/><pre>{msg}</pre>"), "bg-green-500")
    except GitCommandError as e:
        return str(e), 400

    return "ok"
