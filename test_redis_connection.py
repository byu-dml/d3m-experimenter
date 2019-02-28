import redis

try:
    from experimenter.config import redis_host, redis_port
except Exception as E:
    print("Exception: no config file given")
    raise E

try:
    conn = redis.StrictRedis(
        host=redis_host,
        port=redis_port)
    print(conn)
    conn.ping()
    print('Connected!')
except Exception as ex:
    print('Error:', ex)
    exit('Failed to connect, terminating.')
