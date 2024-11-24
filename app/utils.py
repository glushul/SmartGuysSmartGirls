import random
from typing import Sequence

from app.store.database.sqlalchemy_base import ParticipantModel, ThemeModel, QuestionModel, AnswerModel


class Constants:
    TOKEN = '7672228221:AAGQstNZ4c4r30Ld6gqLAF-7yxmWSFJN-4Y'
    BOT_ID = 7672228221
    MAX_ANSWER_TIME = 180

class HelperFunctions:
    def get_random_level(participants: Sequence[ParticipantModel]) -> int:
        available_numbers = [2, 3, 4]
        for participant in participants:
            available_numbers.remove(participant.level)
        return random.choice(available_numbers)

    def get_level_title(level: int) -> str:
        match level:
            case 2:
                return "Красная дорожка"
            case 3:
                return "Желтая дорожка"
            case 4:
                return "Зеленая дорожка"

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