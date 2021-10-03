import os
from typing import Dict, Union, List
from pathlib import Path
from pome.models.encoder import PomeEncodable

RECORDED_INVOICE_FOLDER_NAME = os.path.join("invoices", "recorded")


class Invoice(PomeEncodable):
    """Stores all the metadata associated to a bill."""

    def __init__(
        self,
        id: Union[None, str] = None,
        invoice_number: str = "",
        status: str = "pending",
        client: str = "",
        tags: List[str] = [],
        transactions: Dict[str, str] = {},
        metadata: Dict[str, str] = {},
    ):
        self.id: Union[None, str] = id
        self.invoice_number = invoice_number
        self.status: str = status
        self.client: str = client
        self.tags: List[str] = tags
        self.transactions: Dict[str, str] = transactions
        self.metadata: Dict[str, str] = metadata

    @classmethod
    def fetch_all_recorded_invoices(cls) -> Dict[str, "Invoice"]:
        to_return = {}
        try:
            for invoice_file in os.listdir(RECORDED_INVOICE_FOLDER_NAME):
                if ".json" not in invoice_file:
                    continue
                invoice_path = os.path.join(RECORDED_INVOICE_FOLDER_NAME, invoice_file)
                if not os.path.exists(invoice_path):
                    continue

                invoice_id = invoice_file.replace(".json", "")
                to_return[invoice_id] = cls.from_json_file(invoice_path)

                if invoice_file != to_return[invoice_id].id + ".json":
                    raise ValueError(
                        f"Invoice id `{to_return[invoice_id].id}` stored in `{invoice_path}` does not match file name {invoice_file}`"
                    )
        except FileNotFoundError as e:
            return {}

        return to_return

    def get_invoice_filepath(self, absolute: bool = False) -> Union[None, str]:
        if self.id is None:
            return None
        if not absolute:
            return os.path.join(RECORDED_INVOICE_FOLDER_NAME, self.id + ".json")
        else:
            return os.path.join(
                os.getcwd(), RECORDED_INVOICE_FOLDER_NAME, self.id + ".json"
            )

    def save_on_disk(self):
        if self.get_invoice_filepath() is None:
            return

        Path(RECORDED_INVOICE_FOLDER_NAME).mkdir(parents=True, exist_ok=True)

        with open(self.get_invoice_filepath(), "w") as f:
            f.write(self.to_json())
