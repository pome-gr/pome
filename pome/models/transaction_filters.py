from pome.models.transaction import Transaction
import datetime


def temporal_filter_factory(date_low: str, date_high: str, date_format="%Y-%m-%d"):
    def temporal_filter(tx: Transaction):
        """Returns true if tx.date >= date_low and < date_high"""
        datetime_low = datetime.datetime.strptime(date_low, date_format)
        datetime_high = datetime.datetime.strptime(date_high, date_format)
        datetime_tx = datetime.datetime.strptime(tx.date, date_format)
        return datetime_tx >= datetime_low and datetime_tx < datetime_high

    return temporal_filter
