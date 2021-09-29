import os
from typing import Dict, Union
from pathlib import Path
from pome.models.encoder import PomeEncodable

RECORDED_BILL_FOLDER_NAME = os.path.join("bills", "recorded")


class Bill(PomeEncodable):
    """Stores all the metadata associated to a bill."""

    def __init__(
        self,
        id: Union[None, str] = None,
        status: str = "pending",
        provider: str = "",
        transactions: Dict[str, str] = {},
    ):
        self.id: Union[None, str] = id
        self.status: str = status
        self.provider: str = provider
        self.transactions: Dict[str, str] = transactions

    @classmethod
    def fetch_all_recorded_bills(cls) -> Dict[str, "Bill"]:
        to_return = {}
        try:
            for bill_file in os.listdir(RECORDED_BILL_FOLDER_NAME):
                if ".json" not in bill_file:
                    continue
                bill_path = os.path.join(RECORDED_BILL_FOLDER_NAME, bill_file)
                if not os.path.exists(bill_path):
                    continue

                bill_id = bill_file.replace(".json", "")
                to_return[bill_id] = cls.from_json_file(bill_path)

                if bill_file != to_return[bill_id].id + ".json":
                    raise ValueError(
                        f"Bill id `{to_return[bill_id].id}` stored in `{bill_path}` does not match file name {bill_file}`"
                    )
        except FileNotFoundError as e:
            return {}

        return to_return

    def get_bill_filepath(self, absolute: bool = False) -> Union[None, str]:
        if self.id is None:
            return None
        if not absolute:
            return os.path.join(RECORDED_BILL_FOLDER_NAME, self.id + ".json")
        else:
            return os.path.join(
                os.getcwd(), RECORDED_BILL_FOLDER_NAME, self.id + ".json"
            )

    def save_on_disk(self):
        if self.get_bill_filepath() is None:
            return

        Path(RECORDED_BILL_FOLDER_NAME).mkdir(parents=True, exist_ok=True)

        with open(self.get_bill_filepath(), "w") as f:
            f.write(self.to_json())
