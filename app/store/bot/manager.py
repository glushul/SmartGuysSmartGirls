import asyncio

import aiohttp

TOKEN = '8044877151:AAGWmRwcjLTRqD3iIUFxm3-jFeWkHetkaX8'
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

class BotAccessor:

    async def get_updates(self, offset=None):
        url = API_URL + 'getUpdates'

        if offset is None:
            offset = 0

        params = {'offset': offset, 'timeout': 100}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()


    async def send_message(self, chat_id, text):
        url = API_URL + 'sendMessage'
        params = {'chat_id': chat_id, 'text': text}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                return await response.json()

    async def process_updates(self, offset=None):
        updates = await self.get_updates(offset)
        if updates.get('result'):
            for update in updates['result']:
                chat_id = update['message']['chat']['id']
                text = update['message'].get('text', '')
                await self.send_message(chat_id, text)
                offset = update['update_id'] + 1
        return offset


    async def polling(self):
        offset = None
        while True:
            offset = await self.process_updates(offset)
            await asyncio.sleep(1)