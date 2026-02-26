import os
import io
import openai
import sympy as sp
import matplotlib.pyplot as plt

from aiogram import Bot, Dispatcher, executor, types
from duckduckgo_search import DDGS
from PIL import Image
import pytesseract

# ================== НАСТРОЙКИ ==================
openai.api_key = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

x = sp.symbols('x')

# ================== ИИ ОТВЕТ ==================
async def ai_answer(prompt: str):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты умный учебный помощник. Объясняй понятно и по шагам."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ================== МАТЕМАТИКА ==================
def solve_math(expr: str):
    if "=" in expr:
        left, right = expr.split("=")
        eq = sp.Eq(sp.sympify(left), sp.sympify(right))
        steps = sp.solve(eq, x, dict=True)
        return f"Решение:\n{steps}"
    else:
        result = sp.sympify(expr)
        return f"Ответ: {result}"

# ================== ГРАФИК ==================
def build_plot(expr: str):
    y = sp.sympify(expr)
    xs = range(-10, 11)
    ys = [y.subs(x, i) for i in xs]

    plt.figure()
    plt.plot(xs, ys)
    plt.grid()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# ================== ИНТЕРНЕТ ==================
def internet_search(query: str):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
        text = ""
        for r in results:
            text += f"• {r['title']}\n{r['body']}\n\n"
        return text or "Ничего не найдено"

# ================== ФОТО ==================
def photo_to_text(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image, lang="rus+eng")

# ================== КНОПКИ ==================
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add("📐 Математика", "📷 Фото-задача")
keyboard.add("🌐 Интернет", "📊 График")
keyboard.add("🤖 Спросить ИИ")

# ================== СТАРТ ==================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "👋 Я умный ИИ-бот\n\n"
        "Я умею:\n"
        "• решать задачи\n"
        "• объяснять по шагам\n"
        "• решать по фото\n"
        "• строить графики\n"
        "• искать в интернете",
        reply_markup=keyboard
    )

# ================== ТЕКСТ ==================
@dp.message_handler(content_types=types.ContentType.TEXT)
async def text_handler(msg: types.Message):
    text = msg.text

    try:
        if text.startswith(("x", "2", "3", "4", "5")):
            answer = solve_math(text)
            await msg.answer(answer)
            return
    except:
        pass

    if "график" in text.lower():
        expr = text.replace("график", "").strip()
        plot = build_plot(expr)
        await msg.answer_photo(plot)
        return

    if text.lower().startswith("найди"):
        result = internet_search(text)
        await msg.answer(result)
        return

    ai = await ai_answer(text)
    await msg.answer(ai)

# ================== ФОТО ==================
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def photo_handler(msg: types.Message):
    photo = msg.photo[-1]
    file = await bot.get_file(photo.file_id)
    image_bytes = await bot.download_file(file.file_path)

    text = photo_to_text(image_bytes.read())
    answer = await ai_answer(f"Реши и объясни по шагам:\n{text}")

    await msg.answer(f"📷 Распознанный текст:\n{text}")
    await msg.answer(answer)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)