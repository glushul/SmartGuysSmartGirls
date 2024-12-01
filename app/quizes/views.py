from aiohttp.web_response import json_response

from app.store.database.sqlalchemy_base import AnswerModel
from app.web.app import View


class QuestionAddView(View):

    async def post(self):
        data = await self.request.json()
        questions_data = data["questions"]

        result = {"question_ids": []}
        for question in questions_data:
            answers_data = question["answers"]
            answers = []
            for answer in answers_data:
                answers.append(
                    AnswerModel(
                        question_id=0,
                        title=answer["title"],
                        is_correct=answer["is_correct"]
                    )
                )
            new_question = await self.store.questions.create_question(
                theme_id=question["theme_id"],
                title=question["title"],
                answers=answers
            )
            result["question_ids"] += new_question.id

        return json_response(data=result)