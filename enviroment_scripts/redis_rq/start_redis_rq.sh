sudo docker run -d -p $REDIS_PORT:6379 -v $REDIS_DATA:/data redis
nohup rq-dashboard -P $REDIS_PORT &
python3 test_redis_connection.py
