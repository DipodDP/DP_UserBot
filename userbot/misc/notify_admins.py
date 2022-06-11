import logging

from aiogram import Dispatcher

from tgbot.config import Config


async def on_startup_notify(dp: Dispatcher):
    config: Config = dp.bot.get('config')
    for admin in config.tg_bot.admin_ids:
        try:
            await dp.bot.send_message(admin, "Bot is running and ready. Press /start")
        except Exception as err:
            logging.exception(err)


async def on_down_notify(dp: Dispatcher):
    config: Config = dp.bot.get('config')
    for admin in config.tg_bot.admin_ids:
        try:
            await dp.bot.send_message(admin, "Bot is stopped")
        except Exception as err:
            logging.exception(err)
