import asyncio
import logging

from pyrogram.sync import idle

from userbot.app_init import app_init
from userbot.handlers.retrans import register_retrans


def register_all_handlers(app):
    register_retrans(app)
    # pass


async def main():
    app = app_init()

    register_all_handlers(app)

    try:
        await app.start()
        await idle()
    finally:
        await app.stop()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):
        logger.warning("Bot stopped!")
