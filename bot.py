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
        text = message.text.replace("^", "**")

        # если это уравнение
        if "=" in text:
            left, right = text.split("=", 1)
            expr = sympify(left) - sympify(right)
            result = solve(expr, x)

            if len(result) == 0:
                await message.answer("❌ Решений нет")
            else:
                await message.answer(f"✅ Решение:\n{result}")

        # если обычный пример
        else:
            result = sympify(text).doit()
            await message.answer(f"✅ Результат:\n{result}")

    except (SympifyError, ValueError):
        await message.answer(
            "❌ Я решаю только математические выражения и уравнения.\n\n"
            "Примеры:\n"
            "2+2*(5-1)\n"
            "x^2-4=0\n"
            "2*x+5=9"
        )

# =========================
# ЗАПУСК
# =========================
if __name__ == "__main__":
    logging.info("🚀 Бот запускается...")
    executor.start_polling(dp, skip_updates=True)