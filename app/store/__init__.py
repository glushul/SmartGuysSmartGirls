import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.games.accessor import GameAccessor, ParticipantAccessor
        from app.quizes.accessor import (
            AnswerAccessor,
            QuestionAccessor,
            ThemeAccessor,
        )
        from app.users.accessor import (
            ChatAccessor,
            UpdateAccessor,
            UserAccessor,
        )

        self.users = UserAccessor(app)
        self.chats = ChatAccessor(app)
        self.chat_updates = UpdateAccessor(app)
        self.games = GameAccessor(app)
        self.participants = ParticipantAccessor(app)
        self.themes = ThemeAccessor(app)
        self.questions = QuestionAccessor(app)
        self.answers = AnswerAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
