import asyncio
import httpx
import time
from utile.mongo_connection import connect_to_mongodb
from utile.boto_aws import get_instance_public_ip

db, client = connect_to_mongodb()

def update_server_status(instance_id, new_status):
    db.edgeserver.update_one({"instance_id": instance_id}, {"$set": {"status": new_status}})

async def check_https_server_async(url, retries=3):
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(verify=False) as client:
                start_time = time.time()
                response = await client.head(url)
                elapsed_time = time.time() - start_time

                if response.status_code == 200:
                    print(f"Server responded with status code: {response.status_code}")
                    print(f"Response time: {elapsed_time:.2f} seconds")
                    return True, elapsed_time
                else:
                    print(f"Server returned error code: {response.status_code}")
                    return False, elapsed_time
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
        await asyncio.sleep(1)
    return False, None

async def monitor_edge_servers(db):
    while True:
        cursor = db.edgeserver.find({"status": {"$ne": "OFF"}})
        servers = list(cursor)
        tasks = []
        for server in servers:
            ip_address = get_instance_public_ip(server['instance_id'], server['region'])
            if ip_address:
                url = f"https://{ip_address}/health"
                tasks.append(check_https_server_async(url))
            else:
                print(f"Unable to get IP address for server {server['instance_id']}. Setting status to OFF.")
                update_server_status(server['instance_id'], 'OFF')
        results = await asyncio.gather(*tasks)
        for server, (is_alive, response) in zip(servers, results):
            if not is_alive:
                print(f"Server {server['instance_id']} is down after multiple attempts. Response time: {response} seconds")
                update_server_status(server['instance_id'], 'CRASH')
            else:
                print(f"Server {server['instance_id']} is up. Response time: {response:.2f} seconds")
                if response > 1.5:
                    update_server_status(server['instance_id'], 'SLOW')
                else:
                    update_server_status(server['instance_id'], 'ON')
        await asyncio.sleep(300)

async def main():
    await monitor_edge_servers(db)

if __name__ == "__main__":
    asyncio.run(main())
