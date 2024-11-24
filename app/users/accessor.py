from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.store.database.sqlalchemy_base import UserModel, ChatModel, ChatUpdateModel


class UserAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalars().first()
        return user

    async def create_user(self, user_id: int, username: str, name: str) -> UserModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(UserModel).values(id=user_id, username=username, name=name, score=0).
                returning(UserModel)
            )
            user = result.scalars().first()
        return user

class ChatAccessor:
    def __init__(self, app: "Application") -> None:
        self.app = app

    async def create_chat(self, chat_id: str) -> ChatModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(ChatModel).values(id=chat_id).returning(ChatModel)
            )
            chat = result.scalars().first()
        return chat

    async def get_chat_by_id(self, chat_id: int) -> ChatModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(ChatModel).where(ChatModel.id == chat_id)
            )
            chat = result.scalars().first()
        return chat

class ChatUpdateAccessor:
    def __init__(self, app: "Application") -> None:
        self.app = app

    async def handle_chat_offset(self, chat_id: int, offset: int):
        async with self.app.database.session as session:
            chat_exists = await session.execute(
                select(ChatModel).where(ChatModel.id == chat_id)
            )
            chat_record = chat_exists.scalars().first()

            if chat_record:
                stmt = insert(ChatUpdateModel).values(chat_id=chat_id, offset=offset)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['chat_id'],
                    set_={'offset': offset}
                )
                await session.execute(stmt)
                await session.commit()