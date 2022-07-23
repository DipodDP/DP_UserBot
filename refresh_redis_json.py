from userbot.sessions.redis_json import del_redis_json, get_redis_json

del_redis_json('retrans.json')
json = get_redis_json('retrans.json')
print(json)
