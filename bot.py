import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я ChatGPT-бот 🤖 Напиши мне что-нибудь!")


@dp.message()
async def ai_handler(message: types.Message):
    user_text = message.text

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты полезный помощник."},
            {"role": "user", "content": user_text}
        ]
    )

    answer = response.choices[0].message.content
    await message.answer(answer)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())