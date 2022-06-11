import asyncio
import logging


from pyrogram import idle

from userbot.app_init import app_init
from userbot.config import load_config
from userbot.handlers.retrans import register_retrans

logger = logging.getLogger(__name__)


def register_all_handlers(app):

    register_retrans(app)
    # pass


async def main():

    app = app_init()
    logging.basicConfig(
        # filename='log.txt',
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")

    register_all_handlers(app)

    try:
        await app.start()
        await idle()
    finally:
        await app.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
