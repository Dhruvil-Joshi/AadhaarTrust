from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def save_to_mongodb(qr_data: list, aadhaar_number):
    """Save Aadhar data to MongoDB"""
    try:
        

        # Connect to MongoDB
        client = MongoClient(os.getenv("CLIENT_URL"))
        db = client[os.getenv("DB")]
        collection = db[os.getenv("COLLECTION")]

        # Build simple document
        document = {
            "aadhaar_number": aadhaar_number,
            "qr_data":    qr_data,
            "created_at": datetime.utcnow(),
        }

        # Insert new document
        result = collection.insert_one(document)
        print(f"Saved to MongoDB with id: {result.inserted_id}")
        return str(result.inserted_id)

    except Exception as e:
        print(f"Failed to save to MongoDB: {str(e)}")
        raise