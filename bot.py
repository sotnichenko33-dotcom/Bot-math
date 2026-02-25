from aiogram import Bot, Dispatcher
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import asyncio

BOT_TOKEN = "8733324125:AAFRO1dGo891edYxWlI5nBvx7rl2MB6HZNg"
OPENAI_API_KEY = "proj-6Dyk5QLZ6Odf57NRXxnsh8BD8IfcQ3717yzeT9m8n-UGcPymAO46SHIfyCRzDYSxrdpFOS3uXuT3BlbkFJJc6MCeZi-_aqdjE5uQrsLputQ0TcS0XDlZnnIJTOCcuE9uBWtN8hkmpahciD0JtSjTrgYAHygA"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Я бот, который решает задачи по математике.\n"
        "Просто отправь мне задачу текстом 🙂"
    )


@dp.message()
async def solve_math(message: types.Message):
    try:
        response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Ты опытный преподаватель математики. Решай задачу подробно."},
        {"role": "user", "content": message.text}
    ]
)
        answer = response.choices[0].message.content
        await message.answer(answer)

    except Exception as e:
        await message.answer("❌ Произошла ошибка при решении задачи.")
        print("ERROR:", e)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())