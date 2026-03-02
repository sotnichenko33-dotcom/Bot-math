import asyncio
import os
import logging
from typing import Dict, List

import aiohttp
import base64
from aiogram.types import Message
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from database import (
    init_db,
    add_or_update_user,
    get_stats,
    add_message,
    get_user_history,
    clear_history
)

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
    
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! 🤖 Я AI-бот с памятью.\n\n"
        "Используй кнопки под ответом 👇"
    )

@dp.message(Command("reset"))
async def reset_handler(message: types.Message):
    user_id = message.from_user.id
    clear_history(user_id)
    await message.answer("✅ Память очищена!")

@dp.callback_query(F.data == "clear")
async def clear_memory(callback: types.CallbackQuery):
    clear_history(callback.from_user.id)
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

@dp.message(F.photo)
async def handle_photo(message: Message):
    try:
        await message.answer("📸 Анализирую фото...")

        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_path = file.file_path

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                image_bytes = await resp.read()

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

         # 👇 ВАЖНО: напиши сюда свою модель
        model_name = "openai/gpt-4o"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model_name,
            "messages": [
                 {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Что изображено на фото?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            ) as resp:
                result = await resp.json()

        print(result)  # временно для логов

        if "choices" in result:
            answer = result["choices"][0]["message"]["content"]
        else:
        answer = f"Ошибка API: {result}"

        await message.answer(answer)

    except Exception as e:
        await message.answer(f"❌ Ошибка:\n{e}")

@dp.message(F.text)
async def ai_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    add_or_update_user(user_id, username)

    if not message.text:
        await message.answer("Я понимаю только текст 🤔")
        return

    # 🔥 сохраняем сообщение пользователя в БД
    add_message(user_id, "user", message.text)

    await process_ai(message, user_id)

# =========================
# Core logic
# =========================
async def process_ai(message: types.Message, user_id: int):
    await bot.send_chat_action(message.chat.id, "typing")

    # 🔥 берём историю из БД
    history = get_user_history(user_id, limit=MAX_HISTORY)

    answer = await request_model(history)

    if not answer:
        await message.answer("⚠️ Все модели недоступны.")
        return

    if len(answer) > TELEGRAM_LIMIT:
        answer = answer[:TELEGRAM_LIMIT]

    # 🔥 сохраняем ответ модели в БД
    add_message(user_id, "assistant", answer)

    await message.answer(
        answer,
        reply_markup=get_inline_keyboard()
    )

# =========================
# Запуск
# =========================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())