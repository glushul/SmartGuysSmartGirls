import aiohttp
import asyncio
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from typing import TYPE_CHECKING

from app.store.database.sqlalchemy_base import ChatModel, ChatUpdateModel
from app.utils import Constants

if TYPE_CHECKING:
    from app.web.app import Application


class BotAccessor:
    def __init__(self, app: "Application"):
        self.app = app
        self._session = None
        self.api_url = f"https://api.telegram.org/bot{Constants.TOKEN}/"

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
            return {}

    async def send_message(self, chat_id: int, text: str):
        url = f"{self.api_url}sendMessage"
        params = {'chat_id': chat_id, 'text': text}

        try:
            async with self.session.post(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Ошибка при отправке сообщения: {e}")
            return {}

    async def send_message_with_button(self, chat_id: int, text: str, keyboard):
        url = f"{self.api_url}sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": keyboard
        }

        print(keyboard)

        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                print("Сообщение отправлено успешно.")

    async def answer_callback_query(self, callback_query_id: str, text = str):
        url = f"{self.api_url}answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": False
        }
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                print("Callback закрыт успешно.")

    async def get_chat_offset(self, chat_id: int):
        try:
            async with self.app.database.session as session:
                result = await session.execute(
                    select(ChatUpdateModel.offset).where(ChatUpdateModel.chat_id == chat_id)
                )
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Ошибка при получении offset для чата {chat_id}: {e}")
            return None

    async def save_chat_offset(self, chat_id: int, offset: int):
        try:
            async with self.app.database.session as session:
                stmt = insert(ChatUpdateModel).values(chat_id=chat_id, offset=offset)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['chat_id'],
                    set_={'offset': offset}
                )

                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as e:
            print(f"Ошибка при сохранении offset для чата {chat_id} в базе данных: {e}")

    async def process_updates(self, offset: int = None):
        updates = await self.get_updates(offset)
        for update in updates.get('result', []):
            try:
                update_id = update.get('update_id')
                message = update.get("message")

                if update_id is not None:
                    offset = update_id + 1

                await self.app.bot_handler.handle_updates(update=update)

                if 'chat' in message:
                    chat_id = message['chat']['id']
                    await self.save_chat_offset(chat_id, offset)

            except Exception as e:
                print(f"Ошибка при обработке обновления: {e}")
                print("Полное обновление:", update)

        return offset

    async def polling(self):
        offset = await self.get_last_global_offset()
        while True:
            offset = await self.process_updates(offset)

    async def get_last_global_offset(self):
        try:
            async with self.app.database.session as session:
                result = await session.execute(select(ChatUpdateModel.offset))
                rows = result.scalars().all()
                return max(rows) if rows else None
        except SQLAlchemyError as e:
            print(f"Ошибка при получении последнего global offset: {e}")
            return None
