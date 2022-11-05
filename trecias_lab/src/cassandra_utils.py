from typing import Any, Union, Dict, List
import json

from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, SimpleStatement


class CassandraDBClient:
    def __init__(self):

        self.cluster = Cluster(["0.0.0.0"], port=9042)
        self.session = self.cluster.connect("fish_restoraunt_chain")

    def reset(self):
        """
        Resets the database by dropping all the tables and inserting the data anew
        """
        print("Resetting DB...")

        with open("src/seed_data/seed_data.json", "r") as f:
            seed_data = json.load(f)

        for table_name in seed_data.keys():
            self.session.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.session.execute(seed_data[table_name]["table_generation_query"])
            for values in seed_data[table_name]["data"]:
                self.insert(table_name, values)

    def insert(self, table_name: str, values: Dict[str, Any]):
        field_descriptor = tuple(values.keys())
        value_descriptor = tuple(f"%({key})s" for key in field_descriptor)

        query = (
            f"INSERT INTO {table_name} {field_descriptor} VALUES {value_descriptor} IF NOT EXISTS"
            .replace("'", "")
        )
        self.session.execute(query, values)

    def query(self, query: str):
        return self.session.execute(query)

    # def batch(self, batch: BatchStatement):
    #     self.session.execute(batch)
