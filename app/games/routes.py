import typing
__all__ = ("register_urls",)

if typing.TYPE_CHECKING:
    from app.web.app import Application

def register_urls(application: "Application"):
    pass