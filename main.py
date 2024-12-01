import asyncio
import typing

from aiohttp import web

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.web.app import setup_app


async def start_polling(app: "Application"):
    await app.bot_accessor.polling()

async def start_app(app: "Application"):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

if __name__ == '__main__':
    app = setup_app(config_path="")

    loop = asyncio.get_event_loop()

    loop.create_task(start_app(app))
    loop.create_task(start_polling(app))

    loop.run_forever()