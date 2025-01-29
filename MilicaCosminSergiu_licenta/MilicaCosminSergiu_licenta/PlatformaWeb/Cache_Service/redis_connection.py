import redis
import ssl
from utile.boto_aws import get_instance_public_ip

instance_id = 'i-08777038d1546da66'
public_ip = get_instance_public_ip(instance_id)
REDIS_HOST = public_ip
REDIS_PORT = 6379
def create_redis_connection(instance_id, redis_port=6379):
    try:
        public_ip = get_instance_public_ip(instance_id)
        r = redis.StrictRedis(
            host=public_ip,
            port=redis_port,
            decode_responses=True,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        return r
    except Exception as e:
        print(str(e))
        return None
