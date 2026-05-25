import asyncio
import os
import json
import logging
from threading import Thread
from flask import Flask

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from openpyxl import load_workbook, Workbook

TOKEN = "8959503198:AAGXpkVYMqKn0n1NDh9c3HKgmHJI8PY4y0E"
ADMIN_ID = 2106634618

# RENDER WEB SERVER
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# DB & EXCEL (আগের মতোই)
DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE): return {"settings": {"price_1000x": 15, "price_61x": 12}}
    with open(DB_FILE, "r") as f:
        try: return json.load(f)
        except: return {"settings": {"price_1000x": 15, "price_61x": 12}}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=2)
db = load_db()

def get_balance(user_id): return int(db.get(str(user_id), 0))
def get_price(category): return int(db.get("settings", {}).get(f"price_{category}", 15))

# STATES
class BuyState(StatesGroup): category = State(); amount = State()
class DepositState(StatesGroup): method = State(); amount = State(); txnid = State()
class AdminState(StatesGroup): upload_cat = State(); price_cat = State(); new_price = State()

# CALLBACK HANDLER (এখানেই বাটন কাজ করবে)
@dp.callback_query()
async def callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    user_id = str(call.from_user.id)
    await call.answer()

    # মেনু বাটন ক্লিক করলে আগের স্টেট ডিলিট করা নিরাপদ
    if data in ["products", "deposit", "balance", "admin", "back"]:
        await state.clear()
        
    if data == "balance":
        await call.message.edit_text(f"💰 ব্যালেন্স: `{get_balance(user_id)} BDT`", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back")]]), parse_mode="Markdown")
    
    elif data == "products":
        await call.message.edit_text("🛒 ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Buy 1000x", callback_data="buy_1000x")],
            [InlineKeyboardButton(text="Buy 61x", callback_data="buy_61x")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]))

    elif data.startswith("buy_"):
        cat = data.split("_")[1]
        await state.update_data(category=cat)
        await state.set_state(BuyState.amount)
        await call.message.answer(f"🔢 কত পিস {cat} আইডি কিনবেন? সংখ্যায় লিখুন:")

    elif data == "deposit":
        await call.message.edit_text("💳 মেথড সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="bKash", callback_data="dep_bkash"), InlineKeyboardButton(text="Nagad", callback_data="dep_nagad")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]))

    elif data.startswith("dep_"):
        method = "bKash" if "bkash" in data else "Nagad"
        await state.update_data(method=method)
        await state.set_state(DepositState.amount)
        await call.message.answer(f"✅ {method} সিলেক্ট করেছেন। এখন কত টাকা পাঠিয়েছেন তার পরিমাণ লিখুন:")

    elif data == "back":
        await call.message.edit_text("স্বাগতম!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ BUY FACEBOOK ID", callback_data="products")],
            [InlineKeyboardButton(text="💳 Deposit", callback_data="deposit"), InlineKeyboardButton(text="💰 My Balance", callback_data="balance")],
            [InlineKeyboardButton(text="🧑‍💻 Live Support", url="https://t.me/mohammadrony56"), InlineKeyboardButton(text="👨‍💻 Admin", callback_data="admin")]
        ]))

# RUN
async def main():
    Thread(target=run_flask).start()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
