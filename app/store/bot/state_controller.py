from enum import Enum
from typing import TYPE_CHECKING

from app.store.database.sqlalchemy_base import GameModel
from app.utils import Constants, HelperFunctions

if TYPE_CHECKING:
    from app.web.app import Application

class GameStates(Enum):
    WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
    WAITING_FOR_ANSWER_TIME = "WAITING_FOR_ANSWER_TIME"
    QUESTION_ASKED = "QUESTION_ASKED"
    WAITING_FOR_ANSWER = "WAITING_FOR_ANSWER"
    GAME_ENDED = "GAME_ENDED"


class BotHandler:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, update):

        message, callback, chat_id = self._extract_message_and_chat(update)

        if not message or not chat_id:
            return

        if 'new_chat_members' in message:
            await self._handle_new_members(message, chat_id)

        if 'left_chat_member' in message:
            await self._handle_left_member(message)
            return  # Бот удалён из чата, дальнейшая обработка не требуется

        # Обработка состояния игры
        await self._handle_game_state(chat_id, message, update)

    def _extract_message_and_chat(self, update):
        message = update.get("message")
        callback = update.get("callback_query")

        if callback:
            message = callback.get("message")

        chat_id = message.get("chat", {}).get("id") if message else None
        return message, callback, chat_id

    async def _handle_new_members(self, message, chat_id):
        for new_member in message.get('new_chat_members', []):
            if new_member.get('is_bot') and new_member.get("id") == Constants.BOT_ID:

                # Добавление чата в базу данных
                if await self.app.store.chats.get_chat_by_id(chat_id=chat_id) is None:
                    await self.app.store.chats.create_chat(chat_id=chat_id)

                # Приветственное сообщение
                await self.app.bot_accessor.send_message(
                    chat_id=chat_id,
                    text=f"Привет! Я бот {new_member['username']} и рад быть здесь! Напиши /start, чтобы начать игру"
                )

    async def _handle_left_member(self, message):
        left_chat_member = message.get("left_chat_member")
        if left_chat_member and left_chat_member.get('is_bot') and left_chat_member.get("id") == Constants.BOT_ID:
            return  # Если бот удалён из чата, завершить обработку

    async def _handle_game_state(self, chat_id, message, update):
        game = await self.app.store.games.get_game_by_chat_id(chat_id=chat_id)
        text = message.get('text') if message else None

        if game is None:
            await self.__none_handle(text=text, chat_id=chat_id)
            return

        # Обработка в зависимости от состояния игры
        match game.state:
            case GameStates.WAITING_FOR_ANSWER_TIME.value:
                await self.__waiting_for_answer_time_handle(text=text, game=game)
            case GameStates.WAITING_FOR_PLAYERS.value:
                await self.__waiting_for_players_handle(message=message, text=text, game=game)
            case GameStates.QUESTION_ASKED.value:
                await self.__question_asked_handle(game=game)
            case GameStates.WAITING_FOR_ANSWER.value:
                await self.__waiting_for_answer_handle(update=update, game=game)
            case GameStates.GAME_ENDED.value:
                await self.__game_ended_handle(text=text)


    async def __none_handle(self, text: str, chat_id: int):
        if text == "/start":
            await self.app.store.games.create_game(chat_id=chat_id)
            await self.app.bot_accessor.send_message(chat_id=chat_id,
                                                     text="Укажите время ответа на вопрос в секундах (max - 180 секунд).")

    async def __waiting_for_answer_time_handle(self, text: str, game: GameModel):
        answer_time = None
        try:
            answer_time = int(text)
        except ValueError:
            await self.app.bot_accessor.send_message(chat_id=game.chat_id,
                                                     text="Укажите корректное число (например, 30).")
            return

        if answer_time > Constants.MAX_ANSWER_TIME:
            await self.app.bot_accessor.send_message(chat_id=game.chat_id,
                                                     text="Укажите число меньшее или равное 180.")
        else:
            await self.app.store.games.update_game(game_id=game.id, state=GameStates.WAITING_FOR_PLAYERS.value,
                                                   answer_time=answer_time)
            await self.app.bot_accessor.send_message(chat_id=game.chat_id,
                                                         text="Ждем присоединения игроков, напишите /join для присоединения.")

    async def __waiting_for_players_handle(self, message, text: str, game: GameModel) -> str | None:
        if text == "/join":
            message_user = message.get('from')
            message_user_id = message.get('from')["id"]
            user = await self.app.store.users.get_user_by_id(user_id=message_user_id)
            if user is None:
                user = await self.app.store.users.create_user(
                    user_id=message_user_id, username=message_user.get('username'), name=message_user.get('first_name'))

            # Проверяет есть ли этот participant в БД
            if await self.app.store.participants.get_participant_by_user_game_id(user_id=user.id, game_id=game.id):
                await self.app.bot_accessor.send_message(chat_id=game.chat_id,
                                                         text="Вы уже присоединены к игре")
                return

            # Если нет - добавляет в БД нового participant и присваивает ему уровень сложности
            participants = await self.app.store.participants.get_participants_by_game_id(game_id=game.id)
            participant_level = HelperFunctions.get_random_level(participants)
            if participant_level == 4:
                await self.app.store.participants.create_participant(
                    game_id=game.id, user_id=user.id, level=participant_level, current=True)
            else:
                await self.app.store.participants.create_participant(
                    game_id=game.id, user_id=user.id, level=participant_level)

            #Начинает игру, если игроков 3, продолжает ждать игроков если меньше
            renewed_participants = await self.app.store.participants.get_participants_by_game_id(game_id=game.id)
            if len(renewed_participants) != 3:
                await self.app.bot_accessor.send_message(chat_id=game.chat_id,
                                                         text= f"{len(renewed_participants)}/3 игроков присоединились к игре")
            else:
                #Выбирает рандомную тему игры
                themes = await self.app.store.themes.list_themes()
                game_theme = HelperFunctions.get_random_theme(themes)

                #Выводит приветственную строку
                participants_string = ""
                for participant in renewed_participants:
                    user = await self.app.store.users.get_user_by_id(user_id=participant.user_id)
                    participants_string += f"{user.name}: {HelperFunctions.get_level_title(participant.level)}\n"
                await self.app.bot_accessor.send_message(
                    chat_id=game.chat_id, text=f"Игра началась! Тема игры: {game_theme.title}\n" + participants_string)

                #Меняет статус игры
                await self.app.store.games.update_game(game_id=game.id, state=GameStates.QUESTION_ASKED.value, theme_id=game_theme.id)
                await self.__question_asked_handle(game=game)

    async def __question_asked_handle(self, game: GameModel):
        #Получает вопрос и ответы к нему
        available_questions = await self.app.store.questions.list_available_questions(game=game)
        random_question = HelperFunctions.get_random_question(available_questions)
        answers = await self.app.store.answers.list_answers_by_question_id(question_id=random_question.id)
        keyboard = HelperFunctions.create_keyboard(answers)

        #Выбирает текущего игрока
        current_participant = await self.app.store.participants.get_current_participant(game_id=game.id)
        if current_participant is None:
            await self.app.bot_accessor.send_message(chat_id=game.chat_id, text=f"В этой игре никто не выиграл!")
            await self.app.store.games.update_game(game_id=game.id, state=GameStates.GAME_ENDED.value)
            return
        current_user = await self.app.store.users.get_user_by_id(current_participant.user_id)

        #Задает вопрос
        await self.app.bot_accessor.send_message_with_button(chat_id=game.chat_id,
                                                             text=f"{current_user.name}, {str.lower(random_question.title)}",
                                                             keyboard=keyboard)
        await self.app.store.questions.create_game_question(game_id=game.id, question_id=random_question.id)
        await self.app.store.games.update_game(game_id=game.id, state=GameStates.WAITING_FOR_ANSWER.value, current_question_id=random_question.id)

    async def __waiting_for_answer_handle(self, game: GameModel, update):
        callback = update.get("callback_query")
        if not callback:
            return  # Если callback отсутствует, ничего не делает
        user_id = callback["from"]["id"]
        callback_data = callback["data"]

        current_participant = await self.app.store.participants.get_current_participant(game_id=game.id)
        current_user = await self.app.store.users.get_user_by_id(user_id=current_participant.user_id)
        answer = await self.app.store.answers.get_answer_by_id(answer_id=int(callback_data))
        current_question_id = game.current_question_id

        # Если дан ответ не на текущий вопрос
        if answer.question_id != current_question_id:
            await self.app.bot_accessor.answer_callback_query(callback_query_id=callback["id"],
                                                          text="Этот вопрос не актуален")
        # Если дан ответ на текущий вопрос и текущим игроком
        elif user_id == current_participant.user_id:
            await self.app.bot_accessor.answer_callback_query(callback_query_id=callback["id"], text="Ваш ответ принят")
            # Если ответ правильный
            if answer.is_correct:
                await self.app.bot_accessor.send_message(chat_id=game.chat_id, text=f"«{answer.title}» -"
                                                                               f" это правильный ответ!")
                await self.app.store.participants.change_current_participant(game_id=game.id)
                await self.app.store.games.update_game(game_id=game.id, state=GameStates.QUESTION_ASKED.value)
                participant = await self.app.store.participants.update_participant(user_id=current_participant.user_id,
                                                                     game_id=current_participant.game_id,
                                                                     correct_answers=current_participant.correct_answers+1)
                if participant.correct_answers + participant.incorrect_answers == participant.level:
                    await self.app.bot_accessor.send_message(chat_id=game.chat_id,
                                                             text=f"Поздравляю, {current_user.name} победитель! +{participant.correct_answers} балла")
                    await self.app.store.games.update_game(game_id=game.id, state=GameStates.GAME_ENDED.value)
                    return
                await self.__question_asked_handle(game=game)
            # Если ответ неправильный
            else:
                await self.app.bot_accessor.send_message(chat_id=game.chat_id, text=f"«{answer.title}» -"
                                                                               f" это неправильный ответ! Штрафной балл!")
                await self.app.store.participants.change_current_participant(game_id=game.id)
                await self.app.store.games.update_game(game_id=game.id, state=GameStates.QUESTION_ASKED.value)
                participant = await self.app.store.participants.update_participant(user_id=current_participant.user_id,
                                                                     game_id=current_participant.game_id,
                                                                     incorrect_answers=current_participant.incorrect_answers+1)
                if participant.incorrect_answers > participant.level - 2:
                    await self.app.bot_accessor.send_message(chat_id=game.chat_id, text=f"Вы потратили все свои штрафные очки. Вы проиграли.")
                await self.__question_asked_handle(game=game)
        else:
            await self.app.bot_accessor.answer_callback_query(callback_query_id=callback["id"], text="Сейчас не ваш ход!")

    async def __game_ended_handle(self, text: str) -> str | None:
        return " "
