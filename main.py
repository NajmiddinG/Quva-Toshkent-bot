import os
import sys
import signal
import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load the .env file
load_dotenv(override=True)

# Retrieve environment variables
admins = set(os.getenv('ADMINS').split(','))
api_token = os.getenv('API_TOKEN')
archive_group_id = os.getenv('ARCHIVE_GROUP_ID')
client_group_id = os.getenv('CLIENT_GROUP_ID')
driver_group_id = os.getenv('DRIVER_GROUP_ID')
main_group_id = os.getenv('MAIN_GROUP_ID')


order_info = {
    "gived": "Zakasni ko'rib chiqmoqda.",
    "accepted": "Zakas qabul qilindi.",
    "decline": "Zakas atkaz qilindi.",
}

# PID file setup
PID_FILE = '/tmp/aiogram_bot.pid'
def cleanup_pid_file():
    """Remove the PID file if it exists."""
    if os.path.isfile(PID_FILE):
        os.remove(PID_FILE)

def handle_exit(signum, frame):
    """Handle termination signals and clean up before exiting."""
    print(f"Received signal {signum}. Exiting...")
    cleanup_pid_file()
    sys.exit(0)

# Register signal handlers for clean termination
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def check_and_create_pid_file():
    """Check if the PID file exists and verify if the process is still running."""
    if os.path.isfile(PID_FILE):
        with open(PID_FILE, 'r') as f:
            old_pid = f.read().strip()
        
        try:
            os.kill(int(old_pid), 0)  # Sends signal 0 to check if the process is alive
            print(f"Another instance is running with PID {old_pid}. Exiting.")
            sys.exit()
        except (OSError, ValueError):
            print("Stale PID file found. Removing and starting a new instance.")
            cleanup_pid_file()
    
    # Create the PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

# Check and create PID file
check_and_create_pid_file()

# Bot initialization
bot = Bot(token=api_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class AddAdminState(StatesGroup):
    WaitingForUsername = State()

class RemoveAdminState(StatesGroup):
    WaitingForUsername = State()

class AddDriverState(StatesGroup):
    WaitingForUsername = State()

class RemoveDriverState(StatesGroup):
    WaitingForUsername = State()

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                user_type TEXT
             )''')
conn.commit()


c.execute('''CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                message_id TEXT,
                order_message_id TEXT,
                order_list TEXT,
                created_at DATE DEFAULT CURRENT_DATE,
                message_text text
             )''')
conn.commit()

def check_and_create_message_text_field():
    # Check if the 'message_text' column exists
    c.execute('''PRAGMA table_info(orders)''')
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'message_text' not in column_names:
        # If 'message_text' doesn't exist, add it
        c.execute('''ALTER TABLE orders ADD COLUMN message_text TEXT''')
        conn.commit()
        print("Added 'message_text' column to the 'orders' table.")
    else:
        print("The 'message_text' column already exists in the 'orders' table.")
    return "Success"

check_and_create_message_text_field()

def get_order(order_id):
    try:
        c.execute('''SELECT * FROM orders WHERE order_id = ?''', (order_id,))
        order_info = c.fetchone()
        return order_info
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="1: " + e)
        return -1

def save_order(username='Noaniq', first_name='Noaniq', message_id='0', order_message_id='0', order_list='', message_text=''):
    if message_id == '0': return
    try:
        # Insert a new row into the orders table
        c.execute('''INSERT INTO orders (username, first_name, message_id, order_message_id, order_list, created_at, message_text) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', (username, first_name, message_id, order_message_id, order_list, datetime.now(), message_text))
        conn.commit()
        # Retrieve the last inserted row ID (order_id)
        order_id = c.lastrowid
        return order_id
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="2: " + e)
        return None

def delete_order(order_id):
    try:
        # Execute the DELETE statement to remove the item with the specified order_id
        c.execute('''DELETE FROM orders WHERE order_id = ?''', (order_id,))
        # Commit the transaction
        conn.commit()
        return True
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="3: " + e)
        print(e)
        return False

def delete_old_orders():
    try:
        five_days_ago = datetime.now() - timedelta(days=5)
        c.execute('''DELETE FROM orders WHERE created_at < ?''', (five_days_ago,))
        conn.commit()
        return True
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="4: " + e)
        print(e)
        return False

def get_users(role):
    try:
        c.execute('''SELECT user_id, username, first_name FROM users where user_type = ?''', (role,))
        return set([row for row in c.fetchall()])
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="5: " + e)
        print(e)
        return set()

def get_users_id(role):
    try:
        c.execute('''SELECT user_id FROM users where user_type = ?''', (role,))
        return set([row[0] for row in c.fetchall()])
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="6: " + e)
        print(e)
        return set()

def get_user_info_by_id(user_id):
    try:
        c.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
        user_info = c.fetchone()
        return user_info  # Returns a tuple with user information (user_id, username, first_name, user_type) or None if user not found
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="7: " + e)
        print(e)
        return None

def get_user_info_by_username(username):
    try:
        c.execute('''SELECT * FROM users WHERE username = ?''', (username,))
        user_info = c.fetchone()
        return user_info  # Returns a tuple with user information (user_id, username, first_name, user_type) or None if user not found
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="8: " + e)
        print(e)
        return None

def add_user(user_id, username, first_name):
    username = '@' + username
    try:
        c.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
        existing_user = c.fetchone()
        if existing_user:
            c.execute('''UPDATE users SET username = ?, first_name = ? WHERE user_id = ?''', (username, first_name, user_id))
            conn.commit()
            print("User information updated successfully.")
        else:
            c.execute('''INSERT INTO users (user_id, username, first_name, user_type) VALUES (?, ?, ?, ?)''', (user_id, username, first_name, 'Foydalanuvchi'))
            conn.commit()
            print("New user added successfully.")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="9: " + e)
        print("Error3:", e)

def add_role_to_user(username: str, role):
    if username.startswith('/'): return
    if not username.startswith('@'): username = "@" + username
    try:
        c.execute("SELECT * FROM users WHERE username=? OR username = ?", (username, username[1:]))
        user = c.fetchone()
        if user:
            user_id = user[0]
            emojies = {"Admin": '🤴', "Haydovchi": '🚖', "Foydalanuvchi": '🙎'}
            c.execute("UPDATE users SET user_type=? WHERE user_id=?", (role, user_id))
            conn.commit()
            if emojies.get(role): emojie = emojies[role]
            else: emojie = ''
            return f"""{username} muavvaffaqiyatli {emojie} {role} ga aylandi""", True
        else:
            return f"""{username} botga start bermagan!""", False
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="10: " + e)
        print(e)
        return f"""Xatolik yuz berdi""", False

def delete_user(username):
    try:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        print(f"User with username '{username}' deleted.")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text="11: " + e)
        print(e)

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("/adminlar"))
keyboard.add(KeyboardButton("/admin_qoshish"))
keyboard.add(KeyboardButton("/admin_ochirish"))
keyboard.add(KeyboardButton("/haydovchilar"))
keyboard.add(KeyboardButton("/haydovchi_qoshish"))
keyboard.add(KeyboardButton("/haydovchi_ochirish"))
keyboard.add(KeyboardButton('/start'))

@dp.message_handler(commands=['start'])
async def handle_start_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        await message.reply(f"👋 Assalomu alekum @{user.username} 🤴 admin.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard)
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            add_user(user.id, user.username, user.first_name)
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

# admin
@dp.message_handler(commands=['adminlar'])
async def handle_adminlar_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        all_admins = get_users('Admin')
        text = f"""Barcha 🤴 adminlar ({len(all_admins)})"""
        for index, admin in enumerate(all_admins):
            text+=f"""\n{index+1} - {admin[2]}: {admin[1]}"""
        await message.reply(text=text, reply_markup=keyboard)
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(commands=['admin_qoshish'])
async def handle_admin_qoshish_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        await message.reply(text="Yangi adminni username ni kiriting:")
        await AddAdminState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=AddAdminState.WaitingForUsername)
async def handle_new_admin_username(message: types.Message, state: FSMContext):
    username = message.text
    if not username.startswith("@"): username = "@" + username
    new_role = "Admin"
    new_user = get_user_info_by_username(username)
    res, status = add_role_to_user(username, new_role)
    if status:
        admin_user = get_user_info_by_id(message.from_user.id)
        archive_message = role_change_template_for_archive(admin_user, new_user, new_user[3], new_role)
        await send_to_archive_group(message=archive_message)

    await message.reply(res)
    await state.finish()

@dp.message_handler(commands=['admin_ochirish'])
async def handle_admin_ochirish_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        await message.reply(text="Adminlikdan olib tashlamoqchi bo'lgan username ni kiriting:")
        await RemoveAdminState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=RemoveAdminState.WaitingForUsername)
async def handle_remove_admin_username(message: types.Message, state: FSMContext):
    username = message.text
    if not username.startswith("@"): username = "@" + username
    new_role = "Foydalanuvchi"
    new_user = get_user_info_by_username(username)
    res, status = add_role_to_user(username, new_role)
    if status:
        admin_user = get_user_info_by_id(message.from_user.id)
        archive_message = role_change_template_for_archive(admin_user, new_user, new_user[3], new_role)
        await send_to_archive_group(message=archive_message)

    await message.reply(res)
    await state.finish()

# haydovchi
@dp.message_handler(commands=['haydovchilar'])
async def handle_haydovchilar_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        all_drivers = get_users('Haydovchi')
        text = f"""Barcha 🚖 haydovchilar ({len(all_drivers)})"""
        for index, driver in enumerate(all_drivers):
            text+=f"""\n{index+1} - {driver[2]}: {driver[1]}"""
        await message.reply(text=text, reply_markup=keyboard)
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(commands=['haydovchi_qoshish'])
async def handle_haydovchi_qoshish_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        await message.reply(text="Yangi haydovchini username ni kiriting:")
        await AddDriverState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=AddDriverState.WaitingForUsername)
async def handle_new_driver_username(message: types.Message, state: FSMContext):
    username = message.text
    if not username.startswith("@"): username = "@" + username
    new_role = "Haydovchi"
    new_user = get_user_info_by_username(username)
    res, status = add_role_to_user(username, new_role)
    if status:
        admin_user = get_user_info_by_id(message.from_user.id)
        archive_message = role_change_template_for_archive(admin_user, new_user, new_user[3], new_role)
        await send_to_archive_group(message=archive_message)

    await message.reply(res)
    await state.finish()

@dp.message_handler(commands=['haydovchi_ochirish'])
async def handle_haydovchi_ochirish_command(message: types.Message):
    user = message.from_user
    if user.id in get_users_id('Admin'):
        await message.reply(text="Haydovchilikdan olib tashlamoqchi bo'lgan username ni kiriting:")
        await RemoveDriverState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=RemoveDriverState.WaitingForUsername)
async def handle_remove_driver_username(message: types.Message, state: FSMContext):
    username = message.text
    if not username.startswith("@"): username = "@" + username
    new_role = "Foydalanuvchi"
    new_user = get_user_info_by_username(username)
    res, status = add_role_to_user(username, new_role)
    if status:
        admin_user = get_user_info_by_id(message.from_user.id)
        archive_message = role_change_template_for_archive(admin_user, new_user, new_user[3], new_role)
        await send_to_archive_group(message=archive_message)

    await message.reply(res)
    await state.finish()

async def modify_order_message_id(order_id, new_order_message_id):
    try:
        # Update the order_message_id for the specified order_id
        c.execute('''UPDATE orders SET order_message_id = ? WHERE order_id = ?''', (new_order_message_id, order_id))
        # Commit the transaction
        conn.commit()
        return True
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="12: " + e)
        print(e)
        return False

async def update_order(order_id, order_list):
    try:
        # Update the order_message_id for the specified order_id
        c.execute('''UPDATE orders SET order_list = ? WHERE order_id = ?''', (order_list, order_id))
        # Commit the transaction
        conn.commit()
        return True
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="13: " + e)
        print(e)
        return False

async def drivers_notice(order_id, client_message = None):
    order = get_order(order_id=order_id)
    for admin_id in admins:
        admin_id = int(admin_id)
        if int(admin_id) != 1157747787:
            await give_client_for_admin(admin_id, order)
    
    await asyncio.sleep(15)
    if get_order(order_id) is None: return
    if client_message: await send_client_success_message(client_message)
    text = f"💸 Klientning xabari:<i>{order[-1]}</i>\n🚖Navbatlar:\n1 - joy. bo'sh'\n@QuvaToshkent_bot'"
    button_label = "🙋‍♂ Navbatga yozilish!"
    button_label2 = "➡️ Qolganlarga o'tkazish!"

    # Create an InlineKeyboardMarkup with the button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_label, callback_data=f'add_turn__{order_id}')],
        [InlineKeyboardButton(text=button_label2, callback_data=f'check_turn__{order_id}')]
    ])
    
    # Send the message with the button to the group
    response = await bot.send_message(chat_id=driver_group_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await modify_order_message_id(order_id=order_id, new_order_message_id=response.message_id)
    return response

async def forward_message_to_bot(message: types.Message):
    try: first_name = message.from_user.first_name
    except: first_name = 'Noaniq'
    try: username = '@'+message.from_user.username
    except: username = 'Noaniq'
    resp = await bot.forward_message(chat_id=client_group_id, from_chat_id=message.chat.id, message_id=message.message_id)
    try: await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="16: " + e)
    try:
        try: message_id = resp.message_id
        except: message_id = 'Noaniq'
        message_text = ''
        try:
            for i in str(message.text).split():
                d = 0
                for j in i:
                    if j.isnumeric(): d+=1
                if d<3:
                    message_text += ' ' + i
        except: pass
        order_id = save_order(username=username, first_name=first_name, message_id=message_id, order_message_id='0', order_list='', message_text=message_text)
        await drivers_notice(order_id, client_message=message)
        
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="14: " + e)
        # print(1, e)
        try:
            username = message.from_user.username
            await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n"+message.text)
        except Exception as e:
            await bot.send_message(chat_id=1157747787, text="15: " + e)
            # print(2, e)
            try:
                username = message.from_user.username
                await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n")
            except: await bot.send_message(chat_id=driver_group_id, text="🚖Zakazchidan xabar: ")
    
    
        # print(e)
    
    try: await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Xurmatli mijoz sizning zakasingiz \n🚖Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998905327262\n💬 Admin: @DQOSIMOV""")
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="17: " + e)
        # print(e)

async def send_client_success_message(message: types.Message):
    try:
        success_text = f"""✅ Xurmatli #{message.from_user.first_name} sizning zakasingiz \n🚖 Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998905327262\n💬 Admin: @DQOSIMOV"""
        await bot.send_message(chat_id=main_group_id, text=success_text)
    except:
        success_text = f"""✅ Xurmatli #{message.from_user.id} sizning zakasingiz \n🚖 Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998905327262\n💬 Admin: @DQOSIMOV"""
        await bot.send_message(chat_id=main_group_id, text=success_text)

async def give_client(id, order):
    text = f"🙋‍ Mijozning ma'lumotlari: \nIsmi: {order[2]}\nUsername: {order[1]}"
    await bot.send_message(chat_id=id, text=text, protect_content=True)
    await bot.forward_message(chat_id=id, from_chat_id=client_group_id, message_id=order[3], protect_content=True)
    text = "Buyurtma holatini belgilang:"
    acc = "✅ Qabul qilindi!"
    dec = "🚫 Keyingi odamga o'tkazish!"
    
    # Create an InlineKeyboardMarkup with the button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=acc, callback_data=f'acc_order__{order[0]}')],
        [InlineKeyboardButton(text=dec, callback_data=f'dec_order__{order[0]}')]
    ])
    await bot.send_message(chat_id=id, text=text, reply_markup=keyboard, protect_content=True)
    archive_message = order_message_template_for_archive(id, order, order_info['gived'])
    await send_to_archive_group(message=archive_message)

async def give_client_for_admin(id, order):
    text = f"🙋‍ Mijozning ma'lumotlari: \nIsmi: {order[2]}\nUsername: {order[1]}"
    await bot.send_message(chat_id=id, text=text, protect_content=True)
    await bot.forward_message(chat_id=id, from_chat_id=client_group_id, message_id=order[3], protect_content=True)
    text = "Buyurtma holatini belgilang:"
    acc = "✅ Qabul qilindi!"
    # Create an InlineKeyboardMarkup with the button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=acc, callback_data=f'admin_acc_order__{order[0]}')],
    ])
    await bot.send_message(chat_id=id, text=text, reply_markup=keyboard, protect_content=True)
    archive_message = order_message_template_for_archive(id, order, order_info['gived'])
    await send_to_archive_group(message=archive_message)

@dp.callback_query_handler(lambda query: query.data.startswith('admin_acc_order__'))
async def handle_accept_query_for_admins(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('__')[1])
    order = get_order(order_id)
    if order is None: return
    delete_order(order_id=order_id)
    await callback_query.answer('✅ Qabul qilindi!')

    archive_message = order_message_template_for_archive(callback_query.from_user.id, order, order_info['accepted'])
    await send_to_archive_group(message=archive_message)

    for i in range(1):
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id-i)
        except Exception as e:
            # print(e)
            pass

@dp.callback_query_handler(lambda query: query.data.startswith('acc_order__'))
async def handle_accept_query(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('__')[1])
    order = get_order(order_id)
    await bot.delete_message(chat_id=driver_group_id, message_id=order[4])
    delete_order(order_id=order_id)
    await callback_query.answer('✅ Qabul qilindi!')

    archive_message = order_message_template_for_archive(callback_query.from_user.id, order, order_info['accepted'])
    await send_to_archive_group(message=archive_message)
    
    # try: await bot.delete_message(chat_id=client_group_id, message_id=order[3])
    # except Exception as e:
    #   await bot.send_message(chat_id=1157747787, text="18: " + e)
    #     # print(e)
    
    for i in range(1):
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id-i)
        except Exception as e:
            # print(e)
            pass

@dp.callback_query_handler(lambda query: query.data.startswith('dec_order__'))
async def handle_decline_query(callback_query: types.CallbackQuery):
    delete_old_orders()
    # Extract the order ID from the callback data
    order_id = int(callback_query.data.split('__')[1])
    order = get_order(order_id)
    lists = order[5].split(',')
    archive_message = order_message_template_for_archive(callback_query.from_user.id, order, order_info['decline'])
    await send_to_archive_group(message=archive_message)
    try:
        new_order_list = ','.join(l for l in lists[1:])
    except: new_order_list = ''
    await update_order(order_id=order_id, order_list=new_order_list)
    await update_queue(order_id=order_id)
    try:
        if len(lists)>1:
            id = int(get_user_info_by_username(lists[1])[0])
            order = get_order(order_id=order_id)
            await give_client(id=id, order=order)
            await callback_query.answer("🚫 Keyingi odamga o'tkazildi!")
        else:
            await callback_query.answer("Sizdan olib tashlandi, sizdan keyin hech navbatda yo'q ekan")
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="19: " + e)
        # print(1, e)
    
    for i in range(3):
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id-i)
        except Exception as e:
            # print(e)
            pass

async def forward_message_to_bot_not_delete(message: types.Message):
    try: first_name = message.from_user.first_name
    except: first_name = 'Noaniq'
    try: username = '@'+message.from_user.username
    except: username = 'Noaniq'
    try:
        resp = await bot.forward_message(chat_id=client_group_id, from_chat_id=message.chat.id, message_id=message.message_id)
        try: message_id = resp.message_id
        except: message_id = 'Noaniq'
        message_text = ''
        try:
            for i in str(message.text).split():
                d = 0
                for j in i:
                    if j.isnumeric(): d+=1
                if d<3:
                    message_text += ' ' + i
        except: pass
        order_id = save_order(username=username, first_name=first_name, message_id=message_id, order_message_id='0', order_list='', message_text=message_text)
        await drivers_notice(order_id)
        
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="20: " + e)
        # print(3, e)
        try:
            username = message.from_user.username
            await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n"+message.text)
        except Exception as e:
            await bot.send_message(chat_id=1157747787, text="21: " + e)
            # print(4, e)
            try:
                username = message.from_user.username
                await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n")
            except: await bot.send_message(chat_id=driver_group_id, text="🚖Zakazchidan xabar: ")

    try:
        await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Xurmatli mijoz sizning zakasingiz \n🚖 Haydovchilar qabul qilindi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998905327262\n💬 Admin: @DQOSIMOV""")
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="22: " + e)
        # print(3, e)

async def update_queue(order_id):
    order = get_order(order_id)
    try:
        text = f"💸 Klientning xabari:<i>{order[-1]}</i>\n🚖Navbatlar:"
        i = 0
        if order[5]:
            for username in order[5].split(','):
                i+=1
                text+= f'\n{i} - joy. {username}'
        i+=1

        while i<4:
            text += f"\n{i} - joy. bo'sh"
            i+=1
        text += '\n@QuvaToshkent_bot'

        button_label = "🙋‍♂ Navbatga yozilish!"
        button_label2 = "➡️ Qolganlarga o'tkazish!"
        
        
        # Create an InlineKeyboardMarkup with the button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_label, callback_data=f'add_turn__{order_id}')],
            [InlineKeyboardButton(text=button_label2, callback_data=f'check_turn__{order_id}')]
        ])
        await bot.edit_message_text(chat_id=driver_group_id, message_id=order[4], text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return True
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="23: " + e)
        # print("Error1:", e)
        return False

async def get_message_from_group(chat_id: int, message_id: int):
    try:
        # Retrieve the message from the group
        message = await bot.forward_message(chat_id=chat_id, from_chat_id=client_group_id, message_id=message_id)
        return message
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="24: " + e)
        # print("Error2:", e)
        return None

@dp.message_handler(content_types=['text', 'animation', 'audio', 'document', 'photo', 'sticker', 'video','video_note', 'voice', 'contact', 'dice', 'poll', 'venue', 'location','new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo','delete_chat_photo', 'group_chat_created', 'supergroup_chat_created','channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id','pinned_message', 'invoice', 'successful_payment', 'passport_data', 'game','voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited','inline_query', 'chosen_inline_result', 'callback_query', 'shipping_query','pre_checkout_query', 'unknown'])
async def handle_all_messages(message: types.Message, state: FSMContext):
    non_user_message_types = ['new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo',
                              'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created',
                              'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id',
                              'pinned_message', 'invoice', 'successful_payment', 'passport_data', 'game',
                              'voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited']
    
    if message.content_type in non_user_message_types:
        try: await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e: await bot.send_message(chat_id=1157747787, text="25: " + e)
        return

    sender_id = message.from_user.id

    if str(sender_id) != '1087968824':  # 1087968824 is group message.from.id
        if (sender_id not in get_users_id('Admin') and sender_id not in get_users_id('Haydovchi')):
            if str(message.chat.id) == main_group_id:  # client message sent to group
                await forward_message_to_bot(message)
            if str(message.from_user.id) == str(message.chat.id):  # client message sent to bot
                await forward_message_to_bot_not_delete(message)
        else:  # user is admin or driver
            pass

@dp.callback_query_handler(lambda query: query.data.startswith('check_turn__'))
async def handle_check_turn_callback(callback_query: types.CallbackQuery):
    sender_id = callback_query.from_user.id
    if sender_id not in get_users_id('Admin'):
        await callback_query.answer("Bu tugma faqat adminlar uchun!")
        return
    if callback_query.message.chat.id != int(driver_group_id):
        await callback_query.answer("Xabar haydovchilar guruhida bo'lish kerak!")
        return
    # print(1, callback_query)
    order_id = int(callback_query.data.split('__')[1])
    order = get_order(order_id=order_id)
    if order == -1:
        await callback_query.answer("Bu klient allaqachon haydovchi topgan!")
        return
    # print(2, order)
    try:
        order_list = order[5]
        for index, username in enumerate(order_list.split(',')):
            if index == 0: continue
            user_id = get_user_info_by_username(username)[0]

            order = get_order(order_id=order_id)
            await give_client(user_id, order)
            await callback_query.answer("Sizga botda lichka tashlandi: @QuvaToshkent_bot !")
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="26: " + e)
        # print(e)
        await callback_query.answer("Xatolik kelib chiqdi!")
        return
    await callback_query.answer("Username sizda bo'lishi talab qilinadi!")

@dp.callback_query_handler(lambda query: query.data.startswith('add_turn__'))
async def handle_add_turn_callback(callback_query: types.CallbackQuery):
    sender_id = callback_query.from_user.id
    if (sender_id not in get_users_id('Admin') and sender_id not in get_users_id('Haydovchi')):
        await callback_query.answer("Siz haydovchi yoki admin bo'lishingiz kerak!")
        return
    if callback_query.message.chat.id != int(driver_group_id):
        await callback_query.answer("Xabar haydovchilar guruhida bo'lish kerak!")
        return
    # print(1, callback_query)
    order_id = int(callback_query.data.split('__')[1])
    order = get_order(order_id=order_id)
    if order == -1:
        await callback_query.answer("Bu klient allaqachon haydovchi topgan!")
        return
    # print(2, order)
    try:
        username = callback_query.from_user.username
        if username in order[5]:
            await callback_query.answer("Siz allaqachon navbatga yozilgansiz!")
            return
        else:
            order_list = order[5]
            if order_list.count('@')>3:
                await callback_query.answer("barcha o'rinlar band!")
                return
            if order_list == '': order_list = '@'+username
            else: order_list += ',@'+username
            if await update_order(order_id=order[0], order_list=order_list):
                c = order_list.count(',')
                await callback_query.answer(f"Siz navbatga {c+1}-bo'lib qo'shildingiz")
                if c == 0:
                    order = get_order(order_id=order_id)
                    await give_client(callback_query.from_user.id, order)
                    await callback_query.answer("Sizga botda lichka tashlandi: @QuvaToshkent_bot !")
                await update_queue(order_id)
    except Exception as e:
        await bot.send_message(chat_id=1157747787, text="27: " + e)
        # print(e)
        await callback_query.answer("Xatolik kelib chiqdi!")
        return
    await callback_query.answer("Username sizda bo'lishi talab qilinadi!")

def order_message_template_for_archive(driver_id, order, info):
    # Fetch driver information
    haydovchi = get_user_info_by_id(driver_id)

    # Prepare the message content with improved formatting
    message = (
        f"📝 <b>Zakaz:</b> <a href='https://t.me/c/{client_group_id[4:]}/{order[3]}'>{order[3]}</a>\n"
        f"👨‍✈️ <b>Haydovchi:</b> {haydovchi[1]} ({haydovchi[2]})\n"
        f"👤 <b>Mijoz:</b> {order[1]} ({order[2]})\n"
        f"📌 <b>Maqsad:</b> <i>{info}</i>\n"
        f"📅 <b>Sana:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    return message

def role_change_template_for_archive(admin_user, new_user, old_role, new_role):
    message = (
        f"🔄 <b>Rol o'zgarishi haqida xabar</b>\n"
        f"👤 <b>Admin:</b> {admin_user[1]} ({admin_user[2]})\n"
        f"👥 <b>Foydalanuvchi:</b> {new_user[1]} ({new_user[2]})\n"
        f"🛠️ <b>Eski rol:</b> {old_role}\n"
        f"🎉 <b>Yangi rol:</b> {new_role}\n"
        f"📅 <b>O'zgarish sanasi:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    return message

async def send_to_archive_group(message: str):
    try:
        await bot.send_message(chat_id=archive_group_id, text=message, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Failed to send message to archive group: {e}")

if __name__ == '__main__':
    try:
        # Start polling
        logging.basicConfig(level=logging.INFO)
        executor.start_polling(dp, skip_updates=True)
    finally:
        # Ensure the PID file is removed when the script ends
        cleanup_pid_file()
