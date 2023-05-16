import sys

import redis
from userbot.config import load_config


config = load_config(".env")

endpoint = config.redis_endpoint
password = config.redis_pass


redis_connection = redis.Redis(
    host=endpoint.split(':')[0],
    port=int(endpoint.split(':')[1]),
    password=password.strip()
)
try:
    redis_connection.ping()
    print("Connected to Redis successfully!")
    print("***** ENTERING DANGER ZONE ******")
    ans = input('Are you really want to delete ALL data from your Redis DB? (y/N):\n')
    if ans.lower() in ('y', 'yes'):
        redis_connection.flushall()
        print("All redis DB has been flushed")
    else:
        print('No data has been flushed')

except Exception:
    print("Invalid Redis credentials! Exiting the script")
    sys.exit(1)
