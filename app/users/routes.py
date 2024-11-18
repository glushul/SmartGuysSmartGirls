import typing
__all__ = ("register_urls",)

from app.users.views import UserLoginView


if typing.TYPE_CHECKING:
    from app.web.app import Application

def register_urls(application: "Application"):
    application.router.add_view("/user.login", UserLoginView)
