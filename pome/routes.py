import datetime
import os
from pome.models.encoder import PomeEncoder
from typing import Any, List

from flask import Markup, Response, abort, flash, render_template, request, send_file
from git import GitCommandError

from pome import app, g, git, global_pull
from pome.misc import get_recursive_json_hash
from pome.models.bill import Bill
from pome.models.invoice import Invoice
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


@app.route("/invoices/pay/<invoice_id>", methods=["POST"])
def pay_invoice(invoice_id):
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500

    if not invoice_id in g.recorded_invoices:
        return f"Invoice ID {invoice_id} is not valid.", 400

    if g.recorded_invoices[invoice_id].status == "paid":
        return f"Invoice {invoice_id} is already paid.", 400

    try:
        invoice_data = request.json
        print(invoice_data)

        tx_payment = Transaction.from_payload(invoice_data["transactions"]["payment"])
        tx_payment.assign_suitable_id()
        tx_payment.save_on_disk()

        g.recorded_invoices[invoice_id].transactions["payment"] = tx_payment.id
        g.recorded_invoices[invoice_id].status = "paid"

        g.recorded_invoices[invoice_id].save_on_disk()

        print("Git add")
        git.add(os.path.join(tx_payment.get_tx_path(), "*"))
        git.add(os.path.join(g.recorded_invoices[invoice_id].get_invoice_filepath()))

        commit_message = "Invoice being paid:\n" + invoice_id
        commit_message += (
            "Invoice number:\n" + g.recorded_invoices[invoice_id].invoice_number
        )
        commit_message += "\n\nPayment transaction:\n" + tx_payment.commit_message()

        git.commit(
            "-m", f"Receiving payment for invoice {invoice_id}", "-m", commit_message
        )
        print("Git commit")
        print(commit_message)
        if g.settings.git_communicate_with_remote:
            git.push()
            print("Git push")
    except ValueError as e:
        return str(e), 400
    except GitCommandError as e:
        return str(e), 400

    return invoice_id


@app.route("/bills/pay/<bill_id>", methods=["POST"])
def pay_bill(bill_id):
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500

    if not bill_id in g.recorded_bills:
        return f"Bill ID {bill_id} is not valid.", 400

    if g.recorded_bills[bill_id].status == "paid":
        return f"Bill {bill_id} is already paid.", 400

    try:
        bill_data = request.json
        print(bill_data)

        tx_payment = Transaction.from_payload(bill_data["transactions"]["payment"])
        tx_payment.assign_suitable_id()
        tx_payment.save_on_disk()

        g.recorded_bills[bill_id].transactions["payment"] = tx_payment.id
        g.recorded_bills[bill_id].status = "paid"

        g.recorded_bills[bill_id].save_on_disk()

        print("Git add")
        git.add(os.path.join(tx_payment.get_tx_path(), "*"))
        git.add(os.path.join(g.recorded_bills[bill_id].get_bill_filepath()))

        commit_message = "Bill being paid:\n" + bill_id
        commit_message += "\n\nPayment transaction:\n" + tx_payment.commit_message()

        git.commit("-m", f"Paying bill {bill_id}", "-m", commit_message)
        print("Git commit")
        print(commit_message)
        if g.settings.git_communicate_with_remote:
            git.push()
            print("Git push")
    except ValueError as e:
        return str(e), 400
    except GitCommandError as e:
        return str(e), 400

    return bill_id


@app.route("/bills/record", methods=["POST"])
def record_bill():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500

    try:
        bill_data = request.json

        tx_bill = Transaction.from_payload(bill_data["transactions"]["bill"])
        tx_bill.assign_suitable_id()

        tx_payment = None
        if bill_data["status"] == "paid":
            tx_payment = Transaction.from_payload(bill_data["transactions"]["payment"])
            tx_payment.assign_suitable_id([tx_bill.id])

        if bill_data["provider"].strip() == "":
            return "You must assign a provider to the bill.", 400

        bill = Bill(
            tx_bill.id,
            bill_data["status"],
            bill_data["provider"],
            {
                "bill": tx_bill.id,
                "payment": tx_payment.id
                if tx_payment is not None
                else bill_data["transactions"]["payment"],
            },
        )

        tx_bill.save_on_disk()
        g.recorded_transactions[tx_bill.id] = tx_bill

        if tx_payment is not None:
            tx_payment.save_on_disk()
            g.recorded_transactions[tx_payment.id] = tx_payment

        bill.save_on_disk()
        print(bill.id)
        g.recorded_bills[bill.id] = bill
        print(g.recorded_bills)

        print("Git add")
        git.add(os.path.join(tx_bill.get_tx_path(), "*"))
        if tx_payment is not None:
            git.add(os.path.join(tx_payment.get_tx_path(), "*"))

        git.add(os.path.join(bill.get_bill_filepath()))

        commit_message = "Bill date:\n" + tx_bill.date
        commit_message += "Bill provider:\n" + bill.provider
        commit_message += "Bill transaction:\n" + tx_bill.commit_message()
        if tx_payment is not None:
            commit_message += "\n\nPayment transaction:\n" + tx_payment.commit_message()

        git.commit("-m", f"Adding bill {bill.id}", "-m", commit_message)
        print("Git commit")
        print(commit_message)
        if g.settings.git_communicate_with_remote:
            git.push()
            print("Git push")
    except ValueError as e:
        return str(e), 400
    except GitCommandError as e:
        return str(e), 400

    return bill.id


@app.route("/invoices/record", methods=["POST"])
def record_invoice():
    if not app.jinja_env.globals["GIT_OK"]:
        return "The server is not a valid git repository.", 500

    try:
        invoice_data = request.json
        print(invoice_data)
        tx_bill = Transaction.from_payload(invoice_data["transactions"]["bill"])
        tx_bill.assign_suitable_id()

        tx_payment = None
        if invoice_data["status"] == "paid":
            tx_payment = Transaction.from_payload(
                invoice_data["transactions"]["payment"]
            )
            tx_payment.assign_suitable_id([tx_bill.id])

        if invoice_data["invoice_number"].strip() == "":
            return "You must assign an invoice number to the invoice.", 400

        if invoice_data["client"].strip() == "":
            return "You must assign a client to the bill.", 400

        invoice = Invoice(
            tx_bill.id,
            invoice_data["invoice_number"],
            invoice_data["status"],
            invoice_data["client"],
            invoice_data["tags"],
            {
                "bill": tx_bill.id,
                "payment": tx_payment.id
                if tx_payment is not None
                else invoice_data["transactions"]["payment"],
            },
            {"invoice_payload": invoice_data["metadata"]["invoice_payload"]},
        )

        tx_bill.save_on_disk()
        g.recorded_transactions[tx_bill.id] = tx_bill

        if tx_payment is not None:
            tx_payment.save_on_disk()
            g.recorded_transactions[tx_payment.id] = tx_payment

        invoice.save_on_disk()
        print(invoice.id)
        g.recorded_invoices[invoice.id] = invoice
        print(g.recorded_invoices)

        print("Git add")
        git.add(os.path.join(tx_bill.get_tx_path(), "*"))
        if tx_payment is not None:
            git.add(os.path.join(tx_payment.get_tx_path(), "*"))

        git.add(os.path.join(invoice.get_invoice_filepath()))

        commit_message = "Invoice date:\n" + tx_bill.date
        commit_message += "Invoice client:\n" + invoice.client
        commit_message += "Invoice tags:\n" + ", ".join(invoice.tags)
        commit_message += "Invoice transaction:\n" + tx_bill.commit_message()
        if tx_payment is not None:
            commit_message += "\n\nPayment transaction:\n" + tx_payment.commit_message()

        git.commit("-m", f"Adding invoice {invoice.id}", "-m", commit_message)
        print("Git commit")
        print(commit_message)
        if g.settings.git_communicate_with_remote:
            git.push()
            print("Git push")

        if (
            "invoice_counter_increment" in invoice_data
            and invoice_data["invoice_counter_increment"]
        ):
            g.company.current_invoice_counter += 1
            g.company.save_on_disk()

    except ValueError as e:
        return str(e), 400
    except GitCommandError as e:
        return str(e), 400

    return invoice.id


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


@app.route("/invoices")
@app.route("/invoices/")
def invoices():

    all_transactions = g.recorded_transactions

    pending_invoices: List[Any] = sorted(
        list(
            filter(
                lambda x: x[1].status == "pending", list(g.recorded_invoices.items())
            )
        ),
        key=lambda x: x[1].id,
    )[::-1]

    print(pending_invoices)

    paid_invoices: List[Any] = sorted(
        list(
            filter(lambda x: x[1].status == "paid", list(g.recorded_invoices.items()))
        ),
        key=lambda x: x[1].id,
    )[::-1]

    return render_template(
        "invoices.html",
        all_transactions=all_transactions,
        pending_invoices=pending_invoices,
        paid_invoices=paid_invoices,
    )


@app.route("/bills")
@app.route("/bills/")
def bills():

    all_transactions = g.recorded_transactions

    pending_bills: List[Any] = sorted(
        list(
            filter(lambda x: x[1].status == "pending", list(g.recorded_bills.items()))
        ),
        key=lambda x: x[1].id,
    )[::-1]

    paid_bills: List[Any] = sorted(
        list(filter(lambda x: x[1].status == "paid", list(g.recorded_bills.items()))),
        key=lambda x: x[1].id,
    )[::-1]

    return render_template(
        "bills.html",
        all_transactions=all_transactions,
        pending_bills=pending_bills,
        paid_bills=paid_bills,
    )


@app.route("/bills/recorded/<bill_id>")
def show_bill(bill_id):
    if not bill_id in g.recorded_bills:
        return f"Bill {bill_id} does not exists.", 404
    bill = g.recorded_bills[bill_id]

    textarea_payment_height = 15
    if bill.status == "pending":
        textarea_payment_height = bill.transactions["payment"].count("\n") + 1

    return render_template(
        "show_bill.html",
        bill=bill,
        all_transactions=g.recorded_transactions,
        bill_pending=bill.status == "pending",
        textarea_bill_height=15,
        textarea_payment_height=textarea_payment_height,
    )


@app.route("/invoices/recorded/<invoice_id>")
def show_invoice(invoice_id):
    if not invoice_id in g.recorded_invoices:
        return f"Invoice {invoice_id} does not exists.", 404
    invoice = g.recorded_invoices[invoice_id]

    textarea_payment_height = 15
    if invoice.status == "pending":
        textarea_payment_height = invoice.transactions["payment"].count("\n") + 1

    return render_template(
        "show_invoice.html",
        invoice=invoice,
        all_transactions=g.recorded_transactions,
        invoice_pending=invoice.status == "pending",
        textarea_bill_height=15,
        doc_filler_URL=g.settings.doc_filler_URL,
        textarea_payment_height=textarea_payment_height,
        formatted_invoice_payload=PomeEncoder().encode(
            invoice.metadata["invoice_payload"]
        ),
        textarea_meta_invoice_height=PomeEncoder()
        .encode(invoice.metadata["invoice_payload"])
        .count("\n")
        + 1,
    )


@app.route("/bills/new")
@app.route("/bills/new/preset", methods=["GET", "POST"])
def new_bills():
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

    textarea_bill_height = 15
    textarea_payment_height = 15

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
                                textarea_bill_height = (
                                    preset_transaction_bill.count("\n") + 1
                                )
                            if "payment" in json_content["transactions"]:
                                preset_transaction_payment = PomeEncoder().encode(
                                    json_content["transactions"]["payment"]
                                )
                                textarea_payment_height = (
                                    preset_transaction_payment.count("\n") + 1
                                )
                        if "provider" in json_content:
                            preset_provider = json_content["provider"]

                except FileNotFoundError as e:
                    print(e)

    return render_template(
        "new_bill.html",
        preset_list=["none"] + preset_list,
        preset_transaction_bill=preset_transaction_bill,
        preset_transaction_payment=preset_transaction_payment,
        preset_filename=preset_filename,
        preset_provider=preset_provider,
        textarea_bill_height=textarea_bill_height,
        textarea_payment_height=textarea_payment_height,
    )


@app.route("/invoices/new")
@app.route("/invoices/new/preset", methods=["GET", "POST"])
def new_invoices():
    import json
    from os import listdir
    from os.path import isfile, join

    from pome.models.encoder import PomeEncoder

    preset_list = []

    try:
        preset_list = [
            f.replace(".json", "")
            for f in listdir(join("invoices", "preset"))
            if isfile(join("invoices", "preset", f)) and ".json" in f
        ]
    except FileNotFoundError as e:
        print(e)

    textarea_bill_height = 15
    textarea_payment_height = 15
    textarea_meta_invoice_height = 15

    preset_filename = None
    preset_filepath = None
    preset_transaction_bill = None
    preset_transaction_payment = None
    preset_meta_invoice_payload = None
    preset_client = None
    preset_tags = None
    if request.method == "POST":
        if "preset" in request.form:
            preset_filename = request.form["preset"]
            if preset_filename != "none":
                preset_filepath = join(
                    "invoices", "preset", request.form["preset"] + ".json"
                )

                try:
                    with open(preset_filepath, "r") as f:
                        json_content = json.loads(f.read())
                        if "transactions" in json_content:
                            if "bill" in json_content["transactions"]:
                                preset_transaction_bill = PomeEncoder().encode(
                                    json_content["transactions"]["bill"]
                                )
                                textarea_bill_height = (
                                    preset_transaction_bill.count("\n") + 1
                                )
                            if "payment" in json_content["transactions"]:
                                preset_transaction_payment = PomeEncoder().encode(
                                    json_content["transactions"]["payment"]
                                )
                                textarea_payment_height = (
                                    preset_transaction_payment.count("\n") + 1
                                )
                        if "client" in json_content:
                            preset_client = json_content["client"]
                        if "tags" in json_content:
                            preset_tags = ",".join(json_content["tags"])
                        if (
                            "metadata" in json_content
                            and "invoice_payload" in json_content["metadata"]
                        ):
                            preset_meta_invoice_payload = PomeEncoder().encode(
                                json_content["metadata"]["invoice_payload"],
                            )
                            textarea_meta_invoice_height = (
                                preset_meta_invoice_payload.count("\n") + 1
                            )

                except FileNotFoundError as e:
                    print(e)

    return render_template(
        "new_invoice.html",
        preset_list=["none"] + preset_list,
        preset_transaction_bill=preset_transaction_bill,
        preset_transaction_payment=preset_transaction_payment,
        preset_meta_invoice_payload=preset_meta_invoice_payload,
        preset_filename=preset_filename,
        preset_client=preset_client,
        preset_tags=preset_tags,
        textarea_bill_height=textarea_bill_height,
        textarea_payment_height=textarea_payment_height,
        textarea_meta_invoice_height=textarea_meta_invoice_height,
        doc_filler_URL=g.settings.doc_filler_URL,
        preset_invoice_number=g.company.get_current_invoice_number(),
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
