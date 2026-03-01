import asyncio
import os
import logging
from typing import Dict, List

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from database import init_db, add_or_update_user, get_stats
from aiogram.filters import Command

# =========================
# Конфигурация
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY не найден")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# Память
# =========================
user_sessions: Dict[int, List[Dict]] = {}

SYSTEM_PROMPT = {"role": "system", "content": "Ты полезный AI-помощник."}

MAX_HISTORY = 10
TELEGRAM_LIMIT = 4000

# =========================
# UI
# =========================
def get_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔁 Перегенерировать", callback_data="regenerate"),
                InlineKeyboardButton(text="🧹 Очистить память", callback_data="clear")
            ]
        ]
    )

# =========================
# Memory utils
# =========================
def get_user_history(user_id: int):
    if user_id not in user_sessions:
        user_sessions[user_id] = [SYSTEM_PROMPT.copy()]
    return user_sessions[user_id]

def trim_history(user_id: int):
    history = user_sessions[user_id]
    system_msg = history[0]
    trimmed = history[-(MAX_HISTORY - 1):]
    user_sessions[user_id] = [system_msg] + trimmed

# =========================
# AI Service
# =========================
async def request_model(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = [
        "stepfun/step-3.5-flash:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3-8b-instruct:free"
    ]

    async with aiohttp.ClientSession() as session:
        for model in models:
            try:
                payload = {"model": model, "messages": messages}

                async with session.post(url, headers=headers, json=payload, timeout=60) as response:
                    if response.status != 200:
                        logging.warning(f"{model} вернул статус {response.status}")
                        continue

                    result = await response.json()

                    if "choices" in result:
                        return result["choices"][0]["message"]["content"]

            except Exception:
                logging.exception(f"Ошибка при запросе модели {model}")

    return None

# =========================
# Handlers
# =========================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! 🤖 Я AI-бот с памятью.\n\n"
        "Используй кнопки под ответом 👇"
    )

@dp.message(Command("reset"))
async def reset_handler(message: types.Message):
    user_sessions.pop(message.from_user.id, None)
    await message.answer("✅ Память очищена!")

@dp.callback_query(F.data == "clear")
async def clear_memory(callback: types.CallbackQuery):
    user_sessions.pop(callback.from_user.id, None)
    await callback.message.answer("✅ Память очищена!")
    await callback.answer()

@dp.callback_query(F.data == "regenerate")
async def regenerate_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    history = get_user_history(user_id)

    if len(history) < 2:
        await callback.answer("Нечего перегенерировать 🙂", show_alert=True)
        return

    if history[-1]["role"] == "assistant":
        history.pop()

    await callback.answer()
    await process_ai(callback.message, user_id)

@dp.message()
async def ai_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    add_or_update_user(user_id, username)
    if not message.text:
        await message.answer("Я понимаю только текст 🙂")
        return

    history = get_user_history(user_id)

    history.append({"role": "user", "content": message.text})
    trim_history(user_id)

    await process_ai(message, user_id)

# =========================
# Core logic
# =========================
async def process_ai(message: types.Message, user_id: int):
    await bot.send_chat_action(message.chat.id, "typing")

    history = get_user_history(user_id)
    answer = await request_model(history)

    if not answer:
        await message.answer("⚠️ Все модели недоступны.")
        return

    if len(answer) > TELEGRAM_LIMIT:
        answer = answer[:TELEGRAM_LIMIT]

    history.append({"role": "assistant", "content": answer})

    await message.answer(
        answer,
        reply_markup=get_inline_keyboard()
    )

# =========================
# Запуск
# =========================
ADMIN_ID = 8502393010 # сюда вставь свой Telegram ID


@dp.message(Command("admin"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    total, new_today, active_24h, total_messages = get_stats()

    text = (
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"🆕 Новых сегодня: {new_today}\n"
        f"🟢 Активных за 24ч: {active_24h}\n"
        f"💬 Всего сообщений: {total_messages}"
    )

    await message.answer(text)

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())