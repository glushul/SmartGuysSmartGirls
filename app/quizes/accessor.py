from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from sqlalchemy import insert, select, Sequence, Integer

from app.store.database.sqlalchemy_base import ThemeModel, AnswerModel, QuestionModel

if TYPE_CHECKING:
    from app.web.app import Application


class QuizAccessor:
    def __init__(self, app: "Application", *args, **kwargs) -> None:
        self.app = app
        self.database = app.database

    async def create_theme(self, title: str) -> ThemeModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                insert(ThemeModel).values(title=title).returning(ThemeModel.id)
            )
            theme_id = result.scalar_one()
        return ThemeModel(id=theme_id, title=title)

    async def list_themes(self) -> Sequence[ThemeModel]:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(ThemeModel)
            )
            return result.scalars().all()

    async def create_question(
            self, title: str, theme_id: int, answers: Iterable[AnswerModel]
    ) -> QuestionModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                insert(QuestionModel).values(title=title, theme_id=theme_id).returning(QuestionModel.id)
            )
            question_id = result.scalar_one()
            for answer in answers:
                await session.execute(
                    insert(AnswerModel).values(
                        title=answer.title,
                        is_correct=answer.is_correct,
                        question_id=question_id
                    )
                )
            return QuestionModel(id=question_id, title=title, theme_id=theme_id)

    async def list_questions_by_theme_id(self, theme_id: Integer) -> Sequence[QuestionModel] | None:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(QuestionModel).where(QuestionModel.theme_id == theme_id)
            )
            executed_questions = result.scalars().all()
            return executed_questions

    async def list_questions(self) -> Sequence[QuestionModel]:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(QuestionModel)
            )
            return result.scalars().all()

    async def list_answers_by_question_id(self, question_id: Integer) -> Sequence[AnswerModel] | None:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(AnswerModel).where(AnswerModel.question_id == question_id)
            )
            executed_answers = result.scalars().all()
            return executed_answers