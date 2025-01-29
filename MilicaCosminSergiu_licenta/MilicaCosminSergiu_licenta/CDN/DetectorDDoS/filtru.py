import asyncio
import math
import boto3
import json
import httpx
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from utile.mongo_connection import connect_to_mongodb
from concurrent.futures import ThreadPoolExecutor, as_completed
from utile.boto_aws import get_instance_public_ip

# configuratii SQS
sqs_client = boto3.client('sqs', region_name='eu-central-1')
queue_url = 'https://sqs.eu-central-1.amazonaws.com/637423524179/ddos.fifo'

MEAN_PER_DOMENIU = 1000
MEAN_PER_CLIENT = 300
TIME_WINDOW = timedelta(minutes=1)

domain_requests = defaultdict(lambda: defaultdict(int))
response_time_cache = defaultdict(list)
historical_data = defaultdict(list)

db, _ = connect_to_mongodb()
executor = ThreadPoolExecutor(max_workers=10)
INSTANCE_ID = 'i-08ad270f48e7adec9'
REGION = 'eu-central-1'
# {
#     "example.com": {
#         "192.168.1.1": 5,
#         "192.168.1.2": 3
#     },
#     "test.com": {
#         "192.168.1.1": 2,
#         "192.168.1.3": 4
#     }
# }
async def send_ban_request(ip):
    ip_ban = get_instance_public_ip(INSTANCE_ID)
    if not ip_ban:
        print(f"Failed to get public IP for instance {INSTANCE_ID}")
        return
    url = f"http://{ip_ban}/api/banmanager/ban"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"ip_addresses": ip})
            if response.status_code == 200:
                print(f"Successfully sent ban request to {ip}")
            else:
                print(f"Failed to send ban request to {ip}, status code: {response.status_code}")
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}: {exc}")

def calculate_means(domain_request_counts, client_request_counts):
    total_domains = len(domain_request_counts)
    total_requests = sum(domain_request_counts.values())
    mean_per_domain = total_requests / total_domains if total_domains > 0 else 0

    total_clients = sum(len(clients) for clients in client_request_counts.values())
    total_requests_per_client = sum(sum(clients.values()) for clients in client_request_counts.values())
    mean_per_client = total_requests_per_client / total_clients if total_clients > 0 else 0

    print(f"Total domains: {total_domains}, Total clients: {total_clients}")
    print(f"Mean per domain: {mean_per_domain}")
    print(f"Mean per client: {mean_per_client}")

    return mean_per_domain, mean_per_client

def calculate_average_response_times():
    average_response_times = {}
    for instance_id, response_times in response_time_cache.items():
        total_response_time = sum(response_times)
        average_response_time = total_response_time / len(response_times) if response_times else 0
        average_response_times[instance_id] = average_response_time
    return average_response_times

async def analyze_requests():
    global MEAN_PER_DOMENIU, MEAN_PER_CLIENT

    domain_request_counts = defaultdict(int)
    client_request_counts = defaultdict(lambda: defaultdict(int))
    total_requests = 0

    for domain, clients in domain_requests.items():
        domain_total = sum(clients.values())
        domain_request_counts[domain] = domain_total
        for client, count in clients.items():
            client_request_counts[domain][client] = count
            total_requests += count

    if total_requests < 150:
        print("Not enough requests to update global means and standard deviations.")
        return
    print(f"total req {total_requests}")

    average_response_times = calculate_average_response_times()
    print(f"Average response times per instance: {average_response_times}")

    for domain, clients in domain_requests.items():
        domain_total = sum(clients.values())
        if (domain_total > (1/2)*MEAN_PER_DOMENIU ):
            print(f"Potential DDoS attack detected for domain {domain}")
            print(f"Total requests: {domain_total}, Global mean: {MEAN_PER_DOMENIU}")

            suspicious_ips = [ip for ip, count in clients.items() if count > MEAN_PER_CLIENT]
            print(f"Suspicious IPs: {suspicious_ips}")
            await send_ban_request(suspicious_ips)

            if len(clients) > 9:
                botnet_ips = [ip for ip, count in clients.items() if count > MEAN_PER_CLIENT / 10]
                if botnet_ips:
                    print(f"Potential Botnet DDoS attack detected for domain {domain}")
                    print(f"Botnet IPs: {botnet_ips}")
                    await send_ban_request(botnet_ips)
                return
        for client, count in clients.items():
            if count > MEAN_PER_CLIENT + (1/2) *MEAN_PER_CLIENT:
                print(f"Potential DDoS attack detected from client {client} on domain {domain}")
                print(f"Total requests: {count}, Global mean: {MEAN_PER_CLIENT}")
                suspicious_ips = [client]
                await send_ban_request(suspicious_ips)
                return

    mean_per_domain, mean_per_client = calculate_means(domain_request_counts, client_request_counts)
    MEAN_PER_DOMENIU = (MEAN_PER_DOMENIU + mean_per_domain) / 2
    MEAN_PER_CLIENT = (MEAN_PER_CLIENT + mean_per_client) / 2

    print(f"Updated global mean requests per domain: {MEAN_PER_DOMENIU}")
    print(f"Updated global mean requests per client: {MEAN_PER_CLIENT}")

    historical_data['mean_per_domain'].append(mean_per_domain)
    historical_data['mean_per_client'].append(mean_per_client)

    domain_requests.clear()
    response_time_cache.clear()

def printer():
    print(domain_requests)
async def process_messages():
    last_window_time = None

    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
        )

        if 'Messages' in response:
            for message in response['Messages']:
                request_data = json.loads(message['Body'])
                client = request_data['client_ip']
                domain = request_data['domain']
                instance_id = request_data['instance_id']
                response_time = request_data.get('response_time', 0)
                request_time = datetime.fromisoformat(request_data['time']).replace(second=0, microsecond=0)

                current_minute = request_time.strftime('%Y-%m-%d %H:%M')

                if last_window_time is None:
                    last_window_time = current_minute

                if current_minute == last_window_time:
                    domain_requests[domain][client] += 1
                    response_time_cache[instance_id].append(response_time)
                else:
                    await analyze_requests()

                    last_window_time = current_minute

                    domain_requests[domain][client] = 1
                    response_time_cache[instance_id] = [response_time]

                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

        time.sleep(1)

async def main():
    await process_messages()

asyncio.run(main())
