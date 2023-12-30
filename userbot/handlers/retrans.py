import json
import sys

from pyrogram.client import Client
from pyrogram.errors import BadRequest, ChatForwardsRestricted
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message, User

from userbot.app_init import config, LOGGER
from userbot.handlers.resend_helpers import handle_reply, message_attr_set
from userbot.sessions.redis_json import get_redis_json


try:
    with open('retrans.json', encoding='utf-8') as f:
        resend_config = json.load(f)["resend_configs_list"]
except FileNotFoundError:
    LOGGER.warning(
        "No local retrans.json"
    )
    try:
        resend_config = get_redis_json(
            'retrans.json')["resend_configs_list"]
    except Exception as e:
        LOGGER.error(
            f"Unable to get retranslation channel_configig file!\n{e}"
        )
        sys.exit(1)

# getting list of channels for resending, to fetch messages from them
to_channels = list(
    map(lambda to: to["to_channel_id"], resend_config))
group_id = 0


async def resend(
    app: Client,
    message: Message,
    to_channel_id: int,
    topic_messasge_id: int | None
):
    global group_id

    LOGGER.debug(message)
    # printing some info
    LOGGER.info(
        "-".join([
            message.text.split(
                '\n')[0] if message.text is not None else 'no text',
            message.caption if message.caption is not None else 'no caption',
            str(getattr(getattr(message, "chat", "no chat"), "id", "no id")),
            str(getattr(getattr(message, "chat", "no chat"), "title", "no title")),
            getattr(getattr(message, "from_user", "Noname"),
                    "first_name", "Noname"),
            str(message.reply_to_message_id)
        ])
    )

    reply_to_message_id = await handle_reply(
        app,
        message,
        to_channel_id,
        topic_messasge_id
    )

    try:
        if message.media_group_id is not None:
            if group_id != message.media_group_id:
                group_id = message.media_group_id
                sended_message = await app.copy_media_group(
                    to_channel_id,
                    message.chat.id, message.id,
                    reply_to_message_id=reply_to_message_id
                )

        else:
            message = await message_attr_set(message, to_channel_id)
            sended_message = await message.copy(
                to_channel_id,
                reply_to_message_id=reply_to_message_id
            )

    except ChatForwardsRestricted:

        file = await app.download_media(message, in_memory=True)

        if message.document and file:
            await app.send_document(
                to_channel_id,
                file,
                caption=message.caption,
                reply_to_message_id=reply_to_message_id
            )
        elif message.photo and file:
            await app.send_photo(
                to_channel_id,
                file,
                caption=message.caption,
                reply_to_message_id=reply_to_message_id
            )
        elif message.voice and file:
            await app.send_voice(
                to_channel_id,
                file,
                caption=message.caption,
                reply_to_message_id=reply_to_message_id
            )
        elif message.video_note and file:
            await app.send_video_note(
                to_channel_id,
                file,
                reply_to_message_id=reply_to_message_id
            )
        elif message.audio and file:
            await app.send_audio(
                to_channel_id,
                file,
                caption=message.caption,
                reply_to_message_id=reply_to_message_id
            )
        elif message.video and file:
            await app.send_video(
                to_channel_id,
                file,
                caption=message.caption,
                reply_to_message_id=reply_to_message_id
            )
        elif message.animation and file:
            await app.send_animation(
                to_channel_id,
                file,
                caption=message.caption,
                reply_to_message_id=reply_to_message_id
            )


async def resend_dispatcher(app: Client, message: Message):

    # setting sender id if sender is chat
    if not message.empty:
        sender_id = message.sender_chat.id if 'from_user' not in repr(message) else\
            message.from_user.id if message.from_user is not None else 'No sender id'
        message_text = message.text if 'text' in repr(
            message) else message.caption if 'caption' in repr(message) else 'no text'

        for channel_config in resend_config:
            for source_channel in channel_config["source_channels"]:

                if message.chat.id == source_channel["id"] or source_channel["id"] is None:
                    # getting ids from str for usernames and from channel_configig attributes
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

                    if ((any(map(
                        lambda s: s in str(message_text).lower(),
                        source_channel["key_w"])))
                        or (source_channel["key_w"] == [])
                        and (sender_id in source_channel["from"]
                        or source_channel["from"] == [])
                        and (
                            "reply_markup" not in repr(message)
                            or (
                                "url" in repr(message.reply_markup)
                                or "ReplyKeyboardRemove" in repr(message.reply_markup)
                            ) if "reply_markup" in repr(message) else True)) \
                            and (
                            (all(map(
                                lambda s: s not in message_text, source_channel["stop_w"]
                            ))) or (source_channel["stop_w"] == [])):

                        await resend(
                            app,
                            message,
                            channel_config['to_channel_id'],
                            channel_config['topic_messasge_id']
                            if 'topic_messasge_id' in channel_config else None
                        )


def register_retrans(app: Client):
    app.add_handler(MessageHandler(resend_dispatcher))
