import hashlib
import json
import os
from datetime import datetime


class Blockchain:

    def __init__(self):

        self.filename = "blockchain.json"

        self.chain = []

        self.load_chain()

        self.ensure_genesis_block()


    # =========================
    # HASH
    # =========================

    def calculate_hash(
        self,
        index,
        timestamp,
        data,
        previous_hash
    ):

        block_string = json.dumps(
            {
                "index": index,
                "timestamp": timestamp,
                "data": data,
                "previous_hash": previous_hash
            },
            sort_keys=True
        )

        return hashlib.sha256(
            block_string.encode()
        ).hexdigest()


    # =========================
    # LOAD
    # =========================

    def load_chain(self):

        if os.path.exists(self.filename):

            try:

                with open(
                    self.filename,
                    "r"
                ) as file:

                    self.chain = json.load(file)

            except:

                self.chain = []


    # =========================
    # SAVE
    # =========================

    def save_chain(self):

        with open(
            self.filename,
            "w"
        ) as file:

            json.dump(
                self.chain,
                file,
                indent=4
            )


    # =========================
    # GENESIS
    # =========================

    def ensure_genesis_block(self):

        if len(self.chain) == 0:

            timestamp = datetime.now().isoformat()

            data = {
                "type": "GENESIS"
            }

            block = {

                "index": 0,

                "timestamp": timestamp,

                "data": data,

                "previous_hash": "0"

            }

            block["hash"] = self.calculate_hash(
                block["index"],
                block["timestamp"],
                block["data"],
                block["previous_hash"]
            )

            self.chain.append(block)

            self.save_chain()


    # =========================
    # ADD PRODUCT
    # =========================

    def add_product(self, product_data):

        previous_block = self.chain[-1]

        block = {

            "index": len(self.chain),

            "timestamp":
                datetime.now().isoformat(),

            "data": product_data,

            "previous_hash":
                previous_block["hash"]

        }

        block["hash"] = self.calculate_hash(
            block["index"],
            block["timestamp"],
            block["data"],
            block["previous_hash"]
        )

        self.chain.append(block)

        self.save_chain()

        return block


    # =========================
    # VERIFY PRODUCT
    # =========================

    def verify_product(
        self,
        product_id,
        expected_hash=None
    ):

        for block in self.chain:

            data = block.get(
                "data",
                {}
            )

            if data.get("product_id") == product_id:

                calculated_hash = self.calculate_hash(
                    block["index"],
                    block["timestamp"],
                    block["data"],
                    block["previous_hash"]
                )

                if calculated_hash != block["hash"]:

                    return False

                if expected_hash:

                    if block["hash"] != expected_hash:

                        return False

                return True

        return False