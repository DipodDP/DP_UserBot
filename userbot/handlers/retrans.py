import json
import sys

from pyrogram.client import Client
from pyrogram.errors import BadRequest, ChatForwardsRestricted
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message, User

from userbot.app_init import config, LOGGER
from userbot.sessions.redis_json import get_redis_json


try:
    with open('retrans.json', encoding='utf-8') as f:
        resend_configs = json.load(f)["resend_configs_list"]
except FileNotFoundError:
    LOGGER.warning(
        "No local retrans.json"
    )
    try:
        resend_configs = get_redis_json('retrans.json')["resend_configs_list"]
    except Exception as e:
        LOGGER.error(
            f"Unable to get retranslation config file!\n{e}"
        )
        sys.exit(1)

# getting list of channels for resending, to cut out messages from them
to_channels = list(map(lambda to: to["to_channel_id"], resend_configs))
group_id = 0


async def message_attr_set(m: Message, channel_id: int):

    caption = m.caption if m.caption is not None else ''
    m.caption = f'{caption[:1020]}{"..." if len(caption) > 1023 else ""}'
    if m.from_user is not None:
        caption = f'{caption}\nFrom:' \
            f'{(" " + m.from_user.first_name) if m.from_user.first_name is not None else ""}' \
            f'{(" " + m.from_user.last_name) if m.from_user.last_name is not None else ""}'

    if m.sender_chat is not None:
        m.sender_chat.has_protected_content = False
        m.sender_chat.id = channel_id
        m.sender_chat.title = f'{caption}\n{m.sender_chat.title}'

    if m.chat is not None:
        m.chat.id = channel_id
        if m.chat.title is not None:
            caption = f'{caption}\n{m.chat.title}'
            m.chat.title = ''
        m.chat.has_protected_content = False

    m.text = (m.text + "\n" + caption) if m.text is not None else None

    return m


async def resend(app: Client, message: Message, channel_id: int):
    global group_id

    m: Message = await app.get_messages(message.chat.id, message.id)

    LOGGER.debug(m)
    # printing some info
    LOGGER.info(
        "-".join([
            m.text.split('\n')[0] if m.text is not None else 'no text',
            m.caption if m.caption is not None else 'no caption',
            str(getattr(getattr(m, "chat", "no chat"), "id", "no id")),
            str(getattr(getattr(m, "chat", "no chat"), "title", "no title")),
            getattr(getattr(m, "from_user", "Noname"), "first_name", "Noname"),
            str(m.reply_to_message_id)
        ])
    )

    if 'reply_to_message_id' in repr(message):
        m = await message_attr_set(m, channel_id)
        reply_to_msg: Message = await app.get_messages(message.chat.id,
                                                       message.reply_to_message_id)
        reply_to_msg = await message_attr_set(reply_to_msg, channel_id)
        reply_to_sent: Message = await reply_to_msg.copy(channel_id)
        reply_to_msg_id = reply_to_sent.id

    else:
        m = await message_attr_set(m, channel_id)
        reply_to_msg_id = None

    try:
        if message.media_group_id is not None:
            if group_id != message.media_group_id:
                group_id = message.media_group_id
                await app.copy_media_group(channel_id,
                                           message.chat.id, message.id,
                                           reply_to_message_id=reply_to_msg_id)
        else:
            await m.copy(channel_id, reply_to_message_id=reply_to_msg_id)

    except ChatForwardsRestricted:

        file = await app.download_media(m, in_memory=True)

        if m.document is not None:
            await app.send_document(channel_id, file, caption=m.caption)
        elif m.photo is not None:
            await app.send_photo(channel_id, file, caption=m.caption)
        elif m.voice is not None:
            await app.send_voice(channel_id, file, caption=m.caption)
        elif m.video_note is not None:
            await app.send_video_note(channel_id, file)
        elif m.audio is not None:
            await app.send_audio(channel_id, file, caption=m.caption)
        elif m.video is not None:
            await app.send_video(channel_id, file, caption=m.caption)
        elif m.animation is not None:
            await app.send_animation(channel_id, file, caption=m.caption)


async def resend_dispatcher(app: Client, message: Message):

    msg: Message = await app.get_messages(message.chat.id, message.id)

    # setting sender id if sender is chat
    if not msg.empty:
        sender_id = msg.sender_chat.id if 'from_user' not in repr(msg) else\
            msg.from_user.id if msg.from_user is not None else 'No sender id'
        msg_text = msg.text if 'text' in repr(
            msg) else msg.caption if 'caption' in repr(msg) else 'no text'

        for conf in resend_configs:
            for source_channel in conf["source_channels"]:

                if msg.chat.id == source_channel["id"] or source_channel["id"] is None:
                    # getting ids from str for usernames and from config attributes
                    i = 0
                    while i < len(source_channel["from"]):

                        if type(source_channel["from"][i]) is str:
                            try:
                                user: User = await app.get_users(source_channel["from"][i])
                                source_channel["from"][i] = user.id
                            except BadRequest:
                                source_channel["from"] = source_channel["from"][:i + 1] \
                                    + getattr(config, source_channel["from"][i]) \
                                    + source_channel["from"][i + 1:]
                                source_channel["from"].pop(i)
                        i += 1

                    if ((any(map(lambda s: s in str(msg_text).lower(), source_channel["key_w"])))
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
