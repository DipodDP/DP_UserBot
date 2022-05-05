from telethon import TelegramClient, events
api_id = 11791817
api_hash = "37dfc3c484522a24d0c7a1ff4261a435"
client = TelegramClient('my_account', api_id, api_hash)


@client.on(events.NewMessage)
async def my_event_handler(event):
    print(event.peer_id)

client.start()
client.run_until_disconnected()