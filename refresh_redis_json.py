from userbot.sessions.redis_json \
    import del_redis_json, get_redis_json, save_redis_json

if (old_json := save_redis_json('retrans.json')) is not None or old_json == 'null':

    print(old_json)
    del_redis_json('retrans.json')
    json = get_redis_json('retrans.json')
    print(json)

else:
    print('Cannot save backup json, aborted')
