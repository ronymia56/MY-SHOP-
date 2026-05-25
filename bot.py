import os
from aiogram import Bot, Dispatcher, executor, types
from flask import Flask
from threading import Thread

# আপনার টোকেন এখানে বসান
API_TOKEN = '8959503198:AAGXpkVYMqKn0n1NDh9c3HKgmHJI8PY4y0E'

# বট এবং ডিসপ্যাচার সেটআপ
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ফ্লাস্ক সার্ভার (এটি রেন্ডারকে সচল রাখবে)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# বটের কমান্ড
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("স্বাগতম! আপনার বট সচল হয়েছে।")

if __name__ == '__main__':
    # ফ্লাস্ক সার্ভার আলাদা থ্রেডে চালু করা
    Thread(target=run_flask).start()
    # বট চালু করা
    executor.start_polling(dp, skip_updates=True)

from flask import Flask
from threading import Thread
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    Thread(target=run).start()
