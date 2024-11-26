import random
from enum import Enum
from typing import Sequence

from app.store.database.sqlalchemy_base import (
    AnswerModel,
    ParticipantModel,
    QuestionModel,
    ThemeModel,
)


class Constants:
    TOKEN = '7672228221:AAGQstNZ4c4r30Ld6gqLAF-7yxmWSFJN-4Y'
    BOT_ID = 7672228221
    MAX_ANSWER_TIME = 180
    GREETING = (
        "Привет! Я бот Умники и Умницы, и рад быть здесь!\n"
        "Чтобы начать игру, напиши команду /start@SmartGirls_SmartBoys_Bot. Следуй инструкциям, и мы начнем!\n\n"
        "Как это работает:\n\n"
        "1. Запуск игры и присоединение:\n"
        "Администратор чата запускает игру, после чего каждый игрок может присоединиться, написав специальный тег. "
        "В игре может участвовать максимум 3 игрока.\n\n"
        "2. Назначение уровней:\n"
        "Бот случайным образом назначает каждому игроку уровень сложности от 2 до 4.\n"
        "Уровень сложности определяет количество вопросов, на которые игрок должен ответить:\n"
        "   - Уровень 2 — 2 вопроса\n"
        "   - Уровень 3 — 3 вопроса\n"
        "   - Уровень 4 — 4 вопроса\n\n"
        "3. Штрафные очки:\n"
        "Количество возможных ошибок (штрафных очков) у каждого игрока зависит от уровня сложности:\n"
        "   - Игроки с уровнем 2 не имеют штрафных очков и должны ответить правильно на все вопросы.\n"
        "   - Игроки с уровнем 3 могут ошибиться один раз (1 штрафное очко).\n"
        "   - Игроки с уровнем 4 могут ошибиться дважды (2 штрафных очка).\n\n"
        "4. Выбывание:\n"
        "Если игрок исчерпывает свои штрафные очки, он выбывает из игры.\n\n"
        "5. Победа:\n"
        "Игра состоит максимум из 4 раундов — в каждом раунде задается один вопрос каждому игроку. "
        "Игра заканчивается, когда кто-то успешно отвечает на все вопросы, допустив при этом не больше штрафных очков, чем это позволяет его уровень. "
        "Этот игрок становится победителем!\n\n"
        "Напиши /start@SmartGirls_SmartBoys_Bot, чтобы присоединиться и начать игру! 🎉"
    )
    DEFAULT_ANSWER_TIME = 30


class HelperFunctions:

    def get_random_level(participants: Sequence[ParticipantModel]) -> int:
        available_numbers = [2, 3, 4]
        for participant in participants:
            available_numbers.remove(participant.level)
        return random.choice(available_numbers)

    def get_level_title(level: int) -> str:
        match level:
            case 2:
                return "Красная дорожка🔴"
            case 3:
                return "Желтая дорожка🟡"
            case 4:
                return "Зеленая дорожка🟢"

    def get_random_theme(themes: Sequence[ThemeModel]) -> ThemeModel:
        return random.choice(themes)

    def get_random_question(questions: Sequence[QuestionModel]) -> QuestionModel:
        return random.choice(questions)

    def create_keyboard(answers: Sequence[AnswerModel]):
        shuffled_answers = list(answers)
        random.shuffle(shuffled_answers)

        result = {
            "inline_keyboard": []
        }
        for answer in shuffled_answers:
            result["inline_keyboard"].append([{"text": answer.title, "callback_data": str(answer.id)}])

        return result

    def convert_number_to_smile(number: int) -> str:
        number_to_smile = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            0: "0️⃣"
        }
        return number_to_smile[int(number)]

