import asyncio
import os
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

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
    user_text = message.text

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    models = [
        "stepfun/step-3.5-flash:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3-8b-instruct:free",
        "google/gemma-7b-it:free",
        "nousresearch/nous-hermes-2-mistral-7b-dpo:free"
    ]

    for model in models:
        try:
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": user_text}
                ]
            }

            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if "choices" in result:
                answer = result["choices"][0]["message"]["content"]
                await message.answer(answer)
                return

            # если ошибка 401 или 402 — дальше нет смысла
            if result.get("error", {}).get("code") in [401, 402]:
                break

        except Exception as e:
            print("Error:", model, e)

    await message.answer("⚠️ Все модели сейчас недоступны. Попробуй позже.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())