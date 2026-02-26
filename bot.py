import os
import logging
from aiogram import Bot, Dispatcher, executor, types

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


@dp.message_handler()
async def math_handler(message: types.Message):
    try:
        expr = message.text.replace("^", "**")
        result = eval(expr)
        await message.answer(f"✅ Результат: {result}")
    except:
        await message.answer(
            "❌ Я могу решать только математические выражения.\n"
            "Пример: 2+2*(5-1)"
        )

# =========================
# ЗАПУСК
# =========================
if __name__ == "__main__":
    logging.info("🚀 Бот запускается...")
    executor.start_polling(dp, skip_updates=True)