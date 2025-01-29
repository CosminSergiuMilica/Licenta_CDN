import re
from typing import Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import requests
import grpc
import jwt
from utile import Idm_service_pb2_grpc, Idm_service_pb2
from fastapi.openapi.utils import get_openapi
app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    ,
)
@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="Origin Server", version="1.0.0", routes=app.routes))

def grpc_client():
    channel = grpc.insecure_channel('user_service:50051')
    return Idm_service_pb2_grpc.IDMServiceStub(channel)

def handle_service_error(e: requests.RequestException):
    status_code = e.response.status_code if e.response is not None else 500
    content = {"success": False, "message": ""}
    if e.response is not None and e.response.status_code in [400, 401, 403, 404, 422, 409, 503, 500, 405]:
        content["message"] = e.response.json().get('detail', e.response.text)
    else:
        content["message"] = "An unexpected error occurred"
    return JSONResponse(status_code=status_code, content=content)

def validate_email(email):
    pattern = r"^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+).[a-zA-Z]+$"
    if re.match(pattern, email):
        return True
    else:
        return False

@app.get("/api/cdn")
async def root():
    return {"message": "Hello World"}

@app.get('/api/cdn/user/{user_id}', responses={
        200: {'description': 'Success'},
        404: {'description': 'Resource Not Found'},
        503: {'description': 'Service Unavailable'}})
def get_user_by_id(request: Request, user_id: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(Idm_service_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        id = payload.get('sub')
        if id == user_id:

            response_get = grpc_stub.GetUserData(Idm_service_pb2.GetUserRequest(user_id=user_id))
            user_data = {
                    "username": response_get.username,
                    "last_name": response_get.last_name,
                    "first_name": response_get.first_name,
                    "phone": response_get.phone,
                    "email": response_get.email,
                    "country": response_get.country
                }
            return JSONResponse(status_code=200, content=user_data)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access to user data")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.post('/api/cdn/login')
async def login(request: Request):
    data = await request.json()
    grpc_stub = grpc_client()
    response = grpc_stub.Login(Idm_service_pb2.LoginRequest(username=data['username'], password=data['password']))

    if response.access_token:
        payload = jwt.decode(response.access_token, SECRET_KEY, algorithms=["HS256"])

        user_type = payload.get('role')
        user_id = payload.get('sub')
        headers = {"Authorization": f"Bearer {response.access_token}"}

        json = {"Authorization": f"Bearer {response.access_token}", 'user_role': user_type , 'user_id': user_id}

        return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                            content=json)
    else:
        raise HTTPException(status_code=response.code, detail=response.message)

@app.get('/api/cdn/users/mail/{id}')
def get_mail_by_id(id: str):
    grpc_stub = grpc_client()
    response = grpc_stub.GetUserMail(Idm_service_pb2.GetMailRequest(user_id= id))
    if response.email != '':
        content = {"email": response.email}
        return JSONResponse(status_code=200, content=content)
    else:
        raise HTTPException(status_code=404, detail={"message": "User not found!!!"})

@app.post('/api/cdn/signup')
async def signup(request: Request):
    data = await request.json()
    grpc_stub = grpc_client()
    email = data.get('email')

    response = grpc_stub.SignUp(Idm_service_pb2.SignUpRequest(username=str(data.get('username')), password=str(data.get('password')), last_name=str(data.get('last_name')), first_name=str(data.get('first_name')),
                                                                  phone=str(data.get('phone')), email=str(email),  country=str(data.get('country'))))
    if response.access_token:
        id_user = response.id_user
        headers = {"Authorization": f"Bearer {response.access_token}"}
        payload = jwt.decode(response.access_token, SECRET_KEY, algorithms=["HS256"])
        json = {"Authorization": f"Bearer {response.access_token}",
                    'id_user': id_user
                    }
        user_type = payload.get('role')
        json['user_role'] = user_type
        jsn = {
            "email": email
        }
        requests.post('http://mailserver:8200/api/mail-server/signup-success', json=jsn)
        return JSONResponse(status_code=201, headers=headers, media_type="application/json", content=json)
    elif response.code == 409:
        return JSONResponse(status_code=409, content={"message": response.message})
    else:
        return JSONResponse(status_code=500, content={"message": response.message})

@app.post('/api/cdn/origin_service/', responses={
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
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.post(f"http://origin_service:8000/api/origin_service", json=data, headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=201, content=origin_response.json())

@app.get('/api/cdn/origin_service', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def get_origin_service(request: Request, owner: Optional[str] = Query(None, description="Owner of origin server")):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        params = {}
        if owner is not None:
            params['owner'] = owner
        origin_response = requests.get(f"http://origin_service:8000/api/origin_service", params=params, headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=200, content=origin_response.json())

@app.get('/api/cdn/origin_service/{domain}', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def get_origin_service_by_domain(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.get(f"http://origin_service:8000/api/origin_service/{domain}", headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return JSONResponse(status_code=200, content=origin_response.json())

@app.get('/api/cdn/origin_service/plan/{domain}')
async def get_plan_for_web_site(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.get(f"http://origin_service:8000/api/origin_service/plan/{domain}",
                                       headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return JSONResponse(status_code=200, content=origin_response.json())

@app.put('/api/cdn/origin_service/{domain}', responses={
        200: {"description": "Success"},
        201: {'description': "Created"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def update_put_origin_service(request: Request, domain: str):
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.put(f"http://origin_service:8000/api/origin_service/{domain}", json=data, headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.patch('/api/cdn/origin_service/mode_dev/{domain}', responses={
        200: {"description": "Success"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def set_mode_dev(request: Request, domain: str):
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.patch(f"http://origin_service:8000/api/origin_service/mode_dev/{domain}",
                                       json=data, headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.patch('/api/cdn/origin_service/resource_static/{domain}')
async def set_new_resource_static(request: Request, domain: str):
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.patch(f"http://origin_service:8000/api/origin_service/mode_offline/{domain}",
                                       json=data, headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.get('/api/cdn/cache_service/redis_cache/{domain}', responses={
    200: {"description": "Successfully retrieved cache keys"},
    401: {"description": "Unauthorized access"},
    500: {"description": "Internal server error"}
})
def get_all_redis_cache(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.get(f"http://cache_service:8000/api/cache_service/cache_redis/{domain}",
                                        headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.delete('/api/cdn/cache_service/redis_cache/resource/{resource}', responses={
    200: {"description": "Successfully deleted cache keys"},
    401: {"description": "Unauthorized access"},
    403: {"description": "Forbidden access"},
    500: {"description": "Internal server error"}
})
async def delete_resource_redis(request: Request, resource: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.delete(
            f"http://cache_service:8000/api/cache_server/cache_redis/resource/{resource}",
            headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.delete('/api/cdn/cache_service/redis_cache/{domain}', responses={
    200: {"description": "Successfully deleted cache keys"},
    401: {"description": "Unauthorized access"},
    403: {"description": "Forbidden access"},
    500: {"description": "Internal server error"}
})
def delete_all_cache(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.delete(
            f"http://cache_service:8000/api/cache_service/cache_redis/{domain}",
            headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error()
    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.get('/api/cdn/cache_service', responses={
    200: {"description": "Successfully retrieved cache keys"},
    401: {"description": "Unauthorized access"},
    500: {"description": "Internal server error"}
})
def get_resource_cache(request: Request, resource: str = Query(None)):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        if resource is None:
            origin_response = requests.get(
            f"http://cache_service:8000/api/cache_service/{resource}",
                headers=headers)
        else:
            origin_response = requests.get(
                f"http://cache_service:8000/api/cache_service?resource={resource}",
                headers=headers)

        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error()
    return JSONResponse(status_code=origin_response.status_code, content=origin_response.json())

@app.delete('/api/cdn/origin_service/{domain}')
def delete_origin(request: Request, domain: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        origin_response = requests.delete(f"http://origin_service:8000/api/origin_service/{domain}", headers=headers)
        origin_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

#############EDGESERVERS#################
@app.get('/api/cdn/edgeserver_service/{instance_id}', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'}
})
def get_one_edgeservers(request: Request, instance_id: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"http://edgeserver_service:8000/api/edgeserver_service/{instance_id}",
                headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return JSONResponse(status_code=response.status_code, content=response.json())
@app.get('/api/cdn/edgeserver_service', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'}
})
def get_all_edgeservers(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"http://edgeserver_service:8000/api/edgeserver_service",
                headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return JSONResponse(status_code=response.status_code, content=response.json())

@app.post('/api/cdn/edgeserver_service' , responses={
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
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"http://edgeserver_service:8000/api/edgeserver_service/", json=data, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return JSONResponse(status_code=201, content=response.json())

@app.delete('/api/cdn/edgeserver_service/{instance_id}', responses={
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
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"http://edgeserver_service:8000/api/edgeserver_service/{instance_id}", headers=headers)
        response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except requests.RequestException as e:
        return handle_service_error(e)

@app.put('/api/cdn/edgeserver_service/{instance_id}', responses={
        200: {"description": "Success"},
        201: {'description': "Created"},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        500: {'description': 'Internal server error.'},
        503: {'description': 'Database connection error'}
})
async def update_put_edgeserver(request: Request, instance_id: str):
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.put(f"http://edgeserver_service:8000/api/edgeserver_service/{instance_id}", json=data,
                                        headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)

    return JSONResponse(status_code=response.status_code, content=response.json())
@app.get('/api/cdn/edgeserver_service/banip', responses={
        200: {'description': 'Success'},
        401: {'description': 'Unauthorized access'},
        404: {'description': 'Resource Not Found'},
        403: {'description': 'Forbidden access'},
        500: {'description': 'Internal server error.'}
})
def get_all_edgeservers(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"http://edgeserver_service:8000/api/edgeserver_service/banip",
                headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return JSONResponse(status_code=response.status_code, content=response.json())
def main():
    uvicorn.run("app:app", host="localhost", port=8000, log_level="info")

if __name__ == "__main__":
    main()