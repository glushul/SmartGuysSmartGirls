import random
from enum import Enum
from typing import TYPE_CHECKING, Sequence

from app.store.database.sqlalchemy_base import ParticipantModel

if TYPE_CHECKING:
    from app.web.app import Application

class GameStates(Enum):
    WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
    GAME_STARTED = "GAME_STARTED"
    ROUND1 = "ROUND1"
    ROUND2 = "ROUND2"
    ROUND3 = "ROUND3"
    ROUND4 = "ROUND4"
    GAME_ENDED = "GAME_ENDED"




class BotHandler:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, message, chat_id: int) -> str:
        text = message.get('text')

        executed_game = await self.app.store.games.get_game_by_chat(chat_id)
        if executed_game is None:
            return await self.__none_handle(text, chat_id)
        match executed_game.state:
            case GameStates.WAITING_FOR_PLAYERS.value:
                return await self.__waiting_for_players_handle(message, text, executed_game.id)
            case GameStates.GAME_STARTED.value:
                return await self.__waiting_for_players_handle(text)
            case GameStates.ROUND1.value, GameStates.ROUND2.value, GameStates.ROUND3.value, GameStates.ROUND4.value:
                return await self.__round_handle(text)
            case GameStates.GAME_ENDED.value:
                return await self.__game_ended_handle(text)

    async def __none_handle(self, text: str, chat_id: int) -> str | None:
        if text == "/start":
                return "Укажите время ответа на вопрос в секундах (max - 180 секунд)"
        else:
            try:
                number = int(text)
                if number <= 180:
                    await self.app.store.games.create_game(chat_id, number)
                    return "Ждем присоединения игроков, напишите /join для присоединения"
                else:
                    return "Укажите число меньшее или равное 180"
            except:
                return "Укажите число"

    async def __waiting_for_players_handle(self, message, text: str, game_id) -> str | None:
        if text == "/join":
            message_user = message.get('from')

            # Проверяет есть ли этот user в БД
            user = await self.app.store.users.get_user_by_id(message_user.get('id'))
            if user is None:
                user_id = await self.app.store.users.create_user(message_user.get('id'), message_user.get('username'), message_user.get('first_name'))
            else:
                user_id = user.id

            # Проверяет есть ли этот participant в БД
            if await self.app.store.games.get_participant_by_user_id(user_id):
                return "Вы уже присоединены к игре"

            # Если нет - добавляет в БД нового participant и присваивает ему уровень сложности
            participants = await self.app.store.games.get_participants_by_game_id(game_id)
            participant_level = get_random_level(participants)
            if participant_level == 4:
                await self.app.store.games.create_participant(game_id, user_id, participant_level, True)
            else:
                await self.app.store.games.create_participant(game_id, user_id, participant_level)

            renewed_participants = await self.app.store.games.get_participants_by_game_id(game_id)
            if len(renewed_participants) != 3:
                return f"{len(renewed_participants)}/3 игроков присоединились к игре"
            else:
                await self.app.store.games.change_game_state(game_id, GameStates.GAME_STARTED.value)
                return f"Игра началась! Выберите тему игры:"
        return None

    async def __round_handle(self, text: str) -> str | None:
        return " "

    async def __game_ended_handle(self, text: str) -> str | None:
        return " "


def get_random_level(participants: Sequence[ParticipantModel]) -> int:
    available_numbers = [2, 3, 4]
    for participant in participants:
        available_numbers.remove(participant.level)
    return random.choice(available_numbers)