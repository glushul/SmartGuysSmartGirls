from typing import TYPE_CHECKING, Sequence
from sqlalchemy import insert, func, select, update, and_
from sqlalchemy.orm import selectinload

from app.store.bot.state_controller import GameStates
from app.store.database.sqlalchemy_base import ChatModel, GameModel, ParticipantModel, ThemeModel

if TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor:
    def __init__(self, app: "Application") -> None:
        self.app = app

    async def create_game(self, chat_id: int, answer_time: int = 30) -> GameModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(GameModel).values(chat_id=chat_id, answer_time=answer_time,
                                         created_at=func.now(), state=GameStates.WAITING_FOR_ANSWER_TIME.value).
                returning(GameModel)
            )
            game = result.scalars().first()
        return game

    async def get_game_by_chat_id(self, chat_id: int) -> GameModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(GameModel).where(GameModel.chat_id == chat_id).
                order_by(GameModel.created_at.desc())
            )
            game = result.scalars().first()
        return game

    async def update_game(self, game_id: int, **fields) -> GameModel:
        async with self.app.database.session as session:
            result = await session.execute(
                update(GameModel)
                .where(GameModel.id == game_id)
                .values(**fields)
                .returning(GameModel)
            )
            game = result.scalars().first()
        return game

class ParticipantAccessor:
    def __init__(self, app: "Application") -> None:
        self.app = app

    async def create_participant(self, game_id: int, user_id: int, level: int, current:bool=False) -> ParticipantModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(ParticipantModel).values(game_id=game_id, user_id=user_id, level=level, current=current)
                .returning(ParticipantModel)
            )
            participant = result.scalars().first()
        return participant

    async def update_participant(self, user_id: int, game_id: int, **fields) -> ParticipantModel:
        async with self.app.database.session as session:
            result = await session.execute(
                update(ParticipantModel)
                .where(and_(
                    ParticipantModel.user_id == user_id,
                    ParticipantModel.game_id == game_id
                ))
                .values(**fields)
                .returning(ParticipantModel)
            )
            participant = result.scalars().first()
        return participant

    async def get_current_participant(self, game_id: int) -> ParticipantModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(ParticipantModel).where(
                    and_(ParticipantModel.current == True, ParticipantModel.game_id == game_id)
                )
            )
            participants = result.scalars().first()
        return participants

    async def get_participants_by_game_id(self, game_id: int) -> Sequence[ParticipantModel] | Sequence[None]:
        async with self.app.database.session as session:
            result = await session.execute(
                select(ParticipantModel).where(ParticipantModel.game_id == game_id).
                order_by(ParticipantModel.level.desc())
            )
            participants = result.scalars().all()
        return participants

    async def get_participant_by_user_game_id(self, user_id: int, game_id: int) -> ParticipantModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(ParticipantModel).where(
                    and_(
                        ParticipantModel.user_id == user_id,
                        ParticipantModel.game_id == game_id
                    )
                )
            )
            participant = result.scalars().first()
        return participant

    async def get_participant_by_game_level(self, level: int, game_id: int) -> ParticipantModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(ParticipantModel).where(
                    and_(ParticipantModel.level == level, ParticipantModel.game_id == game_id)
                )
            )
            participants = result.scalars().first()
        return participants

    async def change_current_participant(self, game_id: int) -> ParticipantModel | None:
        """
        Меняет текущего участника, пропуская участников, которые не соответствуют условию.
        Если нет подходящего участника, сбрасывает статус current для всех.
        """
        current_participant = await self.get_current_participant(game_id)
        if current_participant is None:
            return None

        levels = [4, 3, 2]  # Порядок уровней
        current_level = current_participant.level

        # Ищем следующий уровень, который соответствует условию
        next_participant = None
        for _ in range(len(levels)):  # Максимум 3 попытки (по количеству уровней)
            # Определяем следующий уровень
            current_index = levels.index(current_level)
            next_level = levels[(current_index + 1) % len(levels)]  # Цикличный переход

            # Получаем участника с этим уровнем
            participant = await self.get_participant_by_game_level(level=next_level, game_id=game_id)

            # Проверяем условие
            if participant and participant.incorrect_answers <= participant.level - 2:
                next_participant = participant
                break

            # Переходим к следующему уровню
            current_level = next_level

        async with self.app.database.session as session:
            # Сбрасываем текущего участника
            await session.execute(
                update(ParticipantModel)
                .where(ParticipantModel.user_id == current_participant.user_id)
                .values(current=False)
            )

            if next_participant:
                # Делаем найденного участника активным
                result = await session.execute(
                    update(ParticipantModel)
                    .where(ParticipantModel.user_id == next_participant.user_id)
                    .values(current=True)
                    .returning(ParticipantModel)
                )
                participant = result.scalars().first()
            else:
                # Если нет подходящего участника, сбрасываем статус у всех
                await session.execute(
                    update(ParticipantModel)
                    .where(ParticipantModel.game_id == game_id)
                    .values(current=False)
                )
                participant = None

            await session.commit()

        return participant

