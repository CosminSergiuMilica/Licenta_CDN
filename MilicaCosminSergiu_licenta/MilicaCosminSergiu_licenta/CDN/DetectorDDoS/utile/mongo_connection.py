from utile.boto_aws import get_instance_public_ip
from pymongo import MongoClient, errors

def connect_to_mongodb():
    try:
        instance_id = 'i-0bb9483c3a293294d'
        public_ip = get_instance_public_ip(instance_id)
        print(f"Connecting to MongoDB at {public_ip}")
        client = MongoClient(f"mongodb://cosmin:cosmin@{public_ip}:27017", serverSelectionTimeoutMS=5000)
        db = client["edgedb"]
        client.server_info()
        return db, client
    except (errors.ServerSelectionTimeoutError, errors.ConnectionFailure) as e:
        print(f"Failed to connect to DB")
    except Exception as e:
        print(f"Internal server error")

# connect_to_mongodb()