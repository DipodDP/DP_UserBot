from dataclasses import dataclass

from environs import Env


@dataclass
class Config:
    bot_name: str
    api_id: int
    api_hash: str
    admin_ids: list[int]
    redis_endpoint: str
    redis_pass: str
    console_logger_lvl: str
    channel_id: int
    proxy: str


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        bot_name=env.str('BOT_NAME'),
        api_id=env.int("API_ID"),
        api_hash=env.str("API_HASH"),
        admin_ids=list(map(int, env.list("ADMINS"))),
        redis_endpoint=env.str("REDIS_ENDPOINT"),
        redis_pass=env.str("REDIS_PASS"),
        console_logger_lvl=env.str("CONSOLE_LOGGER_LVL"),
        channel_id=env.int('CHANNEL_ID'),
        proxy=env.list('PROXY_URL')
    )


