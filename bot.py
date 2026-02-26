., [26.02.2026 15:03]
import os
import logging
import base64
import io

import matplotlib.pyplot as plt
import sympy as sp
import numpy as np

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
from duckduckgo_search import DDGS

# ================== НАСТРОЙКИ ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("❌ BOT_TOKEN или OPENAI_API_KEY не заданы")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

# ================== ПАМЯТЬ ==================

user_memory = {}
user_mode = {}
MAX_MEMORY = 6

# ================== КНОПКИ ==================

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("📖 Решить по шагам"),
    KeyboardButton("⚡ Кратко")
)
keyboard.add(
    KeyboardButton("🔄 Сбросить диалог")
)

# ================== ИНТЕРНЕТ ==================

def web_search(query: str) -> str:
    with DDGS() as ddgs:
        results = [
            f"- {r['title']}: {r['body']}"
            for r in ddgs.text(query, max_results=3)
        ]
    return "\n".join(results)

# ================== ГРАФИК ==================

def looks_like_graph_request(text: str) -> bool:
    triggers = ["y =", "f(x)", "график", "построй", "зависимость"]
    text = text.lower()
    return any(t in text for t in triggers)

def build_graph(expr_text: str):
    x = sp.symbols("x")
    expr_text = expr_text.replace("^", "**")

    if "=" in expr_text:
        expr_text = expr_text.split("=")[1]

    expr = sp.sympify(expr_text)
    func = sp.lambdify(x, expr, "numpy")

    xs = np.linspace(-10, 10, 400)
    ys = func(xs)

    plt.figure()
    plt.plot(xs, ys)
    plt.axhline(0)
    plt.axvline(0)
    plt.grid()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf

# ================== ИИ (ТЕКСТ) ==================

def ai_answer(user_id: int, text: str) -> str:
    mode = user_mode.get(user_id, "steps")
    web_info = web_search(text)
    memory = user_memory.get(user_id, [])

    system = "Ты умный ИИ-репетитор."
    if mode == "steps":
        system += " Решай ПО ШАГАМ."
    else:
        system += " Отвечай КРАТКО."

    messages = [{"role": "system", "content": system}]
    messages += memory
    messages.append({
        "role": "user",
        "content": f"Интернет:\n{web_info}\n\nВопрос:\n{text}"
    })

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
    )

    answer = resp.choices[0].message.content.strip()

    memory.append({"role": "user", "content": text})
    memory.append({"role": "assistant", "content": answer})
    user_memory[user_id] = memory[-MAX_MEMORY:]

    return answer

# ================== HANDLERS ==================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_mode[message.from_user.id] = "steps"
    user_memory[message.from_user.id] = []
    await message.answer(
        "👋 Я ИИ-репетитор с графиками 📊\n\n"
        "Я умею:\n"
        "• решать задачи\n"
        "• строить графики\n"
        "• объяснять по шагам\n"
        "• работать с фото\n\n"
        "Напиши задачу 👇",
        reply_markup=keyboard
    )

@dp.message_handler(lambda m: m.text == "📖 Решить по шагам")
async def mode_steps(message: types.Message):
    user_mode[message.from_user.id] = "steps"
    await message.answer("📖 Режим: по шагам")

@dp.message_handler(lambda m: m.text == "⚡ Кратко")
async def mode_short(message: types.Message):
    user_mode[message.from_user.id] = "short"
    await message.answer("⚡ Режим: кратко")

@dp.message_handler(lambda m: m.text == "🔄 Сбросить диалог")
async def reset(message: types.Message):
    user_memory[message.from_user.id] = []
    await message.answer("🔄 Диалог очищен")

@dp.message_handler(content_types=types.ContentType.TEXT)

., [26.02.2026 15:03]
async def handle_text(message: types.Message):
    text = message.text

    if looks_like_graph_request(text):
        try:
            graph = build_graph(text)
            await message.answer_photo(
                photo=graph,
                caption="📊 График функции"
            )
        except Exception:
            await message.answer("❌ Не удалось построить график")

    await message.answer("🧠 Думаю...")
    answer = ai_answer(message.from_user.id, text)
    await message.answer(answer)

# ================== START ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)