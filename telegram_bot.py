# telegram_bot/telegram_bot.py
# aiogram-бот с командами: /start, /today, /tomorrow, /bible

import asyncio
from datetime import date, timedelta
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import httpx
import os

# --- Подключение через переменные среды ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# --- Команды бота ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот с планом чтения Библии.\n\n"
        "Доступные команды:\n"
        "/today — чтение на сегодня\n"
        "/tomorrow — чтение на завтра\n"
        "/bible — открыть любую главу Библии"
    )

@dp.message(Command("today"))
async def cmd_today(message: Message):
    await message.answer(await fetch_plan(date.today()))

@dp.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message):
    await message.answer(await fetch_plan(date.today() + timedelta(days=1)))

@dp.message(Command("bible"))
async def cmd_bible(message: Message):
    web_url = "https://ivanzakhvatkin.github.io/biblebot-webapp/"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📖 Открыть Библию", web_app=WebAppInfo(url=web_url)
            )]
        ]
    )
    await message.answer("Открой любую книгу и главу Библии:", reply_markup=keyboard)

# --- Получение плана чтения ---
async def fetch_plan(date_obj: date) -> str:
    date_str = date_obj.isoformat()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:8000/plan?date={date_str}")
            if response.status_code == 200:
                data = response.json()
                if data["readings"]:
                    keys_str = data["readings"][0]["keys"]
                    parts = [part.strip() for part in keys_str.split(";")]
                    links = "\n".join(
                        f'🔹 <a href="https://t.me/{BOT_USERNAME}/webapp?start={date_str}_{p.replace(" ", "_")}">{p}</a>'
                        for p in parts
                    )
                    label = "сегодня" if date_obj == date.today() else f"{date_str}"
                    return f"📖 План чтения на {label}\n{links}"
                else:
                    return f"На {date_str} нет плана чтения."
            else:
                return "Ошибка при получении данных."
    except Exception as e:
        return f"Ошибка подключения: {e}"

# --- Костыль для Render — имитация открытого порта ---
import threading
from fastapi import FastAPI
import uvicorn

fake_app = FastAPI()

@fake_app.get("/")
def read_root():
    return {"status": "I'm alive"}

def run_fake_server():
    uvicorn.run(fake_app, host="0.0.0.0", port=10000)

# --- Запуск ---
if __name__ == "__main__":
    threading.Thread(target=run_fake_server, daemon=True).start()
    asyncio.run(dp.start_polling(bot))
