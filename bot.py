import asyncio
import os
import json
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from openpyxl import load_workbook, Workbook
from flask import Flask
from threading import Thread

# ================= CONFIG =================
TOKEN = "8959503198:AAGXpkVYMqKn0n1NDh9c3HKgmHJI8PY4y0E"
ADMIN_ID = 2106634618 

# RENDER WEB SERVER (এটি বটকে সচল রাখবে)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# BOT SETUP
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================
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

# ================= EXCEL =================
def read_excel(file_name):
    if not os.path.exists(file_name): return []
    wb = load_workbook(file_name)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        if row and any(row): rows.append(list(row))
    return rows
def write_excel(file_name, data):
    wb = Workbook()
    ws = wb.active
    for row in data: ws.append(row)
    wb.save(file_name)

# ================= STATES =================
class BuyState(StatesGroup): category = State(); amount = State()
class DepositState(StatesGroup): method = State(); amount = State(); txnid = State()
class AdminState(StatesGroup): upload_cat = State(); price_cat = State(); new_price = State()

# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ BUY FACEBOOK ID", callback_data="products")],
        [InlineKeyboardButton(text="💳 Deposit", callback_data="deposit"), InlineKeyboardButton(text="💰 My Balance", callback_data="balance")],
        [InlineKeyboardButton(text="🧑‍💻 Live Support", url="https://t.me/mohammadrony56"), InlineKeyboardButton(text="👨‍💻 Admin", callback_data="admin")]
    ])

def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Upload Stock", callback_data="admin_upload")],
        [InlineKeyboardButton(text="💰 Set ID Price", callback_data="admin_price")],
        [InlineKeyboardButton(text="💡 Balance Guide", callback_data="balhelp")],
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back")]
    ])

def deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 bKash", callback_data="dep_bkash"), InlineKeyboardButton(text="📱 Nagad", callback_data="dep_nagad")],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]
    ])

def back_btn():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]])

def get_dashboard_text(name, user_id):
    return f"▬▬▬ ✦ PREMIUM ID STORE ✦ ▬▬▬\n\n👤 User: {name}\n🆔 User ID: `{user_id}`\n\nস্বাগতম! স্টক শেষ হওয়ার আগেই আইডি সংগ্রহ করুন!"

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(get_dashboard_text(message.from_user.full_name, message.from_user.id), reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(Command("addbal"))
async def addbal(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = message.text.split()
        add_balance(uid, int(amount))
        await message.answer(f"✅ Added {amount} to {uid}")
    except: await message.answer("❌ Use: /addbal user_id amount")

@dp.callback_query()
async def callback(call: types.CallbackQuery, state: FSMContext):
    # আপনার আগের কলব্যাক লজিক এখানে হুবহু আছে
    await call.answer()
    # (আপনার আগের কোড থেকে বাকি সব হ্যান্ডলার এখানে বসান)
    if call.data == "back":
        await state.clear()
        await call.message.edit_text(get_dashboard_text(call.from_user.full_name, call.from_user.id), reply_markup=main_menu(), parse_mode="Markdown")

# ================= RUN BOT =================
async def main():
    Thread(target=run_flask).start() # এটি রেন্ডার পোর্টের জন্য
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
