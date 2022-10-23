from typing import Any, Union, Dict, List
import json

from pymongo import MongoClient

class HotelMongoDBClient:
    def __init__(self, connection_string: str, database_name: str):

        self.connection_string = connection_string
        self.database_name = database_name
        
        self.client = self._establish_mongodb_connection()
        self.db = self.client[database_name]

    def _establish_mongodb_connection(self):
        try:
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS = 2000)

            # validate that the connection is valid
            server_info = client.server_info()

            return client
        except Exception as e:
            print("Failed to connect to MongoDB!")
            print("Reason: ", e)


    def drop_db(self):
        print("Deleting previous DB...")
        self.client.drop_database(self.database_name)

    def seed_db(self, mock_data: Dict[str, str]):
        print("Seeding DB...")
        for collection_name in mock_data.keys():
            with open(mock_data[collection_name], "r") as f:
                mock_documents = json.loads(f.read())

                for document_group in mock_documents.keys():
                    self.insert(collection_name, mock_documents[document_group])

    def insert(self, collection: str, data: Union[Dict, List]):
        if type(data) == dict:
            self.db[collection].insert_one(data)
        self.db[collection].insert_many(data)

    def find(self, collection: str, search_query: dict = {}, projection_query: dict= {}):
        return self.db[collection].find(search_query, projection_query)

    def aggregate(self, collection: str, pipeline: List[Dict]):
        return self.db[collection].aggregate(pipeline)





