import logging
import io

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

# ================== НАСТРОЙКИ ==================

API_TOKEN = "ТВОЙ_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================== ПЕРЕМЕННЫЕ ==================

user_mode = {}  # режим пользователя: math / graph

# ================== КНОПКИ ==================

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("▲ Математика"),
    KeyboardButton("📊 График")
)

# ================== ГРАФИК ==================

def build_plot(expr: str):
    x = sp.symbols('x')
    y = sp.sympify(expr)

    f = sp.lambdify(x, y, "numpy")
    xs = np.linspace(-10, 10, 400)
    ys = f(xs)

    plt.figure()
    plt.plot(xs, ys)
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return buf

# ================== /start ==================

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "👋 Привет!\n\n"
        "Я умный математический бот 🤖\n"
        "Выбери режим ниже 👇",
        reply_markup=keyboard
    )

# ================== РЕЖИМ МАТЕМАТИКА ==================

@dp.message_handler(lambda msg: msg.text == "▲ Математика")
async def math_mode(msg: types.Message):
    user_mode[msg.from_user.id] = "math"
    await msg.answer(
        "📐 *Режим Математика включён!*\n\n"
        "Примеры:\n"
        "`2+2`\n"
        "`10000*2`\n"
        "`(5+3)*4`",
        parse_mode="Markdown"
    )

# ================== РЕЖИМ ГРАФИК ==================

@dp.message_handler(lambda msg: msg.text == "📊 График")
async def graph_mode(msg: types.Message):
    user_mode[msg.from_user.id] = "graph"
    await msg.answer(
        "📊 *Режим График включён!*\n\n"
        "Введи выражение с `x`\n"
        "Пример:\n"
        "`x**2 + 3*x`",
        parse_mode="Markdown"
    )

# ================== ОБРАБОТКА СООБЩЕНИЙ ==================

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(msg: types.Message):
    mode = user_mode.get(msg.from_user.id)

    # ---------- МАТЕМАТИКА ----------
    if mode == "math":
        try:
            result = sp.sympify(msg.text)
            await msg.answer(f"✅ Ответ:\n`{result}`", parse_mode="Markdown")
        except:
            await msg.answer("❌ Не могу решить этот пример")
        return

    # ---------- ГРАФИК ----------
    if mode == "graph":
        try:
            buf = build_plot(msg.text)
            await msg.answer_photo(buf)
        except:
            await msg.answer("❌ Ошибка в выражении")
        return

    await msg.answer("ℹ️ Сначала выбери режим кнопкой 👇", reply_markup=keyboard)

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)