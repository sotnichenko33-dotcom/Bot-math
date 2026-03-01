import asyncio
import os
import requests

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from dotenv import load_dotenv

# =========================
# Загрузка переменных
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# =========================
# Инициализация
# =========================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# Память
# =========================
user_sessions = {}

# =========================
# Inline клавиатура
# =========================
def get_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Перегенерировать",
                    callback_data="regenerate"
                ),
                InlineKeyboardButton(
                    text="🧹 Очистить память",
                    callback_data="clear"
                )
            ]
        ]
    )

# =========================
# /start
# =========================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! 🤖 Я AI-бот с памятью.\n\n"
        "Я запоминаю контекст.\n"
        "Используй кнопки под ответом 👇"
    )

# =========================
# Очистка памяти
# =========================
@dp.callback_query(F.data == "clear")
async def clear_memory(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id in user_sessions:
        del user_sessions[user_id]

    await callback.message.answer("✅ Память очищена!")
    await callback.answer()

# =========================
# Перегенерация
# =========================
@dp.callback_query(F.data == "regenerate")
async def regenerate_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_sessions or len(user_sessions[user_id]) < 2:
        await callback.answer("Нечего перегенерировать 🙂", show_alert=True)
        return

    # Удаляем последний ответ бота
    if user_sessions[user_id][-1]["role"] == "assistant":
        user_sessions[user_id].pop()

    await callback.answer()
    await generate_ai_response(callback.message, user_id)

# =========================
# Обработка сообщений
# =========================
@dp.message()
async def ai_handler(message: types.Message):

    if not message.text:
        await message.answer("Я понимаю только текст 🙂")
        return

    user_id = message.from_user.id

    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "Ты полезный AI-помощник."}
        ]

    user_sessions[user_id].append({
        "role": "user",
        "content": message.text
    })

    user_sessions[user_id] = user_sessions[user_id][-10:]

    await generate_ai_response(message, user_id)

# =========================
# Генерация ответа
# =========================
async def generate_ai_response(message, user_id):

    await bot.send_chat_action(message.chat.id, "typing")

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

    for model in models:
        try:
            data = {
                "model": model,
                "messages": user_sessions[user_id]
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            result = response.json()

            if "choices" in result:
                answer = result["choices"][0]["message"]["content"]

                user_sessions[user_id].append({
                    "role": "assistant",
                    "content": answer
                })

                await message.


answer(
                    answer,
                    reply_markup=get_inline_keyboard()
                )
                return

        except Exception as e:
            print("Ошибка:", e)

    await message.answer("⚠️ Все модели недоступны.")

# =========================
# Запуск
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())