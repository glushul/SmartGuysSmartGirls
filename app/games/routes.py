import typing

__all__ = ("register_urls",)

from app.games.views import GameListView, ParticipantListView

if typing.TYPE_CHECKING:
    from app.web.app import Application

def register_urls(application: "Application"):
    application.router.add_view("/games.list", GameListView)
    application.router.add_view("/participants.list", ParticipantListView)