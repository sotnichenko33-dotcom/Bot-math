import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import openai

# =========================
# Загрузка переменных
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Хранилище сессий
user_sessions = {}

# =========================
# Клавиатура
# =========================

def get_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧹 Очистить диалог",
                    callback_data="clear_history"
                )
            ]
        ]
    )

# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_sessions[message.from_user.id] = []
    await message.answer(
        "Привет 👋 Я ChatGPT-бот.\n\nНапиши мне что-нибудь!",
        reply_markup=get_inline_keyboard()
    )

# =========================
# Очистка истории
# =========================

@dp.callback_query(F.data == "clear_history")
async def clear_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_sessions[user_id] = []

    await callback.message.answer("🧹 История очищена!")
    await callback.answer()

# =========================
# Основной обработчик сообщений
# =========================

@dp.message()
async def chat_handler(message: Message):
    user_id = message.from_user.id
    user_text = message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = []

    user_sessions[user_id].append({
        "role": "user",
        "content": user_text
    })

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_sessions[user_id]
        )

        answer = response["choices"][0]["message"]["content"]

        user_sessions[user_id].append({
            "role": "assistant",
            "content": answer
        })

        await message.answer(
            answer,
            reply_markup=get_inline_keyboard()
        )

    except Exception as e:
        print("Ошибка:", e)
        await message.answer("⚠️ Ошибка при обращении к OpenAI.")

# =========================
# Запуск
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
asyncio.run(main())