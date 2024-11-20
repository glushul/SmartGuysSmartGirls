import asyncio
from typing import TYPE_CHECKING

import aiohttp
from pyexpat.errors import messages
from sqlalchemy import select

from app.store.database.sqlalchemy_base import ChatModel

if TYPE_CHECKING:
    from app.web.app import Application

TOKEN = '7672228221:AAGQstNZ4c4r30Ld6gqLAF-7yxmWSFJN-4Y'
BOT_ID =  7672228221
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

class BotAccessor:
    def __init__(self, app: "Application"):
        self.app = app

    async def get_updates(self, offset=None):
        url = API_URL + 'getUpdates'
        params = {'timeout': 100}
        if offset is not None:
            params['offset'] = offset
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def send_message(self, chat_id, text: str | None):
        url = API_URL + 'sendMessage'
        params = {'chat_id': chat_id, 'text': text}
        if text is not None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    return await response.json()

    async def get_last_update_id(self):
        updates = await self.get_updates()
        if updates.get('result'):
            return updates['result'][-1]['update_id']
        return None

    async def process_updates(self, offset=None):
        updates = await self.get_updates(offset)
        if updates.get('result'):
            for update in updates['result']:
                message = update.get('message')

                if message:
                    if 'new_chat_members' in message:
                        for new_member in message['new_chat_members']:
                            if new_member.get('is_bot'):
                                chat_id = message['chat']['id']
                                if new_member.get("id") == BOT_ID:
                                    await self.send_message(chat_id,f"Привет! Я бот {new_member['username']} и рад быть здесь! Напиши /start, чтобы начать игру")
                                    if await self.app.store.games.get_chat_by_id(chat_id) is None:
                                        await self.app.store.games.create_chat(chat_id)

                    text = message.get('text')
                    if text is not None:
                        chat_id = message['chat']['id']
                        response_message = await self.app.bot_handler.handle_updates(message=message, chat_id=chat_id)
                        await self.send_message(chat_id, response_message)

                    offset = update['update_id'] + 1

            return offset

    async def polling(self):
        last_update_id = await self.get_last_update_id()
        offset = last_update_id + 1 if last_update_id is not None else None

        while True:
            offset = await self.process_updates(offset)
            await asyncio.sleep(1)