from sqlalchemy import select, text, insert

from app.store.database.sqlalchemy_base import UserModel


class UserAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app
        self.database = app.database

    async def connect(self, app: "Application") -> None:
        if self.database.session is None:
            await self.database.connect()

    async def get_user_by_username(self, username: str) -> UserModel | None:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.username == username)
            )
            participant = result.scalars().first()
        return participant

    async def get_user_by_id(self, _id: int) -> UserModel | None:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == _id)
            )
            participant = result.scalars().first()
        return participant

    async def create_user(self, _id: int, username: str, name: str) -> UserModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                insert(UserModel).values(id=_id, username=username, name=name, score=0).returning(UserModel.id)
            )
            user_id = result.scalars().first()
        return user_id

    async def create_сhat(self, _id: int) -> UserModel:
        user = UserModel(id=_id, question_time=60)
        async with self.database.session.begin() as session:
            session.add(user)
            await session.commit()
