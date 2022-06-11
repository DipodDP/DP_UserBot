import logging
import time

import redis
from redis.commands.json.path import Path

from pyrogram import Client

DEFAULT_HIVE_PREFIX = "pyrogram:client"
DEFAULT_TS_STR_FORMAT = "%F %T"

LOGGER = logging.getLogger(__name__)


class RedisSession:

    def __init__(self, session_name: str = None, redis_connection: redis.Redis or redis.StrictRedis = None):
        if not isinstance(session_name, str):
            raise TypeError("Session name must be a string.")
        if not redis_connection or not isinstance(redis_connection, (redis.Redis, redis.StrictRedis)):
            raise TypeError("The given redis_connection must be a Redis or StrictRedis instance.")

        self.redis = redis_connection
        self.name: str = session_name
        self.session_string: str = ''
        self.hive_prefix: str = DEFAULT_HIVE_PREFIX
        self.session_prefix = "{}:{}".format(self.hive_prefix, self.name)
        self.feed_session()
        self.add_timestamps: bool = False
        self.ts_format: str = DEFAULT_TS_STR_FORMAT

    def update_session_string(self, client: Client):
        self.session_string = client.export_session_string()
        self._update_sessions()

    def feed_session(self):
        try:
            s = self._get_sessions()
            if len(s) == 0:
                return

            s = self.redis.hgetall(s[-1])
            if not s:
                return

            self.session_string = s.get(b'session_string').decode()

        except Exception as ex:
            LOGGER.exception(ex.args)

    # Getting session_string from redis
    def _get_sessions(self, strip_prefix=False):
        key_pattern = "{}:auth".format(self.session_prefix)
        try:
            sessions = self.redis.keys(key_pattern + '*')
            return [
                s.decode().replace(key_pattern, '')
                if strip_prefix else
                s.decode() for s in sessions
            ]

        except Exception as e:
            LOGGER.exception(e.args)
            return []

    # Send session_string to redis
    def _update_sessions(self):

        key = "{}:auth".format(self.session_prefix)
        s = {"session_string": self.session_string}
        if self.add_timestamps:
            s.update({
                "ts_ts": time.time(),
                "ts_str": time.strftime(self.ts_format, time.localtime()),
            })
        try:

            self.redis.hset(key, mapping=s)
        except Exception as e:
            LOGGER.exception(e.args)

    def delete_auth(self):
        keys = self.redis.keys(f'{self.session_prefix}:auth*')
        self.redis.delete(*keys)

    def delete_all(self):
        keys = self.redis.keys(f'{self.session_prefix}*')
        self.redis.delete(*keys)


class RedisJSON:
    def __init__(self, session_name, json_name: str = None, redis_connection: redis.Redis or redis.StrictRedis = None):
        if not isinstance(json_name, str):
            raise TypeError("Session name must be a string.")
        if not isinstance(redis_connection, (redis.Redis, redis.StrictRedis)):
            raise TypeError("The given redis_connection must be a Redis or StrictRedis instance.")

        self.redis = redis_connection
        self.name: str = session_name
        self.json_name: str = json_name
        self.hive_prefix: str = DEFAULT_HIVE_PREFIX
        self.session_prefix = "{}:{}".format(self.hive_prefix, self.name)
        self.json = None
        self.feed_json()
        self.add_timestamps: bool = False
        self.ts_format: str = DEFAULT_TS_STR_FORMAT

    def feed_json(self):
        try:
            s = self._get_jsons()
            if len(s) == 0:
                return

            s = self.redis.json().get("{}:json:{}".format(self.session_prefix, self.json_name))
            if not s:
                return
            self.json = s

        except Exception as ex:
            LOGGER.exception(ex.args)

        # Getting session_string from redis

    def _get_jsons(self, strip_prefix=False):
        key_pattern = "{}:json:{}".format(self.session_prefix, self.json_name)
        try:
            json = self.redis.keys(key_pattern)
            return [
                s.decode().replace(key_pattern, '')
                if strip_prefix else
                s.decode() for s in json
            ]

        except Exception as e:
            LOGGER.exception(e.args)
            return []

        # Send session_string to redis
    def set_json(self, json):

        key = "{}:json:{}".format(self.session_prefix, self.json_name)
        try:
            self.redis.json().set(key, Path.root_path(), json)
            # self.redis.hset(key, mapping=s)
        except Exception as e:
            LOGGER.exception(e.args)

    def delete(self):
        key = f'{self.session_prefix}:json:{self.json_name}'
        self.redis.json().delete(key, Path.root_path())

# Code for standalone debug pyroredis:

# config = load_config(".env")
# api_id = config.api_id
# api_hash = config.api_hash
# name = config.bot_name
# endpoint = config.redis_endpoint
# password = config.redis_pass
#
# redis_conn = redis.Redis(
#     host=endpoint.split(':')[0],
#     port=endpoint.split(':')[1],
#     password=password.strip()
# )
#
# redis_session = RedisSession(name, redis_conn)
# session_string = redis_session.session_string
# app = Client(name, api_id, api_hash, session_string=session_string)
# if session_string == '':
#     redis_session.client = app
#     with app:
#         redis_session.update_session_string(app)
#         print(f"Your session string: {redis_session.session_string}")
#
# with app:
#     me = app.get_me()
#     name = me.first_name
#     print(f"Successfully generated a session for {name}")
#     entity = app.get_chat(config.channel_id)
#     app.send_message("me", "Greetings from **Pyrogram**!")
#
# if not isinstance(entity, User):
#     if not entity.is_creator:
#         if entity.default_banned_rights.send_messages:
#             print('baned')
#     print(entity)

# For future implementing

    """
    def get_update_state(self, entity_id):
        key_pattern = "{}:update_states:{}".format(self.sess_prefix, entity_id)
        return self.redis_connection.get(key_pattern)

    def set_update_state(self, entity_id, state):
        key_pattern = "{}:update_states:{}".format(self.sess_prefix, entity_id)
        self.redis_connection.set(key_pattern, state)

    def _get_entities(self, strip_prefix=False):
        key_pattern = "{}:entities:".format(self.sess_prefix)
        try:
            entities = self.redis_connection.keys(key_pattern+"*")
            if not strip_prefix:
                return entities
            return [s.decode().replace(key_pattern, "") for s in entities]
        except Exception as ex:
            LOGGER.exception(ex.args)
            return []

    def process_entities(self, tlo):
        rows = self._entities_to_rows(tlo)
        if not rows or len(rows) == 0 or len(rows[0]) == 0:
            return

        try:
            for row in rows:
                key = "{}:entities:{}".format(self.sess_prefix, row[0])
                s = {
                    "id": row[0],
                    "hash": row[1],
                    "username": row[2] or b'',
                    "phone": row[3] or b'',
                    "name": row[4] or b'',
                }
                self.redis_connection.hmset(key, s)
        except Exception as ex:
            LOGGER.exception(ex.args)

    def get_entity_rows_by_phone(self, phone):
        try:
            for key in self._get_entities():
                entity = self.redis_connection.hgetall(key)
                p = (
                    entity.get(b'phone').decode()
                    if entity.get(b'phone') else
                    None
                )
                if p and p == phone:
                    return (
                        int(entity.get(b'id').deocde()),
                        int(entity.get(b'hash').decode())
                    )
        except Exception as ex:
            LOGGER.exception(ex.args)
        return None

    def get_entity_rows_by_username(self, username):
        try:
            for key in self._get_entities():
                entity = self.redis_connection.hgetall(key)
                u = (
                    entity.get(b'username').decode()
                    if entity.get(b'username') else
                    None
                )
                if u and u == username:
                    return (
                        int(entity.get(b'id').deocde()),
                        int(entity.get(b'hash').decode())
                    )
        except Exception as ex:
            LOGGER.exception(ex.args)
        return None

    def get_entity_rows_by_name(self, name):
        try:
            for key in self._get_entities():
                entity = self.redis_connection.hgetall(key)
                n = (
                    entity.get(b'name').decode()
                    if entity.get(b'name') else
                    None
                )
                if n and n == name:
                    return (
                        int(entity.get(b'id').deocde()),
                        int(entity.get(b'hash').decode())
                    )
        except Exception as ex:
            LOGGER.exception(ex.args)
        return None

    def get_entity_rows_by_id(self, id, exact=True):
        if exact:
            key = "{}:entities:{}".format(self.sess_prefix, id)
            s = self.redis_connection.hgetall(key)
            if not s:
                return None
            try:
                return id, int(s.get(b'hash').decode())
            except Exception as ex:
                LOGGER.exception(ex.args)
                return None
        else:
            ids = (
                utils.get_peer_id(types.PeerUser(id)),
                utils.get_peer_id(types.PeerChat(id)),
                utils.get_peer_id(types.PeerChannel(id))
            )
            try:
                for key in self._get_entities():
                    entity = self.redis_connection.hgetall(key)
                    ID = entity.get(b'id').decode()
                    if ID and ID in ids:
                        return ID, int(entity.get(b'hash').decode())
            except Exception as ex:
                LOGGER.exception(ex.args)

    def cache_file(self, md5_digest, file_size, instance):
        if not isinstance(instance, (types.InputDocument, types.InputPhoto)):
            raise TypeError('Cannot cache %s instance' % type(instance))

        key = "{}:sent_files:{}".format(self.sess_prefix, md5_digest)
        s = {
            'md5_digest': md5_digest,
            'file_size': file_size,
            'type': _SentFileType.from_type(type(instance)),
            'id': instance.id,
            'access_hash': instance.access_hash,
        }
        try:
            self.redis_connection.hmset(key, s)
        except Exception as ex:
            LOGGER.exception(ex.args)

    def get_file(self, md5_digest, file_size, cls):
        key = "{}:sent_files:{}".format(self.sess_prefix, md5_digest)
        s = self.redis_connection.hgetall(key)
        if s:
            try:
                if (
                    s.get(b'md5_digest').decode() == md5_digest and
                    s.get(b'file_size').decode() == file_size and
                    s.get(b'type').decode() == _SentFileType.from_type(cls)
                ):
                    return (cls(
                        s.get(b'id').decode(),
                        s.get(b'access_hash').decode()
                    ))
            except Exception as ex:
                LOGGER.exception(ex.args)
                return None
    """
