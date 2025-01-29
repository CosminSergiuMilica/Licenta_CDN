import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
import requests
from typing import Optional
from utile.mongo_connection import connect_to_mongodb
from utile import Idm_service_pb2_grpc, Idm_service_pb2
import grpc
import jwt
from pymongo.errors import ConnectionFailure, PyMongoError, OperationFailure
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

db, client = connect_to_mongodb()
origin = db.origin
plan = db.plan

def grpc_client():
    channel = grpc.insecure_channel('user_service:50051')
    return Idm_service_pb2_grpc.IDMServiceStub(channel)

def transform_origin_data(origin_data):
    transformed_data = {
        "owner": origin_data.get("owner"),
        "domain": origin_data.get("domain"),
        "ip": origin_data.get("ip"),
        "type_plan": origin_data.get("type_plan"),
        "time_cache": origin_data.get("time_cache"),
        "resource_static": origin_data.get("resource_static")
    }

    mode_development = origin_data.get("mode_development")
    if mode_development is not None:
        transformed_data["mode_development"] = mode_development

    return transformed_data

def transform_plan_data(plan_data):
    return {
        "id": plan_data.get("id"),
        "file_size": plan_data.get("file_size"),
        "mode_development": plan_data.get("mode_development"),
        "mode_offline": plan_data.get("mode_offline"),
        "managment_resource": plan_data.get("managment_resource")
    }


app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"


@app.on_event("shutdown")
def shutdown():
    if not client.is_closed():
        client.close()

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="Edge Server", version="1.0.0", routes=app.routes))

@app.get('/api/origin_service/plan/{domain}', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'}
})
def get_plan_for_web_site(domain: str, request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('sub')
        try:
            document = origin.find_one({'domain': domain})
            owner = document.get('owner', '')
            if owner != user_id:
                raise HTTPException(status_code=403, detail="Forbidden access")
            type_plan = document.get('type_plan', '')
            document_plan = plan.find_one({"id": type_plan})
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
        if document_plan is None:
            raise HTTPException(status_code=404, detail="Plan not found")
        response_data = {"plan": transform_plan_data(document_plan)}
        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.get('/api/origin_service', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
def get_all_origin_service(request: Request, owner: Optional[str] = Query(None, description="Owner of origin server")):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        query = {}
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('sub')
        user_type = payload.get('role')
        if owner is not None:
            if owner == user_id:
                query = {"owner": owner}
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        elif user_type != 'admin':
            raise HTTPException(status_code=403, detail="Forbidden access")

        try:
            origins = origin.find(query)
        except ConnectionFailure as e:
            raise HTTPException(status_code=503, detail=f"Database connection error")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
        origin_list = [{"domain": c.get('domain')}for c in origins]

        response_data = {"origins": origin_list}
        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.get('/api/origin_service/{domain}', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
def get_origin_service_by_domain(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")
    token = authorization_header.split(" ")[1]

    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        user_id = payload.get('sub')
        try:
            origin_data = origin.find_one({'domain': domain})
        except ConnectionFailure as e:
            raise HTTPException(status_code=503, detail=f"Database connection error")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")

        if user_type == 'admin' or user_id == origin_data.get('owner'):
            if not origin_data:
                raise HTTPException(status_code=404, detail=f"The origin with domain {domain} does not exist!")
            origin_list = transform_origin_data(origin_data)
            return JSONResponse(status_code=200, content=origin_list)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.post('/api/origin_service' , responses={
        201: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        409: {'description': 'Issue or Conflicts'},
        422: {'description': "Unprocessable Entity"},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def create_origin_service(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('sub')
        origin_data = await request.json()
        session = client.start_session()
        session.start_transaction()
        try:
            if user_id != origin_data.get('owner'):
                raise HTTPException(status_code=422, detail=f"the owner is different from the connected user {user_id}")
            existing_origin = origin.find_one({"domain": origin_data.get("domain")})
            if existing_origin:
                raise HTTPException(status_code=409, detail="The domain already exists")

            new_origin = transform_origin_data(origin_data)
            inserted_id = origin.insert_one(new_origin).inserted_id

            response_data = {"message": "Origin server inserted successfully", "_id": str(inserted_id)}
            return JSONResponse(status_code=201, content=response_data)
        except (ConnectionFailure, OperationFailure):
            session.abort_transaction()
            raise HTTPException(status_code=500, detail="Failed to insert origin")
        finally:
            session.end_session()

    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.put('/api/origin_service/{domain}', responses={
        200: {"description": "Success"},
        201: {'description': "Created"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def update_put_origin_service(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':

        data = await request.json()
        existing_origin = origin.find_one({"domain": domain})
        if existing_origin:
            try:
                origin.update_one({"domain": domain}, {"$set": data})
            except ConnectionFailure as e:
                raise HTTPException(status_code=503, detail=f"Database connection error")
            except PyMongoError as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
            response_data = {"message": "Origin server updated successfully", "_id": str(domain)}
            return JSONResponse(status_code=200, content=response_data)
        else:
            new_origin = transform_origin_data(data)
            try:
                origin.insert_one(new_origin)
            except Exception:
                raise HTTPException(status_code=500, detail="Failed to insert origin")
            response_data = {"message": "Origin server inserted successfully", "_id": str(domain)}
            return JSONResponse(status_code=201, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.patch('/api/origin_service/mode_dev/{domain}', responses={
        200: {"description": "Success"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def set_mode_development(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        data = await request.json()
        existing_origin = origin.find_one({"domain": domain})
        if existing_origin:
            try:
                origin.update_one({"domain": domain}, {"$set": {"mode_development": data['mode_development']}})
            except ConnectionFailure as e:
                raise HTTPException(status_code=503, detail=f"Database connection error")
            except PyMongoError as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
            response_data = {"message": "Origin server updated successfully", "_id": str(domain)}
            return JSONResponse(status_code=200, content=response_data)
        else:
            JSONResponse(status_code=404, content={"message": "Domain not fond"})
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.patch('/api/origin_service/mode_offline/{domain}', responses={
        200: {"description": "Success"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def set_mode_offline(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        data = await request.json()
        existing_origin = origin.find_one({"domain": domain})
        if existing_origin:
            try:
                origin.update_one({"domain": domain}, {"$set": {"mode_offline": data['mode_offline']}})
            except ConnectionFailure as e:
                raise HTTPException(status_code=503, detail=f"Database connection error")
            except PyMongoError as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
            response_data = {"message": "Origin server updated successfully", "_id": str(domain)}
            return JSONResponse(status_code=200, content=response_data)
        else:
            JSONResponse(status_code=404, content={"message": "Domain not fond"})
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.patch('/api/origin_service/resource_static/{domain}', responses={
        200: {"description": "Success"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def set_new_resource_static(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        data = await request.json()
        existing_origin = origin.find_one({"domain": domain})
        if existing_origin:
            try:
                origin.update_one({"domain": domain}, {"$set": {"resource_static": data['resource_static']}})
            except ConnectionFailure as e:
                raise HTTPException(status_code=503, detail=f"Database connection error")
            except PyMongoError as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
            response_data = {"message": "Origin server updated successfully", "_id": str(domain)}
            return JSONResponse(status_code=200, content=response_data)
        else:
            JSONResponse(status_code=404, content={"message": "Domain not fond"})
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.delete('/api/origin_service/{domain}', responses={
    200: {"description": "Successfully deleted domain"},
    401: {"description": "Unauthorized access"},
    403: {"description": "Forbidden access"},
    404: {"description": "Domain not found"},
    500: {"description": "Internal server error"}
})
def delete_origin_service(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))
    if response.is_valid != 'valid':
        raise HTTPException(status_code=401, detail="Unauthorized access")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('sub')
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    is_owner = db.origin.find_one({'domain': domain, 'owner': user_id}) is not None
    if not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden access")
    session = client.start_session()
    session.start_transaction()
    try:
        deleted_result = db.origin.delete_one({'domain': domain})
        if deleted_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail='Domain not found')
        try:
            cache_delete = requests.delete(f'http://cache-service:8000/api/cache_service/cache_redis/{domain}', headers=request.headers)
            cache_delete.raise_for_status()
        except requests.RequestException as e:
            session.abort_transaction()
            raise HTTPException(status_code=500, detail="Internal server error. Please try again")
        session.commit_transaction()
        return JSONResponse(status_code=200, content={"message": "Successfully deleted domain"})

    except (ConnectionFailure, OperationFailure) as e:
        session.abort_transaction()
        raise HTTPException(status_code=500, detail='Internal server error. Please try again')
    finally:
        session.end_session()

def main():
    uvicorn.run("app:app", host="localhost", port=8000, log_level="info")

if __name__ == "__main__":
    main()
