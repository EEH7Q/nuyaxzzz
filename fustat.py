import asyncio
import os
import re

from telethon import TelegramClient
from telethon.sessions import MemorySession
from telethon.tl.types import ChannelForbidden, Channel, MessageService

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

CHAT_WHITELIST = []
SKIP_ADMIN_CHAT = True


async def main():
    if not os.path.exists("log.txt"):
        print("Нет текстового файла log.txt.")
        return
    data = open("log.txt", mode="r", encoding="utf-8").read()
    pattern = r"https://t\.me/(?!c/\d+)([\w\d_]+)"
    usernames = set(re.findall(pattern, data))
    print(f"Найдено предположительных чатов: {len(usernames)}")

    async with TelegramClient(MemorySession(), API_ID, API_HASH, flood_sleep_threshold=3) as client:
        client: TelegramClient = client
        me = await client.get_me()
        print(f"Вошли под {me.id} ({'@' + me.username if me.username else 'без юзернейма'})")

        for chat in usernames:
            print("="*15)
            try:
                entity = await client.get_entity(chat)
            except Exception as error:
                print(f"Не удалось получить информацию о чате {chat} - {error}")
                continue
            if isinstance(entity, ChannelForbidden):
                print(f"Не смогли получить информацию о чате {chat} - пользователь забанен")
                continue
            elif isinstance(entity, Channel):
                if entity.admin_rights and SKIP_ADMIN_CHAT:
                    print(f"Получили информацию о {chat} ({entity.id}) - пропускаем, наличие админ-прав")
                    continue
                if entity.id in CHAT_WHITELIST:
                    print(f"Получили информацию о {chat} ({entity.id}) - пропускаем, находится в вайт-листе")
                    continue
                print(f"Получили информацию о {chat} ({entity.id}) - собираем сообщения...")
                total_message_ids = 0
                while True:
                    message_ids = []
                    async for message in client.iter_messages(chat, from_user="me"):
                        if isinstance(message, MessageService):
                            continue
                        message_ids.append(message.id)
                    total_message_ids += len(message_ids)
                    if message_ids:
                        batch_size = 100
                        for i in range(0, len(message_ids), batch_size):
                            batch = message_ids[i:i + batch_size]
                            await client.delete_messages(chat, batch)
                            print(f"Снесли {len(batch)} сообщений в чате {chat} ({entity.id})...")
                    else:
                        break
                print(f"Закончили чистить сообщения в {chat} - снесли ~{total_message_ids}")
            else:
                print(f"Получили класс который не ожидали: {type(entity)} - пропускаем")
                continue


if __name__ == "__main__":
    asyncio.run(main())
