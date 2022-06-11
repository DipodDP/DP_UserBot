import datetime

from telethon import TelegramClient, events, utils

api_id = 18315649
api_hash = "d05bb851ee633fcc6efec4519aba7ff2"
client = TelegramClient('my_account', api_id, api_hash).start()


@client.on(events.NewMessage)
async def my_event_handler(event):

    # ID чата
    chat_id = event.chat_id
    # Получаем ID Юзера
    sender_id = event.sender_id
    # Получаем ID сообщения
    msg_id = event.id
    # получаем имя юзера
    sender = await event.get_sender()
    # Имя Юзера
    name = utils.get_display_name(sender)

    # получаем имя группы
    chat_from = event.chat if event.chat else (await event.get_chat())
    chat_title = utils.get_display_name(chat_from)

    # полчаем текст сообщения
    if event.message.message == '':
        msg = 'Hided'
    else:
        msg = event.text

    print(f"ID: {event.date} {chat_id} {chat_title} >>  (ID: {sender_id})  {name} - (ID: {msg_id}) {msg}")

with client:
    client.run_until_disconnected()
