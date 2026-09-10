import hashlib
import json
import os
from datetime import datetime

from database import DATABASE_URL, get_connection


class Blockchain:

    def __init__(self):
        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "blockchain.json"
        )
        self.chain = []
        self.load_chain()
        self.ensure_genesis_block()

    def calculate_hash(self, index, timestamp, data, previous_hash):
        block_string = json.dumps(
            {
                "index": index,
                "timestamp": timestamp,
                "data": data,
                "previous_hash": previous_hash
            },
            sort_keys=True
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def load_chain(self):
        if DATABASE_URL:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT block_index, timestamp, data, previous_hash, hash
                FROM blockchain_blocks
                ORDER BY block_index ASC
            """)
            rows = cursor.fetchall()
            connection.close()

            self.chain = []
            for row in rows:
                try:
                    data = json.loads(row["data"])
                except (TypeError, json.JSONDecodeError):
                    data = {}

                self.chain.append({
                    "index": row["block_index"],
                    "timestamp": row["timestamp"],
                    "data": data,
                    "previous_hash": row["previous_hash"],
                    "hash": row["hash"]
                })
            return

        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as file:
                    self.chain = json.load(file)
            except Exception:
                self.chain = []

    def save_chain(self):
        if DATABASE_URL:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM blockchain_blocks")

            for block in self.chain:
                cursor.execute("""
                    INSERT INTO blockchain_blocks
                    (block_index, timestamp, data, previous_hash, hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    block["index"],
                    block["timestamp"],
                    json.dumps(block["data"], sort_keys=True),
                    block["previous_hash"],
                    block["hash"]
                ))

            connection.commit()
            connection.close()
            return

        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(self.chain, file, indent=4)

    def ensure_genesis_block(self):
        if len(self.chain) == 0:
            timestamp = datetime.now().isoformat()
            data = {"type": "GENESIS"}
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

    def add_product(self, product_data):
        previous_block = self.chain[-1]
        block = {
            "index": len(self.chain),
            "timestamp": datetime.now().isoformat(),
            "data": product_data,
            "previous_hash": previous_block["hash"]
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

    def verify_product(self, product_id, expected_hash=None):
        for block in self.chain:
            data = block.get("data", {})
            if data.get("product_id") == product_id:
                calculated_hash = self.calculate_hash(
                    block["index"],
                    block["timestamp"],
                    block["data"],
                    block["previous_hash"]
                )
                if calculated_hash != block["hash"]:
                    return False
                if expected_hash and block["hash"] != expected_hash:
                    return False
                return True
        return False
