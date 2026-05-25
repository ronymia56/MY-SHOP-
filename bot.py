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

# ================= CONFIG =================
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

# ================= DATABASE & EXCEL =================
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
def add_balance(user_id, amount):
    uid = str(user_id)
    db[uid] = get_balance(uid) + int(amount)
    save_db(db)
def get_price(category): return int(db.get("settings", {}).get(f"price_{category}", 15))
def set_price(category, price):
    if "settings" not in db: db["settings"] = {}
    db["settings"][f"price_{category}"] = int(price)
    save_db(db)

def read_excel(file_name):
    if not os.path.exists(file_name): return []
    wb = load_workbook(file_name)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        if row and any(row): rows.append(list(row))
    return rows

# ================= STATES =================
class BuyState(StatesGroup): category = State(); amount = State()
class DepositState(StatesGroup): method = State(); amount = State(); txnid = State()
class AdminState(StatesGroup): upload_cat = State(); price_cat = State(); new_price = State()

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("স্বাগতম! নিচে আপনার বাটনগুলো দেখুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ BUY FACEBOOK ID", callback_data="products")],
        [InlineKeyboardButton(text="💳 Deposit", callback_data="deposit"), InlineKeyboardButton(text="💰 My Balance", callback_data="balance")],
        [InlineKeyboardButton(text="🧑‍💻 Live Support", url="https://t.me/mohammadrony56"), InlineKeyboardButton(text="👨‍💻 Admin", callback_data="admin")]
    ]))

@dp.callback_query()
async def callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    user_id = str(call.from_user.id)
    await call.answer()
    
    if data == "balance":
        await call.message.edit_text(f"💰 আপনার ব্যালেন্স: `{get_balance(user_id)} BDT`", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back")]]), parse_mode="Markdown")
    elif data == "products":
        await call.message.edit_text("🛒 ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Buy 1000x", callback_data="buy_1000x")],
            [InlineKeyboardButton(text="Buy 61x", callback_data="buy_61x")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]))
    elif data == "deposit":
        await call.message.edit_text("💳 ডিপোজিট মেথড সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="bKash", callback_data="dep_bkash"), InlineKeyboardButton(text="Nagad", callback_data="dep_nagad")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]))
    elif data == "admin":
        if call.from_user.id == ADMIN_ID: await call.message.edit_text("⚙️ এডমিন প্যানেল", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📂 Upload Stock", callback_data="admin_upload")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]))
    elif data == "back":
        await call.message.edit_text("স্বাগতম!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ BUY FACEBOOK ID", callback_data="products")],
            [InlineKeyboardButton(text="💳 Deposit", callback_data="deposit"), InlineKeyboardButton(text="💰 My Balance", callback_data="balance")],
            [InlineKeyboardButton(text="🧑‍💻 Live Support", url="https://t.me/mohammadrony56"), InlineKeyboardButton(text="👨‍💻 Admin", callback_data="admin")]
        ]))

# ================= RUN BOT =================
async def main():
    Thread(target=run_flask).start()
    print("🚀 Bot is live on Render!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
