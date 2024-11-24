from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from sqlalchemy import insert, select, Integer

from app.store.database.sqlalchemy_base import ThemeModel, AnswerModel, QuestionModel, GameQuestionModel, GameModel

if TYPE_CHECKING:
    from app.web.app import Application


class ThemeAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app

    async def create_theme(self, title: str) -> ThemeModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(ThemeModel).values(title=title).returning(ThemeModel)
            )
            theme = result.scalars().first()
        return theme

    async def list_themes(self) -> Sequence[ThemeModel] | Sequence[None]:
        async with self.app.database.session as session:
            result = await session.execute(
                select(ThemeModel)
            )
            themes = result.scalars().all()
            return themes


class QuestionAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app

    async def create_question(self, title: str, theme_id: int, answers: Iterable[AnswerModel]) -> QuestionModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(QuestionModel).values(title=title, theme_id=theme_id).returning(QuestionModel)
            )
            question = result.scalars().first()
            answer_data = [
                {"title": answer.title, "is_correct": answer.is_correct, "question_id": question.id}
                for answer in answers
            ]
            if answer_data:
                await session.execute(insert(AnswerModel).values(answer_data))
            return question

    async def create_game_question(self, game_id: int, question_id: int) -> QuestionModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(GameQuestionModel).values(game_id=game_id, question_id=question_id).returning(GameQuestionModel)
            )
            game_question = result.scalars().first()
            return game_question

    async def list_questions_by_theme_id(self, theme_id: int) -> Sequence[QuestionModel] | Sequence[None]:
        async with self.app.database.session as session:
            result = await session.execute(
                select(QuestionModel).where(QuestionModel.theme_id == theme_id)
            )
            questions = result.scalars().all()
            return questions

    async def list_questions(self) -> Sequence[QuestionModel] | Sequence[None]:
        async with self.app.database.session as session:
            result = await session.execute(
                select(QuestionModel)
            )
            questions = result.scalars().all()
            return questions

    async def list_available_questions(self, game: GameModel) -> Sequence[QuestionModel] | Sequence[None]:
        async with self.app.database.session as session:
            subquery = select(GameQuestionModel.question_id).filter(GameQuestionModel.game_id == game.id).subquery()

            result = await session.execute(
                select(QuestionModel)
                .filter(QuestionModel.theme_id == game.theme_id)  # фильтр по теме
                .filter(~QuestionModel.id.in_(subquery))  # исключаем вопросы, уже связанные с игрой
            )

            questions = result.scalars().all()
            return questions

class AnswerAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app

    async def create_answer(self, title: str, is_correct: bool, question_id: int) -> AnswerModel:
        async with self.app.database.session as session:
            result = await session.execute(
                insert(AnswerModel).values(title=title, is_correct=is_correct, question_id=question_id).
                returning(AnswerModel)
            )
            answer = result.scalars().first()
            return answer

    async def list_answers_by_question_id(self, question_id: int) -> Sequence[AnswerModel] | Sequence[None]:
        async with self.app.database.session as session:
            result = await session.execute(
                select(AnswerModel).where(AnswerModel.question_id == question_id)
            )
            answers = result.scalars().all()
            return answers

    async def get_answer_by_id(self, answer_id: int) -> AnswerModel | None:
        async with self.app.database.session as session:
            result = await session.execute(
                select(AnswerModel).where(AnswerModel.id == answer_id)
            )
            answer = result.scalars().first()
            return answer