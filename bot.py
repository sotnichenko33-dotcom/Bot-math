import asyncio
import os
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
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
# Память пользователей
# =========================
user_sessions = {}

# =========================
# Клавиатура
# =========================
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧹 Очистить память")]
    ],
    resize_keyboard=True
)

# =========================
# Команда /start
# =========================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! 🤖 Я ChatGPT-бот с памятью.\n\n"
        "Я запоминаю последние сообщения в диалоге.\n"
        "Если нужно — нажми «Очистить память».",
        reply_markup=keyboard
    )

# =========================
# Очистка памяти
# =========================
@dp.message(lambda message: message.text == "🧹 Очистить память")
async def clear_memory(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_sessions:
        del user_sessions[user_id]

    await message.answer("✅ Память очищена!")

# =========================
# Обработка сообщений
# =========================
@dp.message()
async def ai_handler(message: types.Message):
    # защита от фото / стикеров
    if not message.text:
        await message.answer("Я пока понимаю только текстовые сообщения 🙂")
        return

    user_id = message.from_user.id
    user_text = message.text

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # создаём память, если её нет
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "Ты полезный и умный AI-помощник."}
        ]

    # добавляем сообщение пользователя
    user_sessions[user_id].append({
        "role": "user",
        "content": user_text
    })

    # ограничиваем память (последние 10 сообщений)
    user_sessions[user_id] = user_sessions[user_id][-10:]

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

                # сохраняем ответ бота в память
                user_sessions[user_id].append({
                    "role": "assistant",
                    "content": answer
                })

                await message.answer(answer)
                return

        except Exception as e:
            print("Ошибка модели:", model, e)

    await message.answer("⚠️ Все модели сейчас недоступны. Попробуй позже.")

# =========================
# Запуск
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())