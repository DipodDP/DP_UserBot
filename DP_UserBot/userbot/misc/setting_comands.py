from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_all_default_commands(bot: Bot):
    DEF_COMMANDS = {
        'ru': [
            BotCommand('/start', 'Запустить бота'),
            BotCommand('/help', 'Помощь по боту')
        ],
        'en': [
            BotCommand('/start', 'Bot start'),
            BotCommand('/help', 'Bot help')
        ]
    }

    for language_code, commands in DEF_COMMANDS.items():
        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeDefault(),
            language_code=language_code
        )
