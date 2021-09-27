import datetime
import os
from typing import Any, List

from flask import Markup, Response, abort, flash, render_template, request, send_file
from git import GitCommandError

from pome import app, g, git, global_pull
from pome.misc import get_recursive_json_hash
from pome.models.transaction import (
    RECORDED_TX_FOLDER_NAME,
    Amount,
    Transaction,
    TransactionLine,
)

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


@app.route("/metrics", methods=["GET"])
def metrics():
    return render_template("metrics.html")


@app.route("/eoy", methods=["GET"])
def eoy():
    return render_template("end-of-year.html")


@app.route("/eoy/transaction-profit-or-loss", methods=["GET"])
def eoy_profit_or_loss():
    narrative = "Profit or loss"
    if g.company.current_accounting_period is not None:
        narrative += " for the year ended " + g.company.current_accounting_period.end

    transaction_lines: List[TransactionLine] = []

    for acc in g.accounts_chart.accounts:
        if acc.type == "INCOME":
            transaction_lines.append(
                TransactionLine(
                    acc.code,
                    g.accounts_chart.account_profit_or_loss,
                    Amount.from_Money(acc.balance(algebrised=True)),
                )
            )
        elif acc.type == "EXPENSE":
            transaction_lines.append(
                TransactionLine(
                    g.accounts_chart.account_profit_or_loss,
                    acc.code,
                    Amount.from_Money(acc.balance(algebrised=True)),
                ),
            )

    tx_date = None
    if g.company.current_accounting_period is not None:
        tx_date = g.company.current_accounting_period.end

    to_return = Transaction(tx_date, transaction_lines, [], narrative=narrative)

    return Response(to_return.to_json(), status=200, mimetype="application/json")


@app.route("/bills")
@app.route("/bills/preset", methods=["GET", "POST"])
def bills(preset=None):
    import json
    from os import listdir
    from os.path import isfile, join

    from pome.models.encoder import PomeEncoder

    preset_list = []

    try:
        preset_list = [
            f.replace(".json", "")
            for f in listdir(join("bills", "preset"))
            if isfile(join("bills", "preset", f)) and ".json" in f
        ]
    except FileNotFoundError as e:
        print(e)

    preset_filename = None
    preset_filepath = None
    preset_transaction_bill = None
    preset_transaction_payment = None
    preset_provider = None
    if request.method == "POST":
        if "preset" in request.form:
            preset_filename = request.form["preset"]
            if preset_filename != "none":
                preset_filepath = join(
                    "bills", "preset", request.form["preset"] + ".json"
                )

                try:
                    with open(preset_filepath, "r") as f:
                        json_content = json.loads(f.read())
                        if "transactions" in json_content:
                            if "bill" in json_content["transactions"]:
                                preset_transaction_bill = PomeEncoder().encode(
                                    json_content["transactions"]["bill"]
                                )
                            if "payment" in json_content["transactions"]:
                                preset_transaction_payment = PomeEncoder().encode(
                                    json_content["transactions"]["payment"]
                                )
                        if "provider" in json_content:
                            preset_provider = json_content["provider"]

                except FileNotFoundError as e:
                    print(e)

    return render_template(
        "bills.html",
        preset_list=["none"] + preset_list,
        preset_transaction_bill=preset_transaction_bill,
        preset_transaction_payment=preset_transaction_payment,
        preset_filename=preset_filename,
        preset_provider=preset_provider,
    )


@app.route("/eoy/transactions-closing-and-opening", methods=["GET"])
def eoy_closing_and_closing():

    lines_closing: List[TransactionLine] = []
    lines_opening: List[TransactionLine] = []

    for acc in g.accounts_chart.accounts:

        winning_side = ""
        if acc.type == "ASSET_OR_LIABILITY":
            winning_side = acc.balance()[1]

        if acc.type == "ASSET" or (
            acc.type == "ASSET_OR_LIABILITY" and winning_side == "DR"
        ):
            lines_closing.append(
                TransactionLine(
                    g.accounts_chart.account_closing_balances,
                    acc.code,
                    Amount.from_Money(acc.balance(algebrised=True)),
                )
            )
            lines_opening.append(
                TransactionLine(
                    acc.code,
                    g.accounts_chart.account_closing_balances,
                    Amount.from_Money(acc.balance(algebrised=True)),
                )
            )
        elif (
            acc.type == "LIABILITY"
            or acc.type == "EQUITY"
            or (acc.type == "ASSET_OR_LIABILITY" and winning_side == "CR")
        ):
            lines_closing.append(
                TransactionLine(
                    acc.code,
                    g.accounts_chart.account_closing_balances,
                    Amount.from_Money(acc.balance(algebrised=True)),
                )
            )
            lines_opening.append(
                TransactionLine(
                    g.accounts_chart.account_closing_balances,
                    acc.code,
                    Amount.from_Money(acc.balance(algebrised=True)),
                )
            )

    tx_closing_date = None
    if g.company.current_accounting_period is not None:
        tx_closing_date = g.company.current_accounting_period.end

    tx_opening_date = None
    if g.company.current_accounting_period is not None:
        closing_date_obj = datetime.datetime.strptime(tx_closing_date, "%Y-%m-%d")
        opening_date_obj = closing_date_obj + datetime.timedelta(days=1)
        tx_opening_date = opening_date_obj.strftime("%Y-%m-%d")

    narrative_closing = "balances for the year"
    narrative_opening = "balances for the year"
    if g.company.current_accounting_period.end is not None:
        narrative_closing += " ended " + g.company.current_accounting_period.end
        narrative_opening += " started " + tx_opening_date

    closing_tx = Transaction(
        tx_closing_date, lines_closing, [], narrative="Closing " + narrative_closing
    )

    opening_tx = Transaction(
        tx_opening_date, lines_opening, [], narrative="Opening " + narrative_opening
    )

    return Response(
        closing_tx.to_json() + "\n" + opening_tx.to_json(),
        status=200,
        mimetype="application/json",
    )
