import asyncio
import httpx
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from utile.mongo_connection import connect_to_mongodb
from utile.boto_aws import get_instance_public_ip
from concurrent.futures import ThreadPoolExecutor, as_completed

db, _ = connect_to_mongodb()
executor = ThreadPoolExecutor(max_workers=10)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class ActionRequest(BaseModel):
    ip_addresses: list[str]

def get_instance():
    edgeservers = db.edgeserver.find({'status': {'$in': ['ON', 'SLOW']}})
    instances_info = {}
    for edgeserver in edgeservers:
        region = edgeserver['region']
        instances_info[region] = {
            'instance_id': edgeserver['instance_id']
        }
    return instances_info

async def send_action_to_all_servers(ips, action):
    if action not in ["ban", "unban"]:
        raise ValueError("Invalid action. Must be 'ban' or 'unban'.")

    instance_id = get_instance()
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "ip_addresses": ips
    }
    async with httpx.AsyncClient(verify=False) as client:
        for key, value in instance_id.items():
            ip = get_instance_public_ip(value['instance_id'], key)
            if ip:
                url = f'http://{ip}/{action}'
                try:
                    response = await client.post(url, headers=headers, json=data)
                    if response.status_code == 200:
                        print(f"Successfully sent {action} request to {ip}")
                    else:
                        print(f"Failed to send {action} request to {ip}, status code: {response.status_code}")
                except Exception as e:
                    print(f"Error sending {action} request to {ip}: {e}")

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="BanManager Server", version="1.0.0", routes=app.routes))

@app.post("/api/banmanager/{action}", responses={
    200: {"description": "Successfully sent action requests to all servers"},
    400: {"description": "Bad Request"},
    500: {"description": "Internal Server Error"}
})
async def handle_action(request: Request, action: str):
    body = await request.json()
    ips = body.get("ip_addresses")
    if not ips:
        raise HTTPException(status_code=400, detail="No IP addresses provided.")
    try:
        await send_action_to_all_servers(ips, action)
        return {"message": f"Successfully sent {action} requests to all servers"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def main():
    uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
