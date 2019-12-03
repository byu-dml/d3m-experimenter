# run this script from the host computer you want to store redis/rq dashboard.  Run this script from any directory really
sudo docker run -d -p $REDIS_PORT:6379 -v $REDIS_DATA:/data redis # redis is what rq runs off of - we don't access it directly
nohup rq-dashboard -P $REDIS_PORT &  # hook rq to the redis port, see the dashboard at localhost:9181
python3 test_redis_connection.py  # quick check to make sure it's working
