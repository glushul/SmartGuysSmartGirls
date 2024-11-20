from typing import TYPE_CHECKING, Sequence
from sqlalchemy import insert, func, select, update

from app.store.bot.state_controller import GameStates
from app.store.database.sqlalchemy_base import ChatModel, GameModel, ParticipantModel

if TYPE_CHECKING:
    from app.web.app import Application

class GameAccessor:
    def __init__(self, app: "Application") -> None:
        self.app = app

    async def create_chat(self, chat_id: str) -> ChatModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                insert(ChatModel).values(id=chat_id).returning(ChatModel.id)
            )
            chat_id = result.scalar_one()
        return chat_id

    async def get_chat_by_id(self, chat_id: int) -> ChatModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(ChatModel).where(ChatModel.id == chat_id)
            )
            executed_chat = result.scalars().first()
        return executed_chat

    async def create_game(self, chat_id: int, answer_time: int) -> GameModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                insert(GameModel).values(chat_id=chat_id, answer_time=answer_time, created_at=func.now(), state=GameStates.WAITING_FOR_PLAYERS.value).returning(GameModel.id)
            )
            theme_id = result.scalar_one()
        return theme_id

    async def get_game_by_chat(self, chat_id: int) -> GameModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(GameModel).where(GameModel.chat_id == chat_id).order_by(GameModel.created_at.desc())
            )
            executed_game = result.scalars().first()
        return executed_game

    async def change_game_state(self, game_id: int, state: str) -> GameModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                update(GameModel).where(GameModel.id == game_id).values(state=state).returning(GameModel)
            )
            executed_game = result.scalars().first()
        return executed_game

    async def create_participant(self, game_id: int, user_id: int, level: int, current=False) -> ParticipantModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                insert(ParticipantModel).values(game_id=game_id, user_id=user_id, level=level, correct_answers=0, incorrect_answers=0, current=current).returning(ParticipantModel.user_id)
            )
            participant_id = result.scalar_one()
        return participant_id

    async def get_participants_by_game_id(self, game_id: int) -> Sequence[ParticipantModel]:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(ParticipantModel).where(ParticipantModel.game_id == game_id)
            )
            participants = result.scalars().all()
        return participants

    async def get_participant_by_user_id(self, user_id: int) -> ParticipantModel | None:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(ParticipantModel).where(ParticipantModel.user_id == user_id)
            )
            participant = result.scalars().first()
        return participant