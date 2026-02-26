import os
import logging
from aiogram import Bot, Dispatcher, executor, types

from sympy import sympify, solve
from sympy.core.sympify import SympifyError
from sympy.abc import x

# 🔍 ВРЕМЕННАЯ ДИАГНОСТИКА (можно удалить после проверки)
print("BOT_TOKEN =", repr(os.getenv("BOT_TOKEN")))
print("OPENAI_API_KEY =", repr(os.getenv("OPENAI_API_KEY")))

# =========================
# ЛОГИ
# =========================
logging.basicConfig(level=logging.INFO)

# =========================
# ПЕРЕМЕННЫЕ СРЕДЫ
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =========================
# ПРОВЕРКИ (очень важно)
# =========================
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден в переменных среды")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY не найден в переменных среды")

# =========================
# BOT / DISPATCHER
# =========================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# =========================
# ХЭНДЛЕРЫ
# =========================
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Привет!\n\n"
        "🤖 Я бот-математик\n"
        "✍️ Напиши пример, и я его решу"
    )


@dp.message_handler(lambda message: message.text and not message.text.startswith("/"))
async def math_handler(message: types.Message):
    try:
        text = message.text.replace(" ", "").replace(",", ".")

        # ===== УРАВНЕНИЕ =====
        if "=" in text:
            left, right = text.split("=")
            left_expr = sympify(left)
            right_expr = sympify(right)

            equation = left_expr - right_expr
            solution = solve(equation, x)

            steps = (
                "🧮 *Решение по шагам:*\n\n"
                f"1️⃣ Исходное уравнение:\n{left} = {right}\n\n"
                f"2️⃣ Переносим всё в одну сторону:\n{equation} = 0\n\n"
                f"3️⃣ Решаем уравнение:\n{x} = {solution}"
            )

            await message.answer(steps, parse_mode="Markdown")

        # ===== ВЫРАЖЕНИЕ =====
        else:
            expr = sympify(text)

            simplified = simplify(expr)
            result = expr.evalf()

            steps = (
                "🧮 *Решение по шагам:*\n\n"
                f"1️⃣ Исходное выражение:\n{text}\n\n"
                f"2️⃣ Упрощаем:\n{simplified}\n\n"
                f"3️⃣ Ответ:\n{result}"
            )

            await message.answer(steps, parse_mode="Markdown")

    except Exception as e:
        await message.answer(
            "❌ Ошибка\n\n"
            "Проверь выражение.\n"
            "Примеры:\n"
            "2+2*5\n"
            "2*x+4=10"
        )

# =========================
# ЗАПУСК
# =========================
if __name__ == "__main__":
    logging.info("🚀 Бот запускается...")
    executor.start_polling(dp, skip_updates=True)