import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from flask import Flask
from threading import Thread

API_TOKEN = '8959503198:AAGXpkVYMqKn0n1NDh9c3HKgmHJI8PY4y0E' # আপনার টোকেন এখানে দিন

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!"

def run_flask():
    # রেন্ডার থেকে পাওয়া পোর্ট ব্যবহার করুন
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("বট সচল হয়েছে!")

if __name__ == '__main__':
    # Flask ওয়েব সার্ভার চালু করা
    Thread(target=run_flask).start()
    # বট পোলিং চালু করা
    executor.start_polling(dp, skip_updates=True)
