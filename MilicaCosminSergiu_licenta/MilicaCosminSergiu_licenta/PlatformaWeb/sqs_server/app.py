import asyncio
from datetime import datetime, timedelta, timezone
import requests
import boto3
from fastapi import FastAPI
from boto_aws import *
from fastapi import WebSocket
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from mongo_connection import *
sqs_client = boto3.client('sqs', region_name='eu-central-1')
queue_url = 'https://sqs.eu-central-1.amazonaws.com/637423524179/requests-queue'

app = FastAPI()
db, _ = connect_to_mongodb()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    ,
)
class Message(BaseModel):
    message_id: str
    client_ip: str
    edge_server: str
    domain: str
    resource: str
    state: str
    time: datetime

def get_region(client_addr):
    try:
        response = requests.get(f"https://ipinfo.io/{client_addr}/json?token=2ae48fc877572a")
        response.raise_for_status()
        data = response.json()
        if 'bogon' in data:
            return "Unknown"
        location = f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country', 'Unknown')}"
        return location
    except requests.RequestException as e:
        print(f"Error retrieving location for IP {client_addr}: {e}")
        return "Unknown"

async def get_sqs_messages():
    all_messages = []
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
        )

        messages = response.get('Messages', [])
        if not messages:
            break

        for msg in messages:
            try:
                body_parts = msg['Body'].split('|')
                if len(body_parts) != 6:
                    raise ValueError("Unexpected message format")

                client_ip, edge_server, domain, resource, state, time_str = body_parts
                message_time = datetime.strptime(time_str.strip(), '%Y-%m-%d %H:%M:%S.%f')

                location = get_region(client_ip.strip())

                all_messages.append({
                    "message_id": msg['MessageId'],
                    "client_ip": location,
                    "edge_server": edge_server.strip(),
                    "domain": domain.strip(),
                    "resource": resource.strip(),
                    "state": state.strip(),
                    "time": message_time.isoformat()
                })

                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg['ReceiptHandle']
                )
            except Exception as e:
                print(f"Error processing message: {e}")
                continue

        return all_messages

@app.websocket("/sqs-messages")
async def sqs_messages_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            sqs_messages = await get_sqs_messages()
            if sqs_messages:
                try:
                    await websocket.send_json(sqs_messages)
                except WebSocketDisconnect:
                    print("WebSocket disconnected. Stopping data transmission.")
                    break
            await asyncio.sleep(10)
    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8221,  log_level="info")
