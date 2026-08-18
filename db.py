import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

COGNODB_URI = os.getenv("COGNODB_URI")
COGNODB_USERNAME = os.getenv("COGNODB_USERNAME")
COGNODB_PASSWORD = os.getenv("COGNODB_PASSWORD")

class Database:
    def __init__(self):
        if not COGNODB_URI or not COGNODB_USERNAME or not COGNODB_PASSWORD:
            raise ValueError("CognoDB credentials missing in environment variables.")
        self.driver = GraphDatabase.driver(
            COGNODB_URI,
            auth=(COGNODB_USERNAME, COGNODB_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def get_session(self):
        return self.driver.session()

# Global database instance
db = Database()
