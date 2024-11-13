from aiogram import Router
from aiogram.types import Message


router = Router()

@router.message()
async def cmd_start(message: Message):
    await message.answer(message.text)