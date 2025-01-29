import redis
from fastapi import FastAPI, HTTPException, Query, Request
from pymongo import MongoClient
from utile import Idm_service_pb2_grpc, Idm_service_pb2
import grpc
import jwt
from pymongo.errors import ConnectionFailure, OperationFailure, PyMongoError
from fastapi.responses import JSONResponse
from redis_connection import create_redis_connection
from fastapi.openapi.utils import get_openapi
from utile.boto_aws import get_instance_public_ip

try:
    r = create_redis_connection(instance_id='i-08777038d1546da66')
except Exception:
    raise HTTPException(status_code=503, detail="Failed to connect to the database. Please make sure MongoDB is running.")

try:
    mongo_ip = get_instance_public_ip(instance_id='i-0bb9483c3a293294d')
    client = MongoClient(f"mongodb://cosmin:cosmin@{mongo_ip}:27017")
    db = client["mongodb"]
    origin = db.origin
    plan = db.plan
except ConnectionFailure:
    raise HTTPException(status_code=503, detail="Failed to connect to the database. Please make sure MongoDB is running.")

def grpc_client():
    channel = grpc.insecure_channel('user_service:50051')
    return Idm_service_pb2_grpc.IDMServiceStub(channel)

app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"

@app.on_event("shutdown")
def shutdown():
    if not client.is_closed():
        client.close()

def transform_data(data):
    return {
        "domain": data.get("domain"),
        "resource": data.get("resource"),
        "time_cache": data.get("time_cache"),
        "in_cache": data.get("in_cache")
    }

def parse_redis_key(keys):
    parsed_key = []
    for key in keys:
        domain, rest = key.split("/", 1)
        resource = rest.split("/", 1)[1] if "/" in rest else rest
        parsed_key.append({"domain": domain + ":" + rest.split("/", 1)[0], "resource": resource})

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="Edge Server", version="1.0.0", routes=app.routes))

@app.get('/api/cache_service/cache_redis', responses={
    200: {"description": "Successfully retrieved cache keys"},
    401: {"description": "Unauthorized access"},
    500: {"description": "Internal server error"}
})
def get_all_cache_redis(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    try:
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
        if response.is_valid == 'valid':
            keys = r.keys(f"*")
            response_data = {"keys": keys}
            return JSONResponse(status_code=200, content=response_data)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized access")
    except grpc.RpcError as rpc_error:
        raise HTTPException(status_code=500, detail="gRPC communication error")
    except redis.Connection as e:
        raise HTTPException(status_code=500, detail='Internal redis-server error')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get('/api/cache_service/cache_redis/{domain}', responses={
    200: {"description": "Successfully retrieved cache keys"},
    401: {"description": "Unauthorized access"},
    500: {"description": "Internal server error"}
})
def get_all_cache_redis(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    try:
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
        if response.is_valid == 'valid':

            keys = r.keys(f"{domain}/*")
            response_data = {"keys": keys}
            return JSONResponse(status_code=200, content=response_data)

        else:
            raise HTTPException(status_code=401, detail="Unauthorized access")
    except grpc.RpcError as rpc_error:
        raise HTTPException(status_code=500, detail="gRPC communication error")
    except redis.Connection as e:
        raise HTTPException(status_code=500, detail='Internal redis-server error')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')

@app.delete('/api/cache_service/cache_redis/{domain}', responses={
    200: {"description": "Successfully retrieved cache keys"},
    401: {"description": "Unauthorized access"},
    403: {"description": "Forbidden access"},
    500: {"description": "Internal server error"}
})
async def delete_all_domain_cache(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    try:
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
        if response.is_valid == 'valid':
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('sub')
            is_owner = db.origin.find({'domain': domain, 'owner': user_id}) is not None
            if is_owner:
                keys = r.keys(f"{domain}/*")
                for key in keys:
                    r.delete(key)
                return JSONResponse(status_code=200,  content={"message": "Resource deleted successfully"})
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized access")
    except grpc.RpcError as rpc_error:
        raise HTTPException(status_code=500, detail="gRPC communication error")
    except Exception:
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")

@app.delete('/api/cache_server/cache_redis/resource/{resource}', responses={
    200: {"description": "Successfully retrieved cache keys"},
    401: {"description": "Unauthorized access"},
    403: {"description": "Forbidden access"},
    500: {"description": "Internal server error"}
})
async def delete_resource_redis(request: Request, resource: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    try:
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
        if response.is_valid == 'valid':
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('sub')
            domain = resource.split(':')[0]
            is_owner = db.origin.find({'domain': domain, 'owner': user_id}) is not None
            if is_owner:
                resource_modified = resource.replace(':', '/')
                r.delete(resource_modified)
                return JSONResponse(status_code=200, content={"message": "Resource deleted successfully"})
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized access")
    except grpc.RpcError as rpc_error:
        raise HTTPException(status_code=500, detail="gRPC communication error")
    except redis.Connection as e:
        raise HTTPException(status_code=500, detail='Internal redis-server error')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')