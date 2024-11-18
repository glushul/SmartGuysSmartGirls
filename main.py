import asyncio

from aiohttp import web
from aiohttp.web import run_app

from app.store.bot.manager import get_updates, send_message, polling
from app.web.app import setup_app

async def start_polling():
    await polling()

async def start_app():
    app = setup_app(config_path="")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.create_task(start_polling())
    loop.create_task(start_app())

    loop.run_forever()
