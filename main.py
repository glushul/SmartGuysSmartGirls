import asyncio
from aiogram import Bot, Dispatcher

from app.store.bot.manager import router


async def main():
    bot = Bot(token='8044877151:AAGWmRwcjLTRqD3iIUFxm3-jFeWkHetkaX8')
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')