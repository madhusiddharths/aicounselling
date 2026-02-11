#!/usr/bin/env python3
"""
Test MongoDB Connection Script
This script tests the connection to MongoDB Atlas using the credentials from .env
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

# Load environment variables from .env file
load_dotenv()

def test_mongodb_connection():
    """Test the MongoDB connection"""

    # Get MongoDB URI from environment
    mongodb_uri = os.getenv('MONGODB_URI')

    if not mongodb_uri:
        print("❌ ERROR: MONGODB_URI not found in .env file")
        return False

    print("🔍 Testing MongoDB Connection...")
    print(f"📍 URI: {mongodb_uri.split('@')[0]}@***hidden***")

    try:
        # Create a MongoDB client
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)

        # Attempt to ping the server
        client.admin.command('ping')

        print("✅ Successfully connected to MongoDB!")

        # List databases
        databases = client.list_database_names()
        print(f"\n📊 Available Databases ({len(databases)}):")
        for db_name in databases:
            print(f"   - {db_name}")

        # Try to access the ai-counselling database
        db = client['ai-counselling']
        collections = db.list_collection_names()
        print(f"\n📋 Collections in 'ai-counselling' database ({len(collections)}):")
        if collections:
            for collection_name in collections:
                count = db[collection_name].count_documents({})
                print(f"   - {collection_name} ({count} documents)")
        else:
            print("   (No collections found)")

        client.close()
        return True

    except ServerSelectionTimeoutError:
        print("❌ ERROR: Could not connect to MongoDB - Connection Timeout")
        print("   Check your internet connection and MongoDB URI")
        return False
    except ConnectionFailure as e:
        print(f"❌ ERROR: Connection Failed - {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)

