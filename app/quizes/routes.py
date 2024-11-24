import typing
__all__ = ("register_urls",)

from app.quizes.views import QuestionAddView

if typing.TYPE_CHECKING:
    from app.web.app import Application

def register_urls(application: "Application"):
    application.router.add_view("/question.add", QuestionAddView)