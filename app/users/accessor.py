from sqlalchemy import select, text

from app.store.database.sqlalchemy_base import UserModel


class UserAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app
        self.database = app.database

    async def connect(self, app: "Application") -> None:
        if self.database.session is None:
            await self.database.connect()

    async def get_by_username(self, username: str) -> UserModel | None:
        async with self.database.session.begin() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.username == username)
            )
            executed_user = result.scalars().first()
            if executed_user:
                return UserModel(id=executed_user.id, username=executed_user.username, name = executed_user.name, score = executed_user.score)
        return None

    async def get_by_id(self, _id: int) -> UserModel | None:
        async with self.database.session.begin() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == _id)
            )
            executed_user = result.scalars().first()
            if executed_user:
                return UserModel(id=executed_user.id, username=executed_user.username, name = executed_user.name, score = executed_user.score)
        return None

    async def create_user(self, _id: int, username: str, name: str) -> UserModel:
        user = UserModel(id=_id, username=username, name=name, score=0)
        async with self.database.session.begin() as session:
            session.add(user)
            await session.commit()

    async def create_сhat(self, _id: int) -> UserModel:
        user = UserModel(id=_id, question_time=60)
        async with self.database.session.begin() as session:
            session.add(user)
            await session.commit()
