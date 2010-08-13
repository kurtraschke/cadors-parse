import redis

uuid_db = redis.Redis(host='localhost', port=6379, db=0)
input_db = redis.Redis(host='localhost', port=6379, db=1)
output_db = redis.Redis(host='localhost', port=6379, db=2)
today_db = redis.Redis(host='localhost', port=6379, db=3)
