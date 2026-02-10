from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv(override=True)

mongo_uri = os.getenv("MONGODB_URI")
db_name = os.getenv("MONGO_DB", "coach")
collection_name = os.getenv("MONGO_COLLECTION", "users")

client = MongoClient(mongo_uri)
db = client[db_name]

# ----------------- MongoDB connection -----------------



def fetch_all_from_mongo(collection_name: str, query: dict = None, limit: int = 0):
    """
    Fetch all documents (all fields) from a MongoDB collection and return as list of dicts.
    """
    query = query or {}
    collection = db[collection_name]
    cursor = collection.find(query) 
    if limit > 0:
        cursor = cursor.limit(limit)
    results = list(cursor)
    
    
    for doc in results:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return results
