import asyncio
from typing import TYPE_CHECKING

import aiohttp
from sqlalchemy import select

from app.store.database.sqlalchemy_base import UpdateModel
from app.utils import Constants

if TYPE_CHECKING:
    from app.web.app import Application


class BotAccessor:
    def __init__(self, app: "Application"):
        self.app = app
        self._session = None
        self.api_url = f"https://api.telegram.org/bot{Constants.TOKEN}/"
        self.queue = asyncio.Queue()
        self.num_workers = 5

    @property
    def session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()

    async def get_updates(self, offset: int = None):
        url = f"{self.api_url}getUpdates"
        params = {'timeout': 100}
        if offset is not None:
            params['offset'] = offset

        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Ошибка при получении обновлений с Telegram API: {e}")

    async def send_message(self, chat_id: int, text: str):
        url = f"{self.api_url}sendMessage"
        params = {'chat_id': chat_id, 'text': text}

        try:
            async with self.session.post(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Ошибка при отправке сообщения: {e}")

    async def send_message_with_button(self, chat_id: int, text: str, keyboard):
        url = f"{self.api_url}sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": keyboard
        }
        try:
            await self.session.post(url, json=payload)
        except aiohttp.ClientError as e:
            print(f"Ошибка при отправке сообщения с кнопками: {e}")

    async def answer_callback_query(self, callback_query_id: str, text=str):
        url = f"{self.api_url}answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": False
        }
        try:
            await self.session.post(url, json=payload)
        except aiohttp.ClientError as e:
            print(f"Ошибка при ответе на callback-запрос: {e}")

    async def save_chat_offset(self, offset: int):
        async with self.app.database.session as session:
            result = await session.execute(select(UpdateModel))
            existing_record = result.scalars().first()

            if existing_record:
                existing_record.offset = offset
            else:
                new_record = UpdateModel(offset=offset)
                session.add(new_record)

            await session.commit()

    async def process_updates(self, offset: int = None):
        updates = await self.get_updates(offset)
        for update in updates.get('result', []):
            try:
                update_id = update.get('update_id')
                message = update.get("message")

                if update_id is not None:
                    offset = update_id + 1

                await self.queue.put(update)

                if 'chat' in message:
                    chat_id = message['chat']['id']
                    await self.save_chat_offset(offset=offset)

            except Exception as e:
                print(f"Ошибка при обработке обновления: {e}")
                print("Полное обновление:", update)

        return offset

    async def handle_update(self, update):
        try:
            print(f"Обрабатываем update: {update}")
            await self.app.bot_handler.handle_updates(update=update)
        except Exception as e:
            print(f"Ошибка при обработке update: {e}")

    async def worker(self):
        while True:
            update = await self.queue.get()
            if update is None:
                break
            await self.handle_update(update)
            self.queue.task_done()

    async def start_workers(self):
        workers = [asyncio.create_task(self.worker()) for _ in range(self.num_workers)]
        return workers

    async def stop_workers(self, workers):
        """Остановка воркеров."""
        for _ in range(self.num_workers):
            await self.queue.put(None)

        await asyncio.gather(*workers)

    async def polling(self):
        offset = await self.get_last_global_offset()
        workers = await self.start_workers()
        try:
            while True:
                offset = await self.process_updates(offset)
        finally:
            await self.stop_workers(workers)

    async def get_last_global_offset(self):
        async with self.app.database.session.begin() as session:
            result = await session.execute(select(UpdateModel.offset))
            rows = result.scalars().all()
            return max(rows) if rows else None