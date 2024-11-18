
__all__ = ("setup_routes",)

import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application

def setup_routes(application: "Application"):
    import app.users.routes

    app.users.routes.register_urls(application)
