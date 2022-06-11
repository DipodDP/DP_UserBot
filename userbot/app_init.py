import logging
import pathlib
import sys

import redis
from pyrogram import Client
from pyrogram.types import User

from userbot.config import load_config
from userbot.sessions.pyroredis import RedisSession


try:
    config = load_config(".env")
except ValueError:
    print(
        "Please make sure you have a proper .env in this directory "
        "or the required environment variables set."
        "\nExiting the script."
    )
    sys.exit(1)

ROOT_LOGGER = logging.getLogger()
LOGGER = logging.getLogger(config.bot_name)
logger_group_id = config.channel_id
CONSOLE_LOGGER = config.console_logger_lvl
root = pathlib.Path(__file__).parent
logging.captureWarnings(True)

if CONSOLE_LOGGER.isdigit():
    level = int(CONSOLE_LOGGER)
    if (level % 10 != 0) or (level > 50) or (level < 0):
        level = logging.INFO
ROOT_LOGGER.setLevel(logging.NOTSET)
LOGGER.setLevel(CONSOLE_LOGGER)


def app_init():

    if not (config.api_id and config.api_hash):
        print("You need to set your API keys in your config or environment!")
        LOGGER.debug("No API keys!")
        sys.exit(1)

    name = config.bot_name
    api_id = config.api_id
    api_hash = config.api_hash

    try:
        proxy = {
            "scheme": str(config.proxy[0]),  # "socks4", "socks5" and "http" are supported
            "hostname": str(config.proxy[1]),
            "port": int(config.proxy[2]),
            "username": "username",
            "password": "password"
        }
    except IndexError:
        LOGGER.debug("No proxy given")
        proxy = None

    sql_session = pathlib.Path(root / (name + '.session'))

    if config.redis_endpoint and config.redis_endpoint:
        try:
            redis_host = config.redis_endpoint.split(':')[0]
            redis_port = int(config.redis_endpoint.split(':')[1])
            redis_connection = redis.Redis(
                host=redis_host, port=redis_port, password=config.redis_pass
            )
            redis_connection.ping()
        except Exception as e:
            # LOGGER.exception(e)
            print(e)
            LOGGER.error(
                "Make sure you have the correct Redis endpoint and password "
                "and your machine can make connections."
            )
            sys.exit(1)
        LOGGER.debug("Connected to Redis successfully!")

        if not sql_session.exists():
            LOGGER.debug("Using Redis session!")
            redis_session = RedisSession(config.bot_name, redis_connection)
            session_string = redis_session.session_string

        else:
            session_string = None

        app = Client(name, api_id, api_hash, proxy=proxy, session_string=session_string)

    else:
        app = Client(name, api_id, api_hash, proxy=proxy)

    return app


async def hello(client: Client):
    async with client:
        await client.send_message("me", "Greetings from **Pyrogram**!")


async def verify_logger_group(client: Client) -> None:
    client.logger = True

    def disable_logger(error: str):
        if config.channel_id != 0:
            LOGGER.error(error)
        client.logger = False

    try:
        with client:
            entity = client.get_chat(config.channel_id)

        if not isinstance(entity, User):
            if not entity.is_creator:
                if entity.is_restricted:
                    disable_logger(
                        "Permissions missing to send messages "
                        "for the specified Logger group."
                    )
        client.logger = entity
    except ValueError:
        disable_logger(
            "Logger group ID cannot be found. "
            "Make sure it's correct."
        )
    except TypeError:
        disable_logger(
            "Logger group ID is unsupported. "
            "Make sure it's correct."
        )
    except Exception as ex:
        disable_logger(
            "An Exception occured upon trying to verify "
            "the logger group.\n" + str(ex)
        )


def wakeup(client: Client):
    client.loop.call_later(0.1, wakeup)


# try:
#     if sys.platform.startswith('win'):
#         client.loop.call_later(0.1, wakeup)  # Needed for SIGINT handling
#     client.loop.run_until_complete(client.disconnected)
#     if client.reconnect:
#         LOGGER.info("Client was disconnected, restarting the script.")
#         helpers.restarter(client)
# except NotImplementedError:
#     pass
# except KeyboardInterrupt:
#     print()
#     LOGGER.info("Exiting the script due to keyboard interruption.")
#     client._kill_running_processes()
# finally:
#     client.disconnect()
