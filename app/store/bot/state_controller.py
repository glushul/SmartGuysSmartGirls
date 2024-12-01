import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Sequence

from sqlalchemy.util import await_only

from app.store.database.sqlalchemy_base import (
    AnswerModel,
    GameModel,
    ParticipantModel,
    QuestionModel,
    UserModel, ChatModel,
)
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
        self.timers = {}


    # region Обработка update (сообщения, callbackи, статусы игры, удаление и добавление в чат бота)

    async def handle_updates(self, update: dict):

        message, callback, chat_id = self._extract_message_and_chat(update=update)

        if not message or not chat_id:
            return

        if 'new_chat_members' in message:
            await self._handle_new_members(
                message=message,
                chat_id=chat_id
            )

        if 'left_chat_member' in message:
            await self._handle_left_member(message=message)
            return  # Бот удалён из чата, дальнейшая обработка не требуется

        # Обработка состояния игры
        await self._handle_game_state(
            chat_id=chat_id,
            message=message,
            update=update
        )

    def _extract_message_and_chat(self, update: dict):
        message = update.get("message")
        callback = update.get("callback_query")

        if callback:
            message = callback.get("message")

        chat_id = message.get("chat", {}).get("id") if message else None
        return message, callback, chat_id

    async def _handle_new_members(self, message: dict, chat_id: int):
        for new_member in message.get('new_chat_members', []):
            if new_member.get('is_bot') and new_member.get("id") == Constants.BOT_ID:

                # Добавление чата в базу данных
                if await self.app.store.chats.get_chat_by_id(chat_id=chat_id) is None:
                    await self.app.store.chats.create_chat(chat_id=chat_id)

                # Приветственное сообщение
                await self.app.bot_accessor.send_message(
                    chat_id=chat_id,
                    text=Constants.GREETING
                )

    async def _handle_left_member(self, message: dict):
        left_chat_member = message.get("left_chat_member")
        if left_chat_member and left_chat_member.get('is_bot') and left_chat_member.get("id") == Constants.BOT_ID:
            return  # Если бот удалён из чата, завершить обработку

    async def _handle_game_state(self, chat_id: int, message: dict, update: dict):
        game = await self.app.store.games.get_game_by_chat_id(chat_id=chat_id)
        text = message.get('text') if message else None

        if game is None:
            await self._info_command_handle(
                chat_id=chat_id,
                text=text
            )
            await self.__none_handle(
                text=text,
                chat_id=chat_id
            )
            return

        if game.state == GameStates.GAME_ENDED.value:
            await self._score_table_command_handle(
                game=game,
                text=text
            )
            await self._info_command_handle(
                chat_id=chat_id,
                text=text
            )
            await self.__none_handle(
                text=text,
                chat_id=chat_id
            )
            return

        # Обработка в зависимости от состояния игры
        match game.state:
            case GameStates.WAITING_FOR_ANSWER_TIME.value:
                await self._waiting_for_answer_time_handle(
                    text=text,
                    game=game
                )
            case GameStates.WAITING_FOR_PLAYERS.value:
                await self._waiting_for_players_handle(
                    message=message,
                    text=text,
                    game=game
                )
            case GameStates.QUESTION_ASKED.value:
                await self._question_asked_handle(game=game)
            case GameStates.WAITING_FOR_ANSWER.value:
                await self._waiting_for_answer_handle(
                    update=update,
                    game=game
                )
    # endregion

    # region Обработка отсутствия статуса игры

    async def __none_handle(self, text: str, chat_id: int):
        if text == "/start@SmartGirls_SmartBoys_Bot":
            await self.app.store.games.create_game(chat_id=chat_id)
            await self.app.bot_accessor.send_message(
                chat_id=chat_id,
                text="Укажите время ответа на вопрос в секундах (максимальное время - 180 секунд)."
            )

    # endregion

    # region Обработка статуса игры WAITING_FOR_ANSWER_TIME

    async def _waiting_for_answer_time_handle(self, text: str, game: GameModel):
        if text.isdigit():
            answer_time = int(text)
            if answer_time > Constants.MAX_ANSWER_TIME:
                await self.app.bot_accessor.send_message(
                    chat_id=game.chat_id,
                    text="Укажите число меньшее или равное 180."
                )
            else:
                await self.app.store.games.update_game(
                    game_id=game.id,
                    state=GameStates.WAITING_FOR_PLAYERS.value,
                    answer_time=answer_time
                )
                await self.app.bot_accessor.send_message(
                    chat_id=game.chat_id,
                    text="Ждем присоединения игроков, напишите /join@SmartGirls_SmartBoys_Bot для присоединения."
                )
        else:
            await self.app.bot_accessor.send_message(
                chat_id=game.chat_id,
                text="Укажите корректное число (например, 30)."
            )
            return

    # endregion

    # region Обработка статуса игры WAITING_FOR_PLAYERS

    async def _waiting_for_players_handle(self, message: dict, text: str, game: GameModel):
        if text == "/join@SmartGirls_SmartBoys_Bot":
            user = await self._get_or_create_user(message_user=message.get('from'))
            # Если этот пользователь уже является участником игры
            if await self.app.store.participants.get_participant_by_user_game_id(
                    user_id=user.id,
                    game_id=game.id
            ):
                await self.app.bot_accessor.send_message(
                    chat_id=game.chat_id,
                    text="Вы уже присоединены к игре"
                )
                return
            else:
                await self._add_participant_to_game(
                    user=user,
                    game=game
                )
                await self._handle_game_progress(game=game)

    async def _get_or_create_user(self, message_user: dict) -> UserModel:
        user_id = message_user["id"]
        user = await self.app.store.users.get_user_by_id(user_id=user_id)
        if not user:
            user = await self.app.store.users.create_user(
                user_id=user_id,
                username=message_user.get('username'),
                name=message_user.get('first_name')
            )
        return user

    async def _add_participant_to_game(self, user: UserModel, game: GameModel) -> ParticipantModel:
        # Определяет уровень сложности участника
        participants = await self.app.store.participants.get_participants_by_game_id(game_id=game.id)
        participant_level = HelperFunctions.get_random_level(participants=participants)

        participant = await self.app.store.participants.create_participant(
            game_id=game.id,
            user_id=user.id,
            level=participant_level,
            current=(participant_level == 4)
        )
        return participant

    async def _handle_game_progress(self, game: GameModel):
        participants = await self.app.store.participants.get_participants_by_game_id(game_id=game.id)

        if len(participants) < 3:
            await self.app.bot_accessor.send_message(
                chat_id=game.chat_id,
                text=f"{len(participants)} из 3 игроков присоединились к игре"
            )
            return
        else:
            await self._start_game(
                game=game,
                participants=participants
            )

    async def _start_game(self, game: GameModel, participants: list[ParticipantModel]):
        themes = await self.app.store.themes.list_themes()
        game_theme = HelperFunctions.get_random_theme(themes)

        participants_string = ""
        for participant in participants:
            user = await self.app.store.users.get_user_by_id(participant.user_id)
            participants_string += f"{user.name}: {HelperFunctions.get_level_title(participant.level)}\n"

        await self.app.store.games.update_game(
            game_id=game.id,
            state=GameStates.QUESTION_ASKED.value,
            theme_id=game_theme.id
        )

        await self.app.bot_accessor.send_message(
            chat_id=game.chat_id,
            text=f"Игра началась! Тема игры: {game_theme.title}\n{participants_string}\nОтправь любое сообщение для начала игры"
        )

    # endregion

    # region Обработка статуса игры QUESTION_ASKED

    async def _question_asked_handle(self, game: GameModel) -> None:
        # Получает вопрос и ответы
        random_question, answers = await self._get_question_and_answers(game)

        # Получает текущего участника
        current_participant = await self.app.store.participants.get_current_participant(game_id=game.id)
        if current_participant is None:
            await self._handle_no_participants_left(game)
            return


        current_user = await self.app.store.users.get_user_by_id(current_participant.user_id)

        await self.app.bot_accessor.send_message(
            chat_id=game.chat_id,
            text=f"{current_user.name} на {HelperFunctions.convert_number_to_smile(current_participant.correct_answers
                    +current_participant.incorrect_answers+1)} раунде из "
                 f"{HelperFunctions.convert_number_to_smile(current_participant.level)} \n"
                 f"Вам можно ошибиться {current_participant.level - 2 - current_participant.incorrect_answers} раз.")

        # Задает вопрос
        keyboard = HelperFunctions.create_keyboard(answers)
        await self.app.bot_accessor.send_message_with_button(
            chat_id=game.chat_id,
            text=f"{current_user.name}, {random_question.title}",
            keyboard=keyboard
        )

        # Обновляет состояние игры
        await self.app.store.questions.create_game_question(
            game_id=game.id,
            question_id=random_question.id)
        await self.app.store.games.update_game(
            game_id=game.id,
            state=GameStates.WAITING_FOR_ANSWER.value,
            current_question_id=random_question.id
        )

        # Запускает таймер
        await self._start_timer(game)

    async def _get_question_and_answers(self, game: GameModel) -> tuple[QuestionModel | None, list[AnswerModel]]:
        available_questions = await self.app.store.questions.list_available_questions(game=game)
        if not available_questions:
            return None, []
        random_question = HelperFunctions.get_random_question(questions=available_questions)
        answers = await self.app.store.answers.list_answers_by_question_id(question_id=random_question.id)
        return random_question, answers

    async def _handle_no_participants_left(self, game: GameModel) -> None:
        await self.app.bot_accessor.send_message(
            chat_id=game.chat_id,
            text="В этой игре никто не выиграл! Игра окончена.")
        await self._game_ended_handle(game=game)

    async def _start_timer(self, game: GameModel) -> None:
        if game.id in self.timers:
            self.timers[game.id].cancel()  # Отмена старого таймера
        self.timers[game.id] = asyncio.create_task(self._handle_answer_timeout(game))  # Создание нового таймера

    async def _handle_answer_timeout(self, game: GameModel):
        try:
            await asyncio.sleep(game.answer_time)

            current_participant = await self.app.store.participants.get_current_participant(game_id=game.id)
            current_user = await self.app.store.users.get_user_by_id(user_id=current_participant.user_id)

            await self.app.bot_accessor.send_message(
                chat_id=game.chat_id,
                text=f"{current_user.name} не успел(а) ответить. Штрафной балл!"
            )
            participant = await self.app.store.participants.update_participant(
                user_id=current_participant.user_id,
                game_id=game.id,
                incorrect_answers=current_participant.incorrect_answers + 1
            )
            await self._check_participant_elimination(game, participant)
            if await self._check_game_winner(game, participant):
                return

            await self.app.store.participants.change_current_participant(game_id=game.id)
            await self._question_asked_handle(game=game)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Unexpected error in timer for game {game.id}: {e}")

    # endregion

    # region Обработка статуса игры WAITING_FOR_ANSWER

    async def _waiting_for_answer_handle(self, game: GameModel, update: dict):
        callback = update.get("callback_query")
        if not callback:
            return  # Если callback отсутствует, ничего не делает

        user_id = callback["from"]["id"]
        callback_data = callback["data"]
        current_participant = await self.app.store.participants.get_current_participant(game_id=game.id)

        answer = await self.app.store.answers.get_answer_by_id(answer_id=int(callback_data))
        if answer.question_id != game.current_question_id:
            await self._handle_invalid_question(callback=callback)
            return

        if not current_participant or user_id != current_participant.user_id:
            await self._handle_not_current_turn(callback=callback)
            return

        await self._handle_valid_answer(
            game=game,
            participant=current_participant,
            answer=answer,
            callback=callback
        )

    async def _handle_not_current_turn(self, callback: dict):
        await self.app.bot_accessor.answer_callback_query(
            callback_query_id=callback["id"],
            text="Сейчас не ваш ход!"
        )

    async def _handle_invalid_question(self, callback: dict):
        await self.app.bot_accessor.answer_callback_query(
            callback_query_id=callback["id"],
            text="Этот вопрос не актуален"
        )

    async def _handle_valid_answer(self, game: GameModel, participant: ParticipantModel, answer: AnswerModel, callback: dict):
        if answer.is_correct:
            await self._handle_correct_answer(
                game=game,
                participant=participant,
                answer=answer,
                callback=callback
            )
        else:
            await self._handle_incorrect_answer(
                game=game,
                participant=participant,
                answer=answer,
                callback=callback
            )

    async def _handle_correct_answer(self, game: GameModel, participant: ParticipantModel, answer: AnswerModel, callback: dict):
        await self.app.bot_accessor.answer_callback_query(
            callback_query_id=callback["id"],
            text="Ваш ответ принят"
        )
        await self.app.bot_accessor.send_message(
            chat_id=game.chat_id,
            text=f"«{answer.title}» - это правильный ответ!"
        )
        participant = await self.app.store.participants.update_participant(
            user_id=participant.user_id,
            game_id=game.id,
            correct_answers=participant.correct_answers + 1
        )
        if await self._check_game_winner(
                game=game,
                participant=participant
        ):
            return

        await self.app.store.participants.change_current_participant(game_id=game.id)

        await self._question_asked_handle(game=game)

    async def _handle_incorrect_answer(self, game: GameModel, participant: ParticipantModel, answer: AnswerModel, callback: dict):
        await self.app.bot_accessor.answer_callback_query(
            callback_query_id=callback["id"],
            text="Ваш ответ принят"
        )
        await self.app.bot_accessor.send_message(
            chat_id=game.chat_id,
            text=f"«{answer.title}» - это неправильный ответ! Штрафной балл!"
        )
        participant = await self.app.store.participants.update_participant(
            user_id=participant.user_id,
            game_id=game.id,
            incorrect_answers=participant.incorrect_answers + 1
        )
        await self._check_participant_elimination(
            game=game,
            participant=participant
        )
        if await self._check_game_winner(
            game=game,
            participant=participant
        ):
            return

        await self.app.store.participants.change_current_participant(game_id=game.id)

        await self._question_asked_handle(game=game)

    async def _check_game_winner(self, game: GameModel, participant: ParticipantModel):
        if (participant.correct_answers + participant.incorrect_answers == participant.level and
                participant.incorrect_answers <= participant.level - 2):
            user = await self.app.store.users.get_user_by_id(user_id=participant.user_id)
            await self.app.bot_accessor.send_message(
                chat_id=game.chat_id,
                text=f"Поздравляю, {user.name}, вы победитель! +{participant.correct_answers} балла к рейтингу."
            )
            await self.app.store.users.update_user(
                user_id=user.id,
                score=user.score + participant.correct_answers
            )
            await self._game_ended_handle(game=game)
            return True
        return False

    async def _check_participant_elimination(self, game: GameModel, participant: ParticipantModel):
        user = await self.app.store.users.get_user_by_id(user_id=participant.user_id)
        if participant.incorrect_answers > participant.level - 2:
            await self.app.bot_accessor.send_message(
                chat_id=game.chat_id,
                text=f"Вы потратили все свои штрафные баллы. {user.name} выбывает из игры."
            )
            return True
        return False

    # endregion

    # region Обработка статуса игры GAME_ENDED

    async def _game_ended_handle(self, game: GameModel):
        renewed_game = await self.app.store.games.update_game(
            game_id=game.id,
            state=GameStates.GAME_ENDED.value
        )
        await self.app.bot_accessor.send_message(
            chat_id=game.chat_id,
            text=await self._get_score_table(game=renewed_game)
        )
        if game.id in self.timers:
            timer = self.timers[game.id]
            if timer:
                timer.cancel()

    async def _get_score_table(self, game: GameModel) -> str:
        result = "Рейтинг игроков:"

        participants = await self.app.store.participants.get_participants_by_game_id(game_id=game.id)
        users = await self.app.store.users.get_users_by_game_id(game_id=game.id)

        if game.state == GameStates.GAME_ENDED.value:
            for participant in participants:
                matching_user = next(user for user in users if user.id == participant.user_id)
                if matching_user:
                    if participant.current:
                        result += f"\n{matching_user.name}: {matching_user.score} балла (+{participant.correct_answers})"
                    else:
                        result += f"\n{matching_user.name}: {matching_user.score} балла"
        else:
            for participant in participants:
                matching_user = next(user for user in users if user.id == participant.user_id)
                if matching_user:
                    result += f"\n{matching_user.name}: {participant.correct_answers} балла"

        return result

    # endregion

    # region Обработка дополнительных команд

    async def _info_command_handle(self, chat_id: int, text: str):
        if text == "/info@SmartGirls_SmartBoys_Bot":
            await self.app.bot_accessor.send_message(
                chat_id=chat_id,
                text=Constants.GREETING
            )


    async def _score_table_command_handle(self, game: GameModel, text: str):
        if text == "/score_table@SmartGirls_SmartBoys_Bot":
            await self.app.bot_accessor.send_message(
                chat_id=game.chat_id,
                text=await self._get_score_table(game=game)
            )

    # endregion