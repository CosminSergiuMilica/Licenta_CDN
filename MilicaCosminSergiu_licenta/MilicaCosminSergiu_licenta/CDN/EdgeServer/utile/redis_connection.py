import redis

REDIS_HOST = 'localhost' #'54.221.149.223'
REDIS_PORT = 6379
try:
    r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
except Exception as e:
    print('eroare la conectare')
