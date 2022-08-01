import json
import sys

from pyrogram import Client
from pyrogram.errors import BadRequest, ChatForwardsRestricted
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from userbot.app_init import config, LOGGER
from userbot.sessions.redis_json import get_redis_json, del_redis_json


try:
    with open('retrans.json', encoding='utf-8') as f:
        resend_configs = json.load(f)["resend_configs_list"]
except FileNotFoundError:
    resend_configs = get_redis_json('retrans.json')["resend_configs_list"]
except FileNotFoundError:
    LOGGER.error(
        "No retranslation config file!"
    )
    sys.exit(1)
# print(resend_configs)
# print(resend_configs[0]["source_channels"][0])

# getting list of channels for resending, to cut out messages from them
to_channels = list(map(lambda to: to["to_channel_id"], resend_configs))


async def message_attr_set(m: Message, channel_id: int):

    caption = m.caption if m.caption is not None else ''
    if m.from_user is not None:
        caption = f'{caption}\nFrom:' \
                  f'{(" " + m.from_user.first_name) if m.from_user.first_name is not None else ""}' \
                  f'{(" " + m.from_user.last_name) if m.from_user.last_name is not None else ""}'

    if m.sender_chat is not None:
        m.sender_chat.has_protected_content = False
        m.sender_chat.id = channel_id
        m.sender_chat.title = f'{caption}\n{m.sender_chat.title}'
        # m.sender_chat.is_creator = False
    m.chat.id = channel_id
    if m.chat.title is not None:
        caption = f'{caption}\n{m.chat.title}'
        m.chat.title = ''

    m.caption = caption
    m.chat.has_protected_content = False
    m.text = (m.text + "\n" + caption) if m.text is not None else None

    return m


async def resend(app: Client, message: Message, channel_id: int):

    m = await app.get_messages(message.chat.id, message.id)

    # printing some info
    LOGGER.debug(message.text.split('\n')[0] if m.text is not None else 'no text', message.caption,
                 getattr(getattr(message, "chat", None), "id", None), getattr(getattr(m, "chat", None), "title", None),
                 getattr(getattr(message, "from_user", None), "first_name", None), message.reply_to_message_id)

    if 'reply_to_message_id' in repr(m):
        reply_to_msg = await app.get_messages(m.chat.id, m.reply_to_message_id)
        m = await message_attr_set(m, channel_id)
        reply_to_msg = await message_attr_set(reply_to_msg, channel_id)
        print(reply_to_msg.from_user.first_name)
        reply_to_msg = (await reply_to_msg.copy(channel_id)).id

    else:
        m = await message_attr_set(m, channel_id)
        reply_to_msg = None

    try:
        await m.copy(channel_id, reply_to_message_id=reply_to_msg)

    except ChatForwardsRestricted:

        file = await app.download_media(m, in_memory=True)

        if m.document is not None:
            await app.send_document(config.channel_id, file, caption=m.caption)
        elif m.voice is not None:
            await app.send_voice(config.channel_id, file)
        elif m.video_note is not None:
            await app.send_video_note(config.channel_id, file)
        elif m.audio is not None:
            await app.send_audio(config.channel_id, file)


async def resend_dispatcher(app: Client, message: Message):

    msg = await app.get_messages(message.chat.id, message.id)
    # print(msg)

    # setting sender id if sender is chat
    if not msg.empty:
        sender_id = msg.sender_chat.id if 'from_user' not in repr(msg) else msg.from_user.id
        msg_text = msg.text if 'text' in repr(msg) else msg.caption if 'caption' in repr(msg) else 'no text'

        for conf in resend_configs:
            for source_channel in conf["source_channels"]:

                if msg.chat.id == source_channel["id"] or source_channel["id"] is None:
                    # getting ids from str for usernames and from config attributes
                    i = 0
                    while i < len(source_channel["from"]):

                        if type(source_channel["from"][i]) is str:
                            try:
                                user = await app.get_users(source_channel["from"][i])
                                source_channel["from"][i] = user.id
                            except BadRequest:
                                source_channel["from"] = source_channel["from"][:i + 1] \
                                                         + getattr(config, source_channel["from"][i]) \
                                                         + source_channel["from"][i + 1:]
                                source_channel["from"].pop(i)
                        i += 1

                    if ((any(map(lambda s: s in msg_text.lower(), source_channel["key_w"])))
                        or (source_channel["key_w"] == [])
                        and (sender_id in source_channel["from"] or source_channel["from"] == [])
                        and ("reply_markup" not in repr(msg)
                             or ("url" in repr(msg.reply_markup) or "ReplyKeyboardRemove" in repr(msg.reply_markup))
                             if "reply_markup" in repr(msg) else True)) \
                            and ((all(map(lambda s: s not in msg_text, source_channel["stop_w"])))
                                 or (source_channel["stop_w"] == [])):
                        await resend(app, message, conf["to_channel_id"])


def register_retrans(app: Client):
    app.add_handler(MessageHandler(resend_dispatcher))
