from utile.boto_aws import get_instance_public_ip
from pymongo import MongoClient, errors
from fastapi import HTTPException

def connect_to_mongodb():
    try:
        instance_id = 'i-0bb9483c3a293294d'
        public_ip = get_instance_public_ip(instance_id)
        print(f"Connecting to MongoDB at {public_ip}")
        client = MongoClient(f"mongodb://cosmin:cosmin@{public_ip}:27017", serverSelectionTimeoutMS=5000)
        db = client["mongodb"]
        edge = client['edgedb']
        client.server_info()
        return db, edge,client
    except (errors.ServerSelectionTimeoutError, errors.ConnectionFailure) as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to DB")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error")

# connect_to_mongodb()