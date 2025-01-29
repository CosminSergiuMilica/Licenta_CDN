import base64
import json
from io import BytesIO
from utile.boto_aws import get_instance_public_ip
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
import httpx
import uvicorn
import gzip
from httpx import AsyncClient
from starlette.middleware.cors import CORSMiddleware
from utile.redis_connection import r
from utile.redis_global import create_redis_connection
from utile.mongo_connection import connect_to_mongodb
from datetime import datetime, timezone
from utile.boto_aws import sent_message_to_sqs, sent_message_to_sqs_ddos
from utile.logging_conf import setup_logging

try:
    cache = create_redis_connection(instance_id='i-08777038d1546da66')
except Exception as e:
    raise HTTPException(status_code=503, detail={'message': "Fail to connect db"})

app = FastAPI()
db, edge, client = connect_to_mongodb()

PROTOCOL = "http://"
INSTANCEID = 'i-04dedda7faa99604e'

http_client = AsyncClient()
logger = setup_logging()
queue_url = 'https://sqs.eu-central-1.amazonaws.com/637423524179/requests-queue'
queue_ddos = 'https://sqs.eu-central-1.amazonaws.com/637423524179/ddos.fifo'


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global http_client
    http_client = AsyncClient()
    print('Start')
    edge.edgeserver.update_one({'instance_id': INSTANCEID}, {'$set': {'status': 'ON'}})
    logger.info("HTTP client initialized")

@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()
    edge.edgeserver.update_one({'instance_id': INSTANCEID}, {'$set': {'status': "OFF"}})
    if not client.is_closed():
        client.close()
    r.close()
    cache.close()
    logger.info("Resources closed on shutdown")

def convert_to_seconds(time_cache):
    components = time_cache.split(' ')
    seconds = 0

    for component in components:
        if 'h' in component:
            seconds += int(component.replace('h', '')) * 3600
        elif 'm' in component:
            seconds += int(component.replace('m', '')) * 60
        elif 's' in component:
            seconds += int(component.replace('s', ''))

    return seconds

def build_resource_dict(document):
    if not document:
        return {}

    resource_dict = {
        'domain': document.get('domain', ''),
        'resource_static': document.get('resource_static', []),
        'time_cache': convert_to_seconds(document.get('time_cache', '')),
        'ip_origin': document.get('ip', ''),
        'mode_development': '',
        'mode_offline': '',
        'plan_detail': {}
    }

    type_plan_id = document.get('type_plan', '')
    plan_detail_document = db.plan.find_one({'id': type_plan_id})
    if plan_detail_document:
        resource_dict['plan_detail'] = {
            'id': plan_detail_document.get('id', ''),
            'file_size': plan_detail_document.get('file_size', ''),
            'mode_development': plan_detail_document.get('mode_development', ''),
            'mode_offline': plan_detail_document.get('mode_offline', '')
        }

    mode_dev = document.get('mode_development', '')
    if mode_dev:
        resource_dict['mode_development'] = mode_dev

    return resource_dict

def bytes_to_megabytes(bytes_size):
    kilobytes_size =int(bytes_size) / (1024*1024)
    return kilobytes_size
def get_plan_origin(db, plan):
    document_plan = db.plan.find({"id": plan})
    if document_plan is None:
        raise HTTPException(status_code=404, detail=f"Plan {plan} not found")
    return document_plan

def compress_with_gzip(content):
    buff = BytesIO()
    with gzip.GzipFile(fileobj=buff, mode='wb') as gz:
        gz.write(content)
    content_compress = buff.getvalue()
    buff.close()
    return content_compress

def get_cached_content(resource_key, site_property):
    try:
        cached_content = r.get(resource_key)
        if cached_content:
            return base64.b64decode(cached_content)
    except Exception as e:
        print(f"Redis local cache error: {e}")
    try:
        cached_content = cache.get(resource_key)
        if cached_content:
            r.set(resource_key, cached_content, ex=site_property['time_cache'])
            return base64.b64decode(cached_content)
    except Exception as e:
        print(f"Redis global cache error: {e}")
    return None

async def fetch_and_cache(request, resource_key, site_property, plan_detail):
    header = {k: v for k, v in request.headers.items() if k.lower() not in ["content-range", "range"]}
    response = await http_client.request(
        request.method, PROTOCOL + site_property['ip_origin'] + request.url.path, headers=header
    )
    content = response.content
    headers = {k: v for k, v in response.headers.items() if k.lower() not in ["cache-control"]}

    if response.status_code == 304:
        return Response(status_code=304)

    if "ETag" in response.headers:
        db.resources.insert_one({'': datetime.now()})

    cache_control = response.headers.get('cache-control', '').lower()

    if 'no-store' in cache_control:
        headers['Cache-Control'] = cache_control
    elif 'no-cache' in cache_control:
        headers['Cache-Control'] = cache_control
    else:
        max_age = 1000
        headers['Cache-Control'] = f'public, max-age={max_age}'

    headers['X-Source'] = site_property['ip_origin']
    size = response.headers['content-length']

    if bytes_to_megabytes(size) <= int(plan_detail.get("file_size", '')):
        content_cache = base64.b64encode(content)
        try:
            cache.set(resource_key, content_cache)
            r.set(resource_key, content_cache, ex=site_property['time_cache'])
        except Exception as e:
            print('Eroare la redis cache')
    if 'content-encoding' not in headers:
        content_compressed = compress_with_gzip(content)
        content = content_compressed
        headers['Content-Encoding'] = 'gzip'
        if 'content-length' in headers:
            headers.pop('content-length')

    return Response(content=content, status_code=response.status_code, headers=headers)

async def fetch_from_origin(request, site_property):
    response = await http_client.request(
        request.method, PROTOCOL + site_property['ip_origin'] + request.url.path, headers=request.headers,
        data=await request.body()
    )
    content = response.content
    headers = {k: v for k, v in response.headers.items()}
    headers['X-Source'] = site_property['ip_origin']
    return Response(content=content, status_code=response.status_code, headers=headers)

@app.middleware("https")
async def add_request_data_to_queue(request: Request, call_next):
    start_time = datetime.now(timezone.utc)
    response = await call_next(request)
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    domain = request.headers.get('host', 'unknown')
    domain = domain.split(':')[0]
    request_data = {
        "client_ip": request.client.host,
        "time": start_time.isoformat(),
        "method": request.method,
        "uri": request.url.path,
        "domain": domain,
        "status_code": response.status_code,
        "response_time": duration,
        "instance_id": INSTANCEID
    }
    if response.status_code not in [404, 409, 500, 503, 429]:
        try:
            sent_message_to_sqs_ddos(
                queue_url=queue_ddos,
                message_body=json.dumps(request_data)
            )
        except Exception as e:
            logger.error(f"Error sending message to SQS: {e}")

    return response

async def handle_request_error(domain, document):
    try:
        ip = get_instance_public_ip('i-034bec8cfe1190a43')
        id = document.get('owner')
        response = httpx.get(f'http://{ip}/api/cdn/users/mail/{id}')
        data = response.json()
        email = data.get('email')
        data = {
            "domain": domain,
            "email": email
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"http://{ip}:8200/api/mail-server/client-origin", json=data)
    except Exception as e:
        logger.error(f"Failed to handle request error for domain {domain}: {e}")

@app.head("/health")
def health_check():
    return Response(status_code=200)

@app.get("/{path:path}", responses={
        200: {'description': 'Success'},
        304: {'description': 'Not Modified'},
        404: {'description': 'Resource Not Found'},
        503: {'description': 'Service Unavailable'},
        521: {'description': 'Error connecting to origin server. Web Server Is Down' }})
async def proxy(request: Request, path: str):
    domain = request.headers.get('Host', '')
    client_ip = request.client.host
    try:
        document = db.origin.find_one({'domain': domain})
    except Exception as e:
        logger.error(f"Error querying database for domain {domain}: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again later.")

    if not document:
        logger.warning(f"Domain {domain} not found in database")
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found in database")

    resource_key = f"{domain}{request.url.path}"
    site_property = build_resource_dict(document)
    plan_detail = site_property['plan_detail']
    mode_dev = site_property['mode_development']
    message = f'{client_ip} | Ohio | {domain} | {request.url.path} | '
    try:
        if (mode_dev is False or mode_dev == '') and any(request.url.path.endswith(ext.lower()) for ext in site_property['resource_static']):
            cached_content = get_cached_content(resource_key, site_property)
            if cached_content:
                headers = {
                    'Cache-Control': 'public, max-age=1000',
                    'X-Source': 'Redis-Cache'
                }
                message += 'Hit | '
                message += f"{datetime.now()}"
                sent_message_to_sqs(queue_url, message_body=message)
                return Response(content=cached_content, status_code=200, headers=headers)

            response = await fetch_and_cache(request, resource_key, site_property, plan_detail)
            if response:
                message += 'Miss | '
                message += f"{datetime.now()}"
                sent_message_to_sqs(queue_url, message_body=message)
                return response

        else:
            response = await fetch_from_origin(request, site_property)
            message += 'Miss | '
            message += f"{datetime.now()}"
            sent_message_to_sqs(queue_url, message_body=message)
            return response
    except httpx.RequestError as e:
        logger.error(f"Request error for domain {domain}: {e}")
        await handle_request_error(domain, document)
        raise HTTPException(status_code=521, detail=f"Error connecting to origin server {domain}. Web Server Is Down")

@app.post('/{path:path}', responses={
        200: {'description': 'Success'},
        404: {'description': 'Resource Not Found'},
        503: {'description': 'Service Unavailable'},
        521: {'description': 'Error connecting to origin server. Web Server Is Down'}})
async def proxy_post(request: Request, path):
    domain = request.headers.get('Host', '')
    document = db.origin.find_one({'domain': domain}, {'ip': 1, '_id': 0})
    if not document:
        logger.warning(f"Domain {domain} not found in database")
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found in database")
    ip_origin = document.get('ip', '')
    try:
        response = await http_client.request(
            request.method, PROTOCOL + ip_origin + request.url.path, headers=request.headers, data=await request.body()
            )
        content = response.content
        headers = {k: v for k, v in response.headers.items()}
        client_ip = request.client.host
        message = f'{client_ip} | London | {domain} | {request.url.path} | POST | {datetime.now()} '

        sent_message_to_sqs(queue_url, message_body=message)
        return Response(content=content, status_code=response.status_code, headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Request error for domain {domain}: {e}")
        await handle_request_error(domain, document)
        raise HTTPException(status_code=521, detail=f"Error connecting to origin server {domain}. Web Server Is Down")


@app.delete('/{path:path}',responses={
        200: {'description': 'Success'},
        404: {'description': 'Resource Not Found'},
        503: {'description': 'Service Unavailable'},
        521: {'description': 'Error connecting to origin server. Web Server Is Down'}})
async def proxy_delete(request: Request, path):
    domain = request.headers.get('Host', '')
    document = db.origin.find_one({'domain': domain}, {'ip': 1, '_id': 0})
    if not document:
        logger.warning(f"Domain {domain} not found in database")
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found in database")
    ip_origin = document.get('ip', '')
    try:
        response = await http_client.request(
            request.method, PROTOCOL + ip_origin + request.url.path, headers=request.headers, data=await request.body()
        )
        content = response.content
        headers = {k: v for k, v in response.headers.items()}

        client_ip = request.client.host
        message = f'{client_ip} | Ohio | {domain} | {request.url.path} | DELETE | {datetime.now()} '

        sent_message_to_sqs(queue_url, message_body=message)
        return Response(content=content, status_code=response.status_code, headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Request error for domain {domain}: {e}")
        await handle_request_error(domain, document)
        raise HTTPException(status_code=521, detail=f"Error connecting to origin server {domain}. Web Server Is Down")



@app.patch('/{path:path}', responses={
        200: {'description': 'Success'},
        404: {'description': 'Resource Not Found'},
        503: {'description': 'Service Unavailable'},
        521: {'description': 'Error connecting to origin server. Web Server Is Down'}})
async def proxy_patch(request: Request, path):
    domain = request.headers.get('Host', '')
    document = db.origin.find_one({'domain': domain}, {'ip': 1, 'owner': 1, '_id': 0})
    if not document:
        logger.warning(f"Domain {domain} not found in database")
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found in database")
    ip_origin = document.get('ip', '')
    try:
        response = await http_client.request(
            request.method, PROTOCOL + ip_origin + request.url.path, headers=request.headers, data=await request.body()
        )
        content = response.content
        headers = {k: v for k, v in response.headers.items()}
        client_ip = request.client.host
        message = f'{client_ip} | Ohio | {domain} | {request.url.path} | PATCH | {datetime.now()} '
        sent_message_to_sqs(queue_url, message_body=message)
        return Response(content=content, status_code=response.status_code, headers=headers)
    except httpx.RequestError as e:
        logger.error(f"Request error for domain {domain}: {e}")
        await handle_request_error(domain, document)
        raise HTTPException(status_code=521, detail=f"Error connecting to origin server {domain}. Web Server Is Down")


@app.put('/{path:path}', responses={
        200: {'description': 'Success'},
        404: {'description': 'Resource Not Found'},
        503: {'description': 'Service Unavailable'},
        521: {'description': 'Error connecting to origin server. Web Server Is Down'}})
async def proxy_put(request: Request, path):
    domain = request.headers.get('Host', '')
    document = db.origin.find_one({'domain': domain}, {'ip': 1, '_id': 0})
    if not document:
        logger.warning(f"Domain {domain} not found in database")
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found in database")
    ip_origin = document.get('ip', '')
    try:
        response = await client.request(
            request.method, PROTOCOL + ip_origin + request.url.path, headers=request.headers, data=await request.body()
        )
        content = response.content
        headers = {k: v for k, v in response.headers.items()}

        client_ip = request.client.host
        message = f'{client_ip} | Ohio | {domain} | {request.url.path} | PUT | {datetime.now()} '

        sent_message_to_sqs(queue_url, message_body=message)
        return Response(content=content, status_code=response.status_code, headers=headers)
    except httpx.RequestError:
        logger.error(f"Request error for domain {domain}: {e}")
        await handle_request_error(domain, document)
        raise HTTPException(status_code=521, detail=f"Error connecting to origin server {domain}. Web Server Is Down")


def main():
    uvicorn.run("app:app", host="0.0.0.0", port=443, log_level="info", workers=3, ssl_keyfile='./utile/ca/proxy.key', ssl_certfile='./utile/ca/proxy.crt') # workers=15,


if __name__ == "__main__":
    main()
