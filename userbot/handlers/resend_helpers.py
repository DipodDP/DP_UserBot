from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.types.messages_and_media.message import Str


async def message_attr_set(message: Message, channel_id: int):

    caption = message.caption if message.caption is not None else ''
    message.caption = Str(
        f'{caption[:1020]}{"..." if len(caption) > 1023 else ""}')
    if message.from_user is not None:
        caption = f'{caption}\nFrom:' \
            f'{(" " + message.from_user.first_name) if message.from_user.first_name is not None else ""}' \
            f'{(" " + message.from_user.last_name) if message.from_user.last_name is not None else ""}'

    if message.sender_chat is not None:
        message.sender_chat.has_protected_content = False
        message.sender_chat.id = channel_id
        message.sender_chat.title = f'{caption}\n{message.sender_chat.title}'

    if message.chat is not None:
        message.chat.id = channel_id
        if message.chat.title is not None:
            caption = f'{caption}\n{message.chat.title}'
            message.chat.title = ''
        message.chat.has_protected_content = False

    message.text = Str(message.text + "\n" +
                       caption) if message.text is not None else Str('')

    return message


async def handle_reply(
    app: Client,
    message: Message,
    channel_id: int,
    topic_message_id: int | None = None
) -> int | None:

    if 'reply_to_message_id' in repr(message):
        reply_to_message: Message = await app.get_messages(
            message.chat.id,
            message.reply_to_message_id
        )

        reply_to_message = await message_attr_set(reply_to_message, channel_id)
        sended_reply_to_message: Message = await reply_to_message.copy(
            channel_id,
            reply_to_message_id=topic_message_id
        )
        reply_to_message_id = sended_reply_to_message.id

    else:
        reply_to_message_id = topic_message_id

    return reply_to_message_id
