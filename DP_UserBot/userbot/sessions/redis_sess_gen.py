import asyncio
import platform
import sys
import os.path

from pyrogram import Client
from userbot.config import load_config

ERROR = (
    "Something is wrong with your API {}, "
    "please double check and re-enter the same."
)

if platform.python_version_tuple() < ('3', '10', '4'):
    print(
        "Please run this script with Python 3.10.4 or above."
        "\nExiting the script."
    )
    sys.exit(1)

if sys.platform.startswith('win'):
    loop = asyncio.ProactorEventLoop()
else:
    loop = asyncio.get_event_loop()


async def install_pip_package(package: str) -> bool:
    args = ['-m', 'pip', 'install', '--upgrade', '--user', package]
    process = await asyncio.create_subprocess_exec(
        sys.executable.replace(' ', '\\ '), *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    return True if process.returncode == 0 else False


try:
    import pyrogram
    from pyrogram.errors import SecurityError, BadRequest, RPCError
except (ModuleNotFoundError, ImportError):
    print('Installing Pyrogram, tgcrypto...')
    pip = loop.run_until_complete(install_pip_package('pyrogram tgcrypto'))
    if pip:
        print('Successfully installed Pyrogram, tgcrypto. Run the script again.')
    else:
        print(
            'Failed to install Pyrogram, tgcrypto. '
            'Run the script again after installing it manually using:'
        )
        print('"python3 -m pip install -U pyrogram tgcrypto --user"')
    sys.exit()

try:
    load_config("../../.env")
except ValueError:
    print(
        "Please make sure you have a proper .env in this directory "
        "or the required environment variables set."
        "\nExiting the script."
    )
    sys.exit(1)

api_id = os.environ.get('api_id', None)
api_hash = os.environ.get('api_hash', None)
endpoint = os.environ.get('redis_endpoint', None)
password = os.environ.get('redis_pass', None)
name = os.environ.get('bot_name', None)
redis_db = False

try:
    if all((api_id, api_hash)):
        redis_ip = input("Would you like to generate a Redis session? (yes/no): ")
        if redis_ip.lower() in ('y', 'yes'):
            if ':' not in endpoint:
                print('Invalid Redis endpoint! Try again.')
                sys.exit(1)
            redis_db = True
    elif os.path.exists('../../.env'):
        config = load_config("../../.env")
        api_id = config.api_id
        api_hash = config.api_hash
        name = config.bot_name
        if api_id is None or api_hash is None:
            print("Invalid config file! Fix it before generating a session.")
            sys.exit(1)
        redis_ip = input("Would you like to generate a Redis session? (yes/no): ")
        if redis_ip.lower() in ('y', 'yes'):
            endpoint = config.redis_endpoint
            password = config.redis_pass
            if endpoint is None or password is None:
                print(
                    "Make sure you have redis_endpoint and redis_password "
                    "in your .env"
                )
                sys.exit(1)
            elif ':' not in endpoint:
                print("Invalid Redis endpoint.")
                sys.exit(1)
            redis_db = True
    else:
        while True:
            api_id = input("Enter your API ID: ")
            if len(api_id) >= 2 and api_id.isnumeric():
                break
            else:
                print(ERROR.format('ID'))
        while True:
            api_hash = input("Enter your API hash: ")
            if len(api_hash) == 32 and api_hash.isalnum():
                break
            else:
                print(ERROR.format('hash'))
        redis_ip = input("Would you like to generate a Redis session? (yes/no): ")
        if redis_ip.lower() in ('y', 'yes'):
            while True:
                endpoint = input("Enter your Redis endpoint: ")
                if ':' in endpoint:
                    break
                else:
                    print('Invalid Redis endpoint! Try again.')
            password = input("Enter your Redis password: ")
            redis_db = True

    if redis_db:
        try:
            import redis
        except (ModuleNotFoundError, ImportError):
            print('Installing Redis...')
            pip = loop.run_until_complete(install_pip_package('redis'))
            if pip:
                print('Successfully installed Redis. Run the script again.')
            else:
                print(
                    'Failed to install Redis. '
                    'Run the script again after installing it manually using:'
                )
                print('"python3 -m pip install -U redis --user"')
            sys.exit()

        from userbot.sessions.pyroredis import RedisSession

        redis_connection = redis.Redis(
            host=endpoint.split(':')[0],
            port=int(endpoint.split(':')[1]),
            password=password.strip()
        )
        try:
            redis_connection.ping()

        except Exception:
            print("Invalid Redis credentials! Exiting the script")
            sys.exit(1)

        redis_session = RedisSession(name, redis_connection)
        session_string = redis_session.session_string
        app = Client(name, api_id, api_hash, session_string=session_string)

        if session_string == '':
            redis_session.client = app
            with app:
                redis_session.update_session_string(app)

    else:
        app = Client(name, api_id, api_hash)

    try:
        with app:
            me = app.get_me()
            first_name = me.first_name
            session_string = app.export_session_string()

        print(f"Successfully generated a session for {first_name}")
        print(f"Your session string: \n{session_string}")

    except RPCError as e:
        if redis_db:
            redis_session.delete()
            print(f"Your old session was invalid and has been automatically deleted!")
        print(f"Run the script again to generate a new session. {e}")
        sys.exit(1)

except (KeyboardInterrupt, SystemExit):
    print('Session generation cancelled.')
    sys.exit(1)
