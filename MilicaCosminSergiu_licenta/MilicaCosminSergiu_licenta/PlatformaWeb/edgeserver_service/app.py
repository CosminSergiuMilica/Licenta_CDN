from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from utile.mongo_connection import connect_to_mongodb
from utile import Idm_service_pb2_grpc, Idm_service_pb2
import grpc
import jwt
from pymongo.errors import ConnectionFailure, PyMongoError, OperationFailure
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from utile.boto_aws import get_cloudwatch_data
db, mongodb, client = connect_to_mongodb()

origin = db.origin
plan = db.plan

def grpc_client():
    channel = grpc.insecure_channel('user_service:50051')
    return Idm_service_pb2_grpc.IDMServiceStub(channel)

def transform_data(data):
    transformed_data = {
        'region': data.get("region"),
        "instance_id": data.get("instance_id"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        'status': data.get('status')
    }
    return transformed_data

def ban_data(ip):
    return {
        "ip_address": ip.get("ip_address"),
         "blocked_at": ip.get("blocked_at").isoformat() if isinstance(ip.get("blocked_at"), datetime) else ip.get("blocked_at")
    }

app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"
@app.on_event("shutdown")
def shutdown():
    if not client.is_closed():
        client.close()

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="EdgeServerService", version="1.0.0", routes=app.routes))

@app.get('/api/edgeserver_service/banip', responses={
    200: {"description": "Successfully retrieved ban ips"},
    401: {"description": "Unauthorized access"},
    403: {"description": "Forbidden access"},
    500: {"description": "Internal server error"}
})
def get_all_banip(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')
            if user_type == 'admin':
                blocked_ips = list(mongodb.blocked_ips.find())
                if blocked_ips:
                    result = [ban_data(ip) for ip in blocked_ips]
                else:
                    result = []
                return JSONResponse(content=result, status_code=200)
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ConnectionFailure:
            raise HTTPException(status_code=500, detail="Database connection failed")
        except OperationFailure:
            raise HTTPException(status_code=500, detail="Database operation failed")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")
@app.get('/api/edgeserver_service', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'}
})
def get_all_edgeservers(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')
            if user_type == 'admin':
                edge_servers = db.edgeserver.find()
                edge_servers_list = [transform_data(server) for server in edge_servers]
                return JSONResponse(content=edge_servers_list, status_code=200)
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ConnectionFailure:
            raise HTTPException(status_code=500, detail="Database connection failed")
        except OperationFailure:
            raise HTTPException(status_code=500, detail="Database operation failed")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.get('/api/edgeserver_service/{instance_id}', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'}
})
def get_one_edgeserver(request: Request, instance_id: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')
            if user_type == 'admin':
                edge_servers = db.edgeserver.find_one({'instance_id': instance_id})
                edge_servers = transform_data(edge_servers)
                metrics = get_cloudwatch_data(instance_id, edge_servers['region'])
                result = {
                    "edge_server": edge_servers,
                    "metrics": metrics
                }
                return JSONResponse(content=result, status_code=200)
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ConnectionFailure:
            raise HTTPException(status_code=500, detail="Database connection failed")
        except OperationFailure:
            raise HTTPException(status_code=500, detail="Database operation failed")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")
@app.post('/api/edgeserver_service/' , responses={
        201: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        409: {'description': 'Issue or Conflicts'},
        422: {'description': "Unprocessable Entity"},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def create_edgeserver(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('sub')
            user_type = payload.get('role')
            if user_type == 'admin':
                data = await request.json()
                if 'region' not in data or 'instance_id' not in data or 'lat' not in data or 'lon' not in data:
                    raise HTTPException(status_code=422, detail="Missing required fields")

                new_edge_server = {
                    "region": data['region'],
                    "instance_id": data['instance_id'],
                    "lat": data['lat'],
                    "lon": data['lon']
                }
                edge_servers = db.edgeserver.find_one({'instance_id': new_edge_server['instance_id']})
                if edge_servers:
                    raise HTTPException(status_code=409, detail="EdgeServer Exists")
                try:
                    db.edgeserver.insert_one(new_edge_server)
                    return JSONResponse(content={"message": "Edge server created successfully"}, status_code=201)
                except PyMongoError as e:
                    raise HTTPException(status_code=500, detail=f"Database error")
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ConnectionFailure:
            raise HTTPException(status_code=503, detail="Database connection failed")
        except OperationFailure:
            raise HTTPException(status_code=500, detail="Database operation failed")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.put('/api/edgeserver_service/{instance_id}', responses={
        200: {"description": "Success"},
        201: {'description': "Created"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def update_put_edgeserver(request: Request, instance_id: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')
            if user_type == 'admin':
                data = await request.json()
                update_fields = {}
                if 'region' in data:
                    update_fields['region'] = data['region']
                if 'lat' in data:
                    update_fields['lat'] = data['lat']
                if 'lon' in data:
                    update_fields['lon'] = data['lon']
                if not update_fields:
                    raise HTTPException(status_code=422, detail="No fields to update")
                try:
                    result = db.edgeserver.update_one(
                        {'instance_id': instance_id},
                        {'$set': update_fields},
                        upsert=True
                    )
                    if result.matched_count == 0:
                        return JSONResponse(content={"message": "Edge server created successfully"}, status_code=201)
                    return JSONResponse(content={"message": "Edge server updated successfully"}, status_code=200)
                except PyMongoError as e:
                    raise HTTPException(status_code=500, detail=f"Database error")
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ConnectionFailure:
            raise HTTPException(status_code=503, detail="Database connection failed")
        except OperationFailure:
            raise HTTPException(status_code=500, detail="Database operation failed")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.delete('/api/edgeserver_service/{instance_id}', responses={
        200: {"description": "Success"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def delete_edgeserver(request: Request, instance_id: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))

    if response.is_valid == 'valid':
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('sub')
            user_type = payload.get('role')

            if user_type == 'admin':
                try:
                    result = db.edgeserver.delete_one({'instance_id': instance_id})
                    if result.deleted_count == 0:
                        raise HTTPException(status_code=404, detail="Edge server not found")

                    return JSONResponse(content={"message": "Edge server deleted successfully"}, status_code=200)
                except PyMongoError as e:
                    raise HTTPException(status_code=500, detail=f"Database error")
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ConnectionFailure:
            raise HTTPException(status_code=503, detail="Database connection failed")
        except OperationFailure:
            raise HTTPException(status_code=500, detail="Database operation failed")

    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


def main():
    uvicorn.run("app:app", host="localhost", port=8003, log_level="info")

if __name__ == "__main__":
    main()
