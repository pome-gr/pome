from pome import app


@app.route("/test/add-random-tx", methods=["GET"])
@app.route("/test/add-random-tx/<int:nb_tx>", methods=["GET"])
def add_random_simple_transactions(nb_tx=1):
    import random
    import time
    from datetime import datetime, timedelta

    import requests
    from lorem_text import lorem

    def str_time_prop(start, end, time_format, prop):
        """Get a time at a proportion of a range of two formatted times.

        start and end should be strings specifying times formatted in the
        given format (strftime-style), giving an interval [start, end].
        prop specifies how a proportion of the interval to be taken after
        start.  The returned time will be in the specified format.
        """

        stime = time.mktime(time.strptime(start, time_format))
        etime = time.mktime(time.strptime(end, time_format))

        ptime = stime + prop * (etime - stime)

        return time.strftime(time_format, time.localtime(ptime))

    def random_date(start, end, prop):
        return str_time_prop(start, end, "%Y-%m-%d", prop)

    for _ in range(nb_tx):
        amount = random.randint(0, 100000)
        payload = {}
        if random.randint(0, 1) == 1:
            tx_line = {
                "account_dr": "2000",
                "account_cr": "6003",
                "raw_amount_in_main_currency": str(amount / 100),
            }
        else:
            tx_line = {
                "account_dr": "6003",
                "account_cr": "0400",
                "raw_amount_in_main_currency": str(amount / 100),
            }
        payload["lines"] = [tx_line]
        yesterday = datetime.now() - timedelta(1)
        tx_date = random_date(
            "2021-01-01", datetime.strftime(yesterday, "%Y-%m-%d"), random.random()
        )
        payload["date"] = tx_date
        record_date = random_date(
            tx_date, datetime.strftime(yesterday, "%Y-%m-%d"), random.random()
        )
        payload["date_recorded"] = record_date + "T01:45:36.123Z"

        narrative = ""
        if random.randint(0, 1) == 1:
            narrative = lorem.words(13)
        payload["narrative"] = narrative

        r = requests.post("http://localhost:5000/transactions/record", json=payload)

    return "ok"
