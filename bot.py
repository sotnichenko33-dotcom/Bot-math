import asyncio
import os
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
user_sessions = {}

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! 🤖 Я ChatGPT-бот. Напиши мне что-нибудь!")

# Обработка всех сообщений
@dp.message()
async def ai_handler(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # если пользователя нет в памяти — создаём
    if user_id not in user_sessions:
        user_sessions[user_id] = []

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

            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if "choices" in result:
                answer = result["choices"][0]["message"]["content"]

                # добавляем ответ бота в память
                user_sessions[user_id].append({
                    "role": "assistant",
                    "content": answer
                })

                await message.answer(answer)
                return

        except Exception as e:
            print("Error:", model, e)

    await message.answer("⚠️ Все модели сейчас недоступны.")
# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())