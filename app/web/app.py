from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.store import Store, setup_store
from app.store.bot.manager import BotAccessor
from app.store.database.database import Database
from app.web.routes import setup_routes


class Application(AiohttpApplication):
    database: Database | None = None
    store: Store | None = None
    bot: BotAccessor | None = None

class Request(AiohttpRequest):

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self) -> Database:
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()


def setup_app(config_path: str) -> Application:
    setup_routes(app)
    setup_store(app)
    app.bot = BotAccessor()
    return app
