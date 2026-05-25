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

# ================= RENDER SERVER =================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# ================= CONFIG =================
TOKEN = "8959503198:AAF7rdGMAiqOm4Y1QcOdYowOcfeOaYnBL4U"
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
            if "settings" not in data:
                data["settings"] = {"price_1000x": 15, "price_61x": 12}
            return data
        except: 
            return {"settings": {"price_1000x": 15, "price_61x": 12}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

db = load_db()

def get_balance(user_id):
    return int(db.get(str(user_id), 0))

def add_balance(user_id, amount):
    uid = str(user_id)
    db[uid] = get_balance(uid) + int(amount)
    save_db(db)

def get_price(category):
    return int(db.get("settings", {}).get(f"price_{category}", 15))

def set_price(category, price):
    if "settings" not in db:
        db["settings"] = {}
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
    category = State()
    amount = State()

class DepositState(StatesGroup):
    method = State()
    amount = State()
    txnid = State()

class AdminState(StatesGroup):
    upload_cat = State()
    price_cat = State()
    new_price = State()

# ================= PREMIUM KEYBOARDS =================
def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ BUY FACEBOOK ID", callback_data="products")],
            [InlineKeyboardButton(text="💳 Deposit", callback_data="deposit"), 
             InlineKeyboardButton(text="💰 My Balance", callback_data="balance")],
            [InlineKeyboardButton(text="🧑‍💻 Live Support", url="https://t.me/mohammadrony56"),
             InlineKeyboardButton(text="👨‍💻 Admin", callback_data="admin")]
        ]
    )

def admin_panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📂 Upload Stock", callback_data="admin_upload")],
            [InlineKeyboardButton(text="💰 Set ID Price", callback_data="admin_price")],
            [InlineKeyboardButton(text="💡 Balance Guide", callback_data="balhelp")],
            [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back")]
        ]
    )

def deposit_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 bKash", callback_data="dep_bkash"),
             InlineKeyboardButton(text="📱 Nagad", callback_data="dep_nagad")],
            [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]
        ]
    )

def back_btn():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]]
    )

# ================= DESIGN TEMPLATE =================
def get_dashboard_text(name, user_id):
    return (
        f"▬▬▬ ✦ PREMIUM ID STORE ✦ ▬▬▬\n\n"
        f"👤 **User::** {name}\n"
        f"🆔 **User ID::** `{user_id}`\n\n"
        f"──────────────────────────────\n"
        f"👋 **আমাদের বটে আপনাকে স্বাগতম!**\n"
        f"📥 স্টক শেষ হওয়ার আগেই নিচের বাটনে ক্লিক করে আপনার আইডি সংগ্রহ করুন 🎯!"
    )

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start(message: types.Message):
    name = message.from_user.full_name
    user_id = message.from_user.id
    await message.answer(get_dashboard_text(name, user_id), reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(Command("addbal"))
async def addbal(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = message.text.split()
        add_balance(uid, int(amount))
        await message.answer(f"✅ **Manual Success!** `{amount} BDT` added to `{uid}`.", parse_mode="Markdown")
    except:
        await message.answer("❌ Use: `/addbal user_id amount`", parse_mode="Markdown")

# --- ADMIN STOCK UPLOAD HANDLING ---
@dp.message(lambda m: m.document)
async def upload_stock(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    current_state = await state.get_state()
    
    if current_state != AdminState.upload_cat:
        await message.answer("⚠️ আগে এডমিন প্যানেল থেকে সিলেক্ট করুন কোন ক্যাটাগরির স্টক আপলোড করতে চান।")
        return
        
    user_data = await state.get_data()
    cat = user_data["upload_cat"]
    file_name = "1000x_pc.xlsx" if cat == "1000x" else "61x_pc.xlsx"
    
    try:
        await bot.download(message.document, destination=file_name)
        await message.answer(f"🚀 **{cat} PC CLONE Stock Updated Successfully!**", reply_markup=admin_panel(), parse_mode="Markdown")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ **Upload Failed!** Error: `{e}`", reply_markup=admin_panel())
        await state.clear()

elif data == "admin":
        if call.from_user.id != ADMIN_ID:
            await call.answer("❌ দুঃখিত! এই বাটনটি শুধুমাত্র অ্যাডমিনের জন্য।", show_alert=True)
            return
        
        await call.message.edit_text(
            "🔒 **ADMIN CONTROL PANEL**", 
            reply_markup=admin_panel() 
        )

    if data == "balance":
        await call.message.edit_text(
            f"▬▬▬ ✦ ACCOUNT BALANCE ✦ ▬▬▬\n\n"
            f"👤 User: **{name}**\n"
            f"💰 Available Balance: `{get_balance(user_id)} BDT` 💵\n\n"
            f"──────────────────────────────\n"
            f"ℹ️ _Need more balance? Click on Deposit to add funds._",
            reply_markup=back_btn(), parse_mode="Markdown"
        )

    elif data == "products":
        stock_1000x = read_excel("1000x_pc.xlsx")
        stock_61x = read_excel("61x_pc.xlsx")
        price_1000x = get_price("1000x")
        price_61x = get_price("61x")
        
        await call.message.edit_text(
            f"📦 **PRODUCT CATALOGUE**\n\n"
            f"🔥 **1. 1000x PC CLONE ID**\n"
            f"├ Stock: `{len(stock_1000x)} Pcs`\n"
            f"└ Price: `{price_1000x} BDT` / Pcs\n\n"
            f"🔥 **2. 61x PC CLONE ID**\n"
            f"├ Stock: `{len(stock_61x)} Pcs`\n"
            f"└ Price: `{price_61x} BDT` / Pcs\n\n"
            f"👇 আপনি কোন ক্যাটাগরির আইডি কিনতে চান তা নিচে সিলেক্ট করুন:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Buy 1000x PC CLONE", callback_data="buy_1000x")],
                    [InlineKeyboardButton(text="🛒 Buy 61x PC CLONE", callback_data="buy_61x")],
                    [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back")]
                ]
            ), parse_mode="Markdown"
        )

    elif data.startswith("buy_"):
        cat = data.split("_")[1]
        await state.update_data(category=cat)
        await state.set_state(BuyState.amount)
        await call.message.answer(
            f"🔢 **আপনি কত পিস {cat} PC CLONE আইডি কিনতে চান?**\n\n"
            f"👉 দয়া করে সংখ্যাটি লিখে পাঠান:", 
            parse_mode="Markdown"
        )

    elif data == "deposit":
        await call.message.edit_text(
            "📥 **CHOOSE DEPOSIT METHOD**\n\n"
            "নিচের যেকোনো একটি পেমেন্ট গেটওয়ে সিলেক্ট করুন:",
            reply_markup=deposit_menu(),
            parse_mode="Markdown"
        )

    elif data.startswith("dep_"):
        method = "bKash" if "bkash" in data else "Nagad"
        await state.update_data(method=method)
        await state.set_state(DepositState.amount)
        await call.message.edit_text(
            f"📱 **{method} (Personal):** `01639216168`\n"
            f"📢 **সর্বনিম্ন ডিপোজিট:** `20` টাকা।\n\n"
            f"💵 **ধাপ ১:** প্রথমে ওপরের নাম্বারে **Send Money** করুন।\n"
            f"📥 **ধাপ ২:** আপনি কত টাকা পাঠিয়েছেন তা নিচে টাইপ করে পাঠান (যেমন: `150`):",
            parse_mode="Markdown"
        )

    elif data == "admin":
        # আইডি চেক করার জন্য এই অংশটুকু ব্যবহার করো
        if call.from_user.id != ADMIN_ID:
            await call.answer("❌ দুঃখিত! এই বাটনটি শুধুমাত্র অ্যাডমিনের জন্য।", show_alert=True)
            return
        
        # অ্যাডমিন হলে কন্ট্রোল প্যানেল দেখাবে
        await call.message.edit_text(
            "🔒 **ADMIN CONTROL PANEL**", 
            reply_markup=admin_main_menu() # তোমার অ্যাডমিন মেনুর ফাংশন
        )
       
    elif data == "admin_upload":
        await call.message.edit_text(
            "📂 **কোন ক্যাটাগরির স্টক ফাইল আপলোড করতে চান?**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📁 Upload 1000x Stock", callback_data="upcat_1000x")],
                [InlineKeyboardButton(text="📁 Upload 61x Stock", callback_data="upcat_61x")],
                [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin")]
            ])
        )

    elif data.startswith("upcat_"):
        cat = data.split("_")[1]
        await state.update_data(upload_cat=cat)
        await state.set_state(AdminState.upload_cat)
        await call.message.edit_text(f"📂 **Please send the revised `.xlsx` file for {cat} PC CLONE now...**")

    elif data == "admin_price":
        await call.message.edit_text(
            "💰 **কোন ক্যাটাগরির দাম পরিবর্তন করতে চান?**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Set 1000x Price", callback_data="prcat_1000x")],
                [InlineKeyboardButton(text="💰 Set 61x Price", callback_data="prcat_61x")],
                [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin")]
            ])
        )

    elif data.startswith("prcat_"):
        cat = data.split("_")[1]
        await state.update_data(price_cat=cat)
        await state.set_state(AdminState.new_price)
        current_price = get_price(cat)
        await call.message.edit_text(f"💰 **SET {cat.upper()} PRICE**\n\n📊 বর্তমান দাম: `{current_price} BDT`\n\n👉 নতুন দামটি নিচে টাইপ করে পাঠান:")

    elif data == "balhelp":
        await call.message.edit_text("💡 `/addbal <user_id> <amount>`", reply_markup=admin_panel(), parse_mode="Markdown")

    elif data == "back":
        await state.clear()
        await call.message.edit_text(get_dashboard_text(name, user_id), reply_markup=main_menu(), parse_mode="Markdown")

    # --- Approve / Reject ---
    elif data.startswith("approve_"):
        _, target_uid, amount = data.split("_")
        add_balance(target_uid, amount)
        await call.message.edit_text(f"✅ **Deposit Approved!**\nUser `{target_uid}` কে `{amount} BDT` দেওয়া হয়েছে।", parse_mode="Markdown")
        try:
            await bot.send_message(target_uid, f"🎉 **Deposit Approved!**\n\n`{amount} BDT` has been credited to your account.", parse_mode="Markdown")
        except: pass

    elif data.startswith("reject_"):
        _, target_uid = data.split("_")
        await call.message.edit_text(f"❌ **Deposit Rejected!**", parse_mode="Markdown")
        try:
            await bot.send_message(target_uid, "❌ **Deposit Rejected!**\n\nYour transaction was invalid.", parse_mode="Markdown")
        except: pass

# ================= ADMIN PRICE SET PROCESS =================
@dp.message(AdminState.new_price)
async def process_new_price(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    try:
        new_price = int(message.text)
        if new_price <= 0: raise ValueError
    except:
        await message.answer("❌ **ভুল ইনপুট!** শুধু সংখ্যা লিখুন।")
        return

    user_data = await state.get_data()
    cat = user_data["price_cat"]
    set_price(cat, new_price)
    
    await message.answer(f"✅ **সফল হয়েছে!** {cat} এর নতুন দাম `{new_price} BDT` সেট করা হলো।", reply_markup=admin_panel(), parse_mode="Markdown")
    await state.clear()

# ================= DEPOSIT SUBMISSION PROCESS =================
MIN_DEPOSIT = 20

@dp.message(DepositState.amount)
async def dep_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0: raise ValueError
    except:
        await message.answer("❌ **ভুল ইনপুট!** দয়া করে সঠিক টাকার পরিমাণ সংখ্যায় লিখুন।")
        return

    if amount < MIN_DEPOSIT:
        await message.answer(f"⚠️ **দুঃখিত!** সর্বনিম্ন ডিপোজিট অ্যামাউন্ট হলো `{MIN_DEPOSIT} BDT`।\n👉 দয়া করে `{MIN_DEPOSIT}` বা তার বেশি টাকা পাঠিয়ে আবার সঠিক অ্যামাউন্টটি লিখুন:")
        return

    await state.update_data(amount=amount)
    await state.set_state(DepositState.txnid)
    await message.answer("🆔 **ধাপ ৩:** এবার পেমেন্টের **Transaction ID (TxnID)** টি লিখে পাঠান:")

@dp.message(DepositState.txnid)
async def dep_txnid(message: types.Message, state: FSMContext):
    txnid = message.text.strip()
    user_data = await state.get_data()
    method = user_data['method']
    amount = user_data['amount']
    user_id = message.from_user.id

    await message.answer("⏳ **পেমেন্ট রিকোয়েস্ট সাবমিট হয়েছে!** এডমিন ভেরিফাই করার পর ব্যালেন্স এড হবে।", reply_markup=back_btn())

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user_id}_{amount}"),
        InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user_id}")
    ]])

    await bot.send_message(
        ADMIN_ID,
        f"📥 **NEW DEPOSIT REQUEST**\n\n👤 **User:** {message.from_user.full_name} (`{user_id}`)\n💳 **Method:** {method}\n💰 **Amount:** `{amount} BDT`\n🔍 **TxnID:** `{txnid}`",
        reply_markup=admin_markup, parse_mode="Markdown"
    )
    await state.clear()

# ================= BUY PROCESS =================
@dp.message(BuyState.amount)
async def buy_amount(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    try:
        amount = int(message.text)
        if amount <= 0: raise ValueError
    except:
        await message.answer("❌ **Invalid Input!** Please send a valid positive number.")
        return

    user_data = await state.get_data()
    cat = user_data["category"]
    
    file_name = "1000x_pc.xlsx" if cat == "1000x" else "61x_pc.xlsx"
    stock = read_excel(file_name)

    if len(stock) < amount:
        await message.answer(f"❌ **Insufficient Stock!** Only `{len(stock)}` IDs available in {cat}.")
        await state.clear()
        return

    price_per_id = get_price(cat)
    total_price = amount * price_per_id
    
    if get_balance(user_id) < total_price:
        await message.answer(f"❌ **Insufficient Balance!** Need `{total_price} BDT`.\n\n👉 ব্যালেন্স চেক করতে 'My Balance' বাটনে ক্লিক করুন।")
        await state.clear()
        return

    bought = stock[:amount]
    stock = stock[amount:]
    write_excel(file_name, stock)
    add_balance(user_id, -total_price)

    wb = Workbook()
    ws = wb.active
    ws.append(["UID", "PASSWORD", "COOKIES"])
    for row in bought:
        def safe(i): return str(row[i]).strip() if len(row) > i and row[i] is not None else "N/A"
        ws.append([safe(0).replace(".0", ""), safe(1), safe(2)])

    delivery_file = f"buy_{cat}_{user_id}.xlsx"
    wb.save(delivery_file)

    try:
        await message.answer_document(FSInputFile(delivery_file), caption=f"🎉 **ORDER DELIVERED!**\n\n📦 **Category:** `{cat} PC CLONE`\n🔢 **Items:** `{amount} Pcs`\n💰 **Debited:** `{total_price} BDT`")
        if os.path.exists(delivery_file): os.remove(delivery_file)
    except Exception as e:
        await message.answer(f"❌ Delivery Error: `{e}`")
    await state.clear()

# ================= RUN BOT =================
async def main():
    threading.Thread(target=run_flask).start() # এটি সার্ভারটি ব্যাকগ্রাউন্ডে চালু রাখবে
    print("🔥 Shop Bot with Render Support Running...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
