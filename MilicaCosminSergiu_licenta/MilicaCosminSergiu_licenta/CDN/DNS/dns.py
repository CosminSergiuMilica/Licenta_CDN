import hashlib
from datetime import datetime, timedelta
from dnslib import *
from dnslib.server import DNSServer, BaseResolver
import requests
import boto3
from math import radians, sin, cos, sqrt, atan2
from cachetools import TTLCache
from utile.mongo_connection import connect_to_mongodb
from concurrent.futures import ThreadPoolExecutor, as_completed

ip_cache = TTLCache(maxsize=100, ttl=600)
edgeservers_cache = TTLCache(maxsize=100, ttl=60)
dns_response_cache = TTLCache(maxsize=100, ttl=300)

db, edge = connect_to_mongodb()

CPU_THRESHOLD = 70

executor = ThreadPoolExecutor(max_workers=10)

def update_edgeservers_info():
    edgeservers = edge.edgeserver.find({'status': {'$in': ['ON', 'SLOW']}})
    updated_instances_info = {'ON': {}, 'SLOW': {}}
    for edgeserver in edgeservers:
        region = edgeserver['region']
        status = edgeserver['status']
        updated_instances_info[status][region] = {
            'instance_id': edgeserver['instance_id'],
            'lat': edgeserver['lat'],
            'lon': edgeserver['lon']
        }
    return updated_instances_info

def get_edgeservers_info():
    if not edgeservers_cache:
        updated_info = update_edgeservers_info()
        edgeservers_cache['ON'] = updated_info['ON']
        edgeservers_cache['SLOW'] = updated_info['SLOW']
    return edgeservers_cache

def get_ec2_instance_ip(region, instance_id):
    cache_key = f"{region}-{instance_id}"
    try:
        if cache_key in ip_cache:
            return ip_cache[cache_key]
        ec2_client = boto3.client('ec2', region_name=region)
        cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        instances = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = instances['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        if state != 'running':
            return None, None
        # verificam ca cpu sa fie sub 70% utilizare
        cpu_usage = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            Period=300,
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Statistics=['Average'],
            Unit='Percent'
        )

        if cpu_usage['Datapoints']:
            average_cpu = cpu_usage['Datapoints'][0]['Average']
            if average_cpu > CPU_THRESHOLD:
                return None, None

        public_ip = instance.get('PublicIpAddress')
        ipv6_addresses = instance.get('NetworkInterfaces', [{}])[0].get('Ipv6Addresses', [])
        public_ipv6 = ipv6_addresses[0]['Ipv6Address'] if ipv6_addresses else None
        ip_cache[cache_key] = (public_ip, public_ipv6)
        return public_ip, public_ipv6
    except Exception as e:
        print(f"Eroare la obtinerea IP-ului instantei: {e}")
        return None, None

def get_location_from_ip(ip):
    response = requests.get(f"https://ipinfo.io/{ip}/json?token=2ae48fc877572a")
    response.raise_for_status()
    data = response.json()
    if 'bogon' in data:
        return None, None
    location = data['loc']
    lat, lon = map(float, location.split(','))
    return lat, lon

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 #raza pamant
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    #formula haversine
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def get_best_server_ip(client_ip):
    client_lat, client_lon = get_location_from_ip(client_ip)
    instances_info = get_edgeservers_info()
    if client_lat is None or client_lon is None:
        # random in caz de nu obtinem pozitia clientului
        random_region = random.choice(list(instances_info['ON'].keys()))
        instance_id = instances_info['ON'][random_region]['instance_id']
        best_server_ip, best_server_ipv6 = get_ec2_instance_ip(random_region, instance_id)
        return best_server_ip, best_server_ipv6

    # prima data on
    sorted_servers_on = sorted(instances_info['ON'].items(),
                            key=lambda item: haversine(client_lat, client_lon, float(item[1]['lat']), float(item[1]['lon'])))
    futures_on = [executor.submit(get_ec2_instance_ip, region, info['instance_id']) for region, info in sorted_servers_on]
    for future in as_completed(futures_on):
        best_server_ip, best_server_ipv6 = future.result()
        if best_server_ip:
            print(f"Server gasit: {best_server_ip}")
            return best_server_ip, best_server_ipv6

    # apoi slow
    sorted_servers_slow = sorted(instances_info['SLOW'].items(),
                            key=lambda item: haversine(client_lat, client_lon, float(item[1]['lat']), float(item[1]['lon'])))
    futures_slow = [executor.submit(get_ec2_instance_ip, region, info['instance_id']) for region, info in sorted_servers_slow]
    for future in as_completed(futures_slow):
        best_server_ip, best_server_ipv6 = future.result()
        if best_server_ip:
            print(f"Server gasit: {best_server_ip}")
            return best_server_ip, best_server_ipv6

    return None, None


class DynamicResolver(BaseResolver):
    def resolve(self, request, handler):
        client_ip = handler.client_address[0]
        print(f"Client IP: {client_ip}")

        best_server_ip, best_server_ipv6 = get_best_server_ip(client_ip)

        reply = request.reply()
        qname = request.q.qname
        qtype = request.q.qtype
        domain = str(qname).rstrip('.')
        if db.origin.find_one({'domain': domain}) is not None:
            print('database')
            if qtype == QTYPE.A and best_server_ip is not None:
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(best_server_ip), ttl=300))
            elif qtype == QTYPE.AAAA:
                if best_server_ipv6 is not None:
                    reply.add_answer(RR(qname, QTYPE.AAAA, rdata=AAAA(best_server_ipv6), ttl=300))
                else:
                    print("Nu a fost gasita adresa IPv6 pentru cel mai bun server.")
            else:
                reply.header.rcode = RCODE.NXDOMAIN
        else:
            print('Domeniu nu a fost gasit, interogare DNS implicita')
            dns_response = self.fallback_dns_query(request.pack())
            if dns_response:
                return DNSRecord.parse(dns_response)
        return reply

    def fallback_dns_query(self, data):
        cache_key = hashlib.sha256(data).hexdigest()
        if cache_key in dns_response_cache:
            return dns_response_cache[cache_key]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        try:
            sock.sendto(data, ('127.0.0.1', 53))
            response, _ = sock.recvfrom(512)
            dns_response_cache[cache_key] = response
            return response
        except socket.timeout:
            print("Interogare DNS a expirat")
            return None
        finally:
            sock.close()


resolver = DynamicResolver()
server = DNSServer(resolver, port=53, address='172.31.41.59')
server.start_thread()

