
import os
from dotenv import load_dotenv
load_dotenv()

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT1_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT1_TOKEN is not set")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BOT2_USERNAME = "linktotgk_bot"


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id

    ref_link = f"https://t.me/{BOT2_USERNAME}?start={user_id}"

    kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Количество переходов")]
    ],
    resize_keyboard=True
)

    await message.answer(
        f"Твоя реферальная ссылка:\n{ref_link}",
        reply_markup=kb
    )


@dp.message(lambda m: m.text == "Количество переходов")
async def count_refs(message: types.Message):
    user_id = message.from_user.id
    ref_code = f"/start {user_id}"

    data = supabase.table("ref_joins").select("id").eq("ref_code", ref_code).execute()
    count = len(data.data)

    await message.answer(f"Успешных переходов: {count} 🎉")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
