import asyncio
import os
import json
import threading
from flask import Flask

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from openpyxl import load_workbook, Workbook

# ================= RENDER SERVER (Render এ বটের জন্য এটি আবশ্যিক) =================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# ================= CONFIG =================
TOKEN = "8959503198:AAGXpkVYMqKn0n1NDh9c3HKgmHJI8PY4y0E"
ADMIN_ID = 2106634618

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= DATABASE =================
DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: 
            json.dump({"settings": {"price_1000x": 15, "price_61x": 12}}, f)
        return {"settings": {"price_1000x": 15, "price_61x": 12}}
    with open(DB_FILE, "r") as f:
        try: 
            data = json.load(f)
            if "settings" not in data: data["settings"] = {"price_1000x": 15, "price_61x": 12}
            return data
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
class BuyState(StatesGroup):
    category = State(); amount = State()
class DepositState(StatesGroup):
    method = State(); amount = State(); txnid = State()
class AdminState(StatesGroup):
    upload_cat = State(); price_cat = State(); new_price = State()

# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛍️ BUY FACEBOOK ID", callback_data="products")], [InlineKeyboardButton(text="💳 Deposit", callback_data="deposit"), InlineKeyboardButton(text="💰 My Balance", callback_data="balance")], [InlineKeyboardButton(text="🧑‍💻 Live Support", url="https://t.me/mohammadrony56"), InlineKeyboardButton(text="👨‍💻 Admin", callback_data="admin")]])

def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📂 Upload Stock", callback_data="admin_upload")], [InlineKeyboardButton(text="💰 Set ID Price", callback_data="admin_price")], [InlineKeyboardButton(text="💡 Balance Guide", callback_data="balhelp")], [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back")]])

def deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 bKash", callback_data="dep_bkash"), InlineKeyboardButton(text="📱 Nagad", callback_data="dep_nagad")], [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]])

def back_btn():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]])

def get_dashboard_text(name, user_id):
    return f"▬▬▬ ✦ PREMIUM ID STORE ✦ ▬▬▬\n\n👤 **User:** {name}\n🆔 **User ID:** `{user_id}`\n\n👋 **আমাদের বটে আপনাকে স্বাগতম!**\n📥 স্টক শেষ হওয়ার আগেই আইডি সংগ্রহ করুন 🎯!"

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
        await message.answer(f"✅ **Manual Success!** `{amount} BDT` added to `{uid}`.", parse_mode="Markdown")
    except: await message.answer("❌ Use: `/addbal user_id amount`", parse_mode="Markdown")

@dp.message(lambda m: m.document)
async def upload_stock(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    user_data = await state.get_data()
    cat = user_data.get("upload_cat")
    if not cat: return
    file_name = "1000x_pc.xlsx" if cat == "1000x" else "61x_pc.xlsx"
    await bot.download(message.document, destination=file_name)
    await message.answer(f"🚀 **{cat} Stock Updated!**", reply_markup=admin_panel())
    await state.clear()

@dp.callback_query()
async def callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    user_id = str(call.from_user.id)
    name = call.from_user.full_name
    await call.answer()
    if data == "balance":
        await call.message.edit_text(f"💰 Balance: `{get_balance(user_id)} BDT`", reply_markup=back_btn(), parse_mode="Markdown")
    elif data == "products":
        await call.message.edit_text("🛒 ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Buy 1000x", callback_data="buy_1000x")], [InlineKeyboardButton(text="Buy 61x", callback_data="buy_61x")], [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]))
    elif data.startswith("buy_"):
        cat = data.split("_")[1]
        await state.update_data(category=cat); await state.set_state(BuyState.amount)
        await call.message.answer(f"🔢 কত পিস {cat} আইডি কিনবেন?")
    elif data == "deposit":
        await call.message.edit_text("💳 মেথড সিলেক্ট করুন:", reply_markup=deposit_menu())
    elif data.startswith("dep_"):
        method = "bKash" if "bkash" in data else "Nagad"
        await state.update_data(method=method); await state.set_state(DepositState.amount)
        await call.message.edit_text(f"📱 {method} নাম্বারে পেমেন্ট করে কত টাকা পাঠিয়েছেন লিখে পাঠান:")
    elif data == "admin":
        if call.from_user.id == ADMIN_ID: await call.message.edit_text("⚙️ এডমিন প্যানেল", reply_markup=admin_panel())
    elif data == "admin_upload":
        await call.message.edit_text("📂 ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="1000x", callback_data="upcat_1000x")], [InlineKeyboardButton(text="61x", callback_data="upcat_61x")]]))
    elif data.startswith("upcat_"):
        cat = data.split("_")[1]; await state.update_data(upload_cat=cat); await state.set_state(AdminState.upload_cat)
        await call.message.edit_text(f"📁 Please send the .xlsx file for {cat}")
    elif data == "back":
        await state.clear(); await call.message.edit_text(get_dashboard_text(name, user_id), reply_markup=main_menu(), parse_mode="Markdown")
    elif data.startswith("approve_"):
        _, target_uid, amount = data.split("_")
        add_balance(target_uid, amount)
        await call.message.edit_text(f"✅ Approved: `{target_uid}` got `{amount} BDT`")

# ================= RUN BOT =================
async def main():
    # রেন্ডার সার্ভার চালু করার জন্য থ্রেড
    threading.Thread(target=run_flask).start()
    print("🚀 Shop Bot is running with Render Support!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
