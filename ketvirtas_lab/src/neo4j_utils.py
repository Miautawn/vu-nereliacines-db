from typing import Any, Union, Dict, List
import json

from neo4j import GraphDatabase


class Neo4jConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def query_function(self, transaction: Any, query: str):
        result = transaction.run(query)
        return [record.data() for record in result]

    def query(self, query: str):
        with self.driver.session() as session:
            return session.execute_read(self.query_function, query)

