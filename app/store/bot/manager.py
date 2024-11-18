import asyncio

import aiohttp
from aiohttp.web_response import json_response

TOKEN = '8044877151:AAGWmRwcjLTRqD3iIUFxm3-jFeWkHetkaX8'
API_URL = f"https://api.telegram.org/bot{TOKEN}/"


async def get_updates(offset=None):
    url = API_URL + 'getUpdates'

    if offset is None:
        offset = 0

    params = {'offset': offset, 'timeout': 100}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()


async def send_message(chat_id, text):
    url = API_URL + 'sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            return await response.json()

async def process_updates(offset=None):
    updates = await get_updates(offset)
    if updates.get('result'):
        for update in updates['result']:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')

            if text == '/start':
                await send_message(chat_id, 'Привет! Я твой бот!')
            else:
                await send_message(chat_id, f'Вы сказали: {text}')

            offset = update['update_id'] + 1
    return offset


async def polling():
    offset = None
    while True:
        offset = await process_updates(offset)
        await asyncio.sleep(1)