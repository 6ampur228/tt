
import os
from dotenv import load_dotenv
load_dotenv()

import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT2_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TGK_CHANNEL = "@giftoryhub"  # канал для проверки подписки
TGK_URL = "https://t.me/giftoryhub"

if not BOT_TOKEN:
    raise RuntimeError("BOT2_TOKEN is not set")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временное хранилище реф-кодов: user_id -> ref_code
ref_cache: dict[int, str] = {}


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    args = message.text.split()

    if len(args) > 1:
        # пользователь пришёл по реф-ссылке
        referrer_id = args[1]
        ref_code = f"/start {referrer_id}"

        ref_cache[message.from_user.id] = ref_code

        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Перейти в канал", url=TGK_URL)],
            [types.InlineKeyboardButton(text="Я зашёл", callback_data="check_sub")]
        ])

        await message.answer(
            "Спасибо, что перешёл по ссылке!\n"
            "Подпишись на канал и затем нажми «Я зашёл».",
            reply_markup=kb
        )
    else:
        await message.answer(
            "Привет! Это бот для учёта рефералов.\n"
            "Приходи по реферальной ссылке, чтобы быть засчитанным 😎"
        )


@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Проверяем, что пользователь вообще пришёл по реф-ссылке
    ref_code = ref_cache.get(user_id)
    if not ref_code:
        await callback.answer("Не вижу, что ты пришёл по реф-ссылке 😕", show_alert=True)
        return

    # Проверка подписки на канал
    try:
        member = await bot.get_chat_member(TGK_CHANNEL, user_id)
        if member.status not in ("member", "creator", "administrator"):
            await callback.answer("Сначала подпишись на канал 🥺", show_alert=True)
            return
    except Exception as e:
        logging.exception("Ошибка при get_chat_member")
        await callback.answer("Не смог проверить подписку, попробуй позже 🙏", show_alert=True)
        return

    # Проверяем, не существует ли уже запись
    exists = supabase.table("ref_joins").select("id").eq("user_id", user_id).execute()
    if exists.data:
        await callback.answer("Ты уже засчитан как реферал 😎", show_alert=True)
        return

    # Добавляем запись в базу
    supabase.table("ref_joins").insert({
        "user_id": user_id,
        "ref_code": ref_code
    }).execute()

    await callback.answer("Готово! Ты засчитан 🎉", show_alert=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
