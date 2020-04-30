import redis
import os

try:
    redis_host = os.environ["REDIS_HOST"]
    redis_port = int(os.environ["REDIS_PORT"])
except Exception as E:
    print("Exception: environment variables not set")
    raise E

try:
    conn = redis.StrictRedis(host=redis_host, port=redis_port)
    print(conn)
    conn.ping()
    print("Connected!")
except Exception as ex:
    print("Error:", ex)
    raise Exception("Failed to connect, terminating.")
