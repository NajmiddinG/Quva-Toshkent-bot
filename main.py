import logging
from aiogram import Bot, Dispatcher, types, executor
import sqlite3
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta



# bot = Bot(token=API_TOKEN, proxy='http://server:3128') # for pythonanywhere
admins = {1157747787, 5294055251, 1456151744}
client_group = '-1001843864425'
# real
# driver_group_id = '-1001999379495'
# main_group = '-1001866888083'
# API_TOKEN = '6726936671:AAGvsymQGNa6CjDrL1bnl6yhFxN9Q24rXlQ'
# for me
driver_group_id = '-1001509656302'
main_group = '-1001902499620'
API_TOKEN = '7003670909:AAHW9sf_aO3hSAIjDfEfqJ61Nu8UBCmLgIs'
bot = Bot(token=API_TOKEN)
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

async def check_and_create_message_text_field():
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


async def get_order(order_id):
    try:
        c.execute('''SELECT * FROM orders WHERE order_id = ?''', (order_id,))
        order_info = c.fetchone()
        return order_info
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return -1

async def save_order(username='Noaniq', first_name='Noaniq', message_id='0', order_message_id='0', order_list='', message_text=''):
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
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return None

async def delete_order(order_id):
    try:
        # Execute the DELETE statement to remove the item with the specified order_id
        c.execute('''DELETE FROM orders WHERE order_id = ?''', (order_id,))
        # Commit the transaction
        conn.commit()
        return True
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return False

async def delete_old_orders():
    try:
        five_days_ago = datetime.now() - timedelta(days=5)
        c.execute('''DELETE FROM orders WHERE created_at < ?''', (five_days_ago,))
        conn.commit()
        return True
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return False

async def get_users(role):
    try:
        c.execute('''SELECT user_id, username, first_name FROM users where user_type = ?''', (role,))
        return set([row for row in c.fetchall()])
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return set()

async def get_users_id(role):
    try:
        c.execute('''SELECT user_id FROM users where user_type = ?''', (role,))
        return set([row[0] for row in c.fetchall()])
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return set()

async def get_user_info_by_id(user_id):
    try:
        c.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
        user_info = c.fetchone()
        return user_info  # Returns a tuple with user information (user_id, username, first_name, user_type) or None if user not found
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return None

async def get_user_info_by_username(username):
    try:
        c.execute('''SELECT * FROM users WHERE username = ?''', (username,))
        user_info = c.fetchone()
        return user_info  # Returns a tuple with user information (user_id, username, first_name, user_type) or None if user not found
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return None

async def add_user(user_id, username, first_name):
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
        bot.send_message(chat_id=1157747787, text=e)
        print("Error3:", e)

async def add_role_to_user(username, role):
    try:
        c.execute("SELECT * FROM users WHERE username=? OR username = ?", (username, '@' + username))
        user = c.fetchone()
        if user:
            user_id = user[0]
            emojies = {"Admin": '🤴', "Haydovchi": '🚖', "Foydalanuvchi": '🙎'}
            c.execute("UPDATE users SET user_type=? WHERE user_id=?", (role, user_id))
            conn.commit()
            if emojies.get(role): emojie = emojies[role]
            else: emojie = ''
            print(f"""Role '{role}' added to user '{username}'.""")
            return f"""{username} muavvaffaqiyatli {emojie} {role} ga aylandi"""
        else:
            print(f"""User '{username}' not found in the database.""")
            return f"""{username} botga start bermagan!"""
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return f"""Xatolik yuz berdi"""

async def delete_user(username):
    try:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        print(f"User with username '{username}' deleted.")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
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
    if user.id in await get_users_id('Admin'):
        await message.reply(f"👋 Assalomu alekum @{user.username} 🤴 admin.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard)
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await add_user(user.id, user.username, user.first_name)
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

# admin
@dp.message_handler(commands=['adminlar'])
async def handle_adminlar_command(message: types.Message):
    user = message.from_user
    if user.id in await get_users_id('Admin'):
        all_admins = await get_users('Admin')
        text = f"""Barcha 🤴 adminlar ({len(all_admins)})"""
        for index, admin in enumerate(all_admins):
            text+=f"""\n{index+1} - {admin[2]}: {admin[1]}"""
        await message.reply(text=text, reply_markup=keyboard)
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(commands=['admin_qoshish'])
async def handle_admin_qoshish_command(message: types.Message):
    user = message.from_user
    if user.id in await get_users_id('Admin'):
        await message.reply(text="Yangi adminni username ni kiriting:")
        await AddAdminState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=AddAdminState.WaitingForUsername)
async def handle_new_admin_username(message: types.Message, state: FSMContext):
    username = message.text
    await message.reply(await add_role_to_user(username, 'Admin'))
    await state.finish()

@dp.message_handler(commands=['admin_ochirish'])
async def handle_admin_ochirish_command(message: types.Message):
    user = message.from_user
    if user.id in await get_users_id('Admin'):
        await message.reply(text="Adminlikdan olib tashlamoqchi bo'lgan username ni kiriting:")
        await RemoveAdminState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=RemoveAdminState.WaitingForUsername)
async def handle_remove_admin_username(message: types.Message, state: FSMContext):
    username = message.text
    await message.reply(await add_role_to_user(username, 'Foydalanuvchi'))
    await state.finish()

# haydovchi
@dp.message_handler(commands=['haydovchilar'])
async def handle_haydovchilar_command(message: types.Message):
    user = message.from_user
    if user.id in await get_users_id('Admin'):
        all_drivers = await get_users('Haydovchi')
        text = f"""Barcha 🚖 haydovchilar ({len(all_drivers)})"""
        for index, driver in enumerate(all_drivers):
            text+=f"""\n{index+1} - {driver[2]}: {driver[1]}"""
        await message.reply(text=text, reply_markup=keyboard)
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(commands=['haydovchi_qoshish'])
async def handle_haydovchi_qoshish_command(message: types.Message):
    user = message.from_user
    if user.id in await get_users_id('Admin'):
        await message.reply(text="Yangi haydovchini username ni kiriting:")
        await AddDriverState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=AddDriverState.WaitingForUsername)
async def handle_new_driver_username(message: types.Message, state: FSMContext):
    username = message.text
    await message.reply(await add_role_to_user(username, 'Haydovchi'))
    await state.finish()

@dp.message_handler(commands=['haydovchi_ochirish'])
async def handle_haydovchi_ochirish_command(message: types.Message):
    user = message.from_user
    if user.id in await get_users_id('Admin'):
        await message.reply(text="Haydovchilikdan olib tashlamoqchi bo'lgan username ni kiriting:")
        await RemoveDriverState.WaitingForUsername.set()
    else:
        keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard2.add(KeyboardButton('/start'))
        if user.id in await get_users_id('Haydovchi'):
            await message.reply(f"👋 Assalomu alekum @{user.username} 🚖 haydovchi.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)
        else:
            await message.reply(f"👋 Assalomu alekum @{user.username} 🙎‍.\n🚖 Quva Toshkent botiga hush kelibsiz.", reply_markup=keyboard2)

@dp.message_handler(state=RemoveDriverState.WaitingForUsername)
async def handle_remove_driver_username(message: types.Message, state: FSMContext):
    username = message.text
    await message.reply(await add_role_to_user(username, 'Foydalanuvchi'))
    await state.finish()

async def modify_order_message_id(order_id, new_order_message_id):
    try:
        # Update the order_message_id for the specified order_id
        c.execute('''UPDATE orders SET order_message_id = ? WHERE order_id = ?''', (new_order_message_id, order_id))
        # Commit the transaction
        conn.commit()
        return True
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
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
        bot.send_message(chat_id=1157747787, text=e)
        print(e)
        return False

async def drivers_notice(order_id):
    order = await get_order(order_id=order_id)
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
    try:
        resp = await bot.forward_message(chat_id=client_group, from_chat_id=message.chat.id, message_id=message.message_id)
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
        order_id = await save_order(username=username, first_name=first_name, message_id=message_id, order_message_id='0', order_list='', message_text=message_text)
        await drivers_notice(order_id)
        
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(1, e)
        try:
            username = message.from_user.username
            await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n"+message.text)
        except Exception as e:
            bot.send_message(chat_id=1157747787, text=e)
            # print(2, e)
            try:
                username = message.from_user.username
                await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n")
            except: await bot.send_message(chat_id=driver_group_id, text="🚖Zakazchidan xabar: ")
    
    try: await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(e)
    
    try: await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Xurmatli mijoz sizning zakasingiz \n🚖 Haydovchilar qabul qilindi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055\n💬 Admin: @SHERZOD_QUVA""")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(e)
    try:
        success_text = f"""✅ Xurmatli #{message.from_user.first_name} sizning zakasingiz \n🚖 Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055\n💬 Admin: @SHERZOD_QUVA"""
        await bot.send_message(chat_id=main_group, text=success_text)
    except:
        success_text = f"""✅ Xurmatli #{message.from_user.id} sizning zakasingiz \n🚖 Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055\n💬 Admin: @SHERZOD_QUVA"""
        await bot.send_message(chat_id=main_group, text=success_text)


async def give_client(id, order):
    text = f"🙋‍ Mijozning ma'lumotlari: \nIsmi: {order[2]}\nUsername: {order[1]}"
    await bot.send_message(chat_id=id, text=text, protect_content=True)
    await bot.forward_message(chat_id=id, from_chat_id=client_group, message_id=order[3], protect_content=True)
    text = "Buyurtma holatini belgilang:"
    acc = "✅ Qabul qilindi!"
    dec = "🚫 Keyingi odamga o'tkazish!"
    
    # Create an InlineKeyboardMarkup with the button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=acc, callback_data=f'acc_order__{order[0]}')],
        [InlineKeyboardButton(text=dec, callback_data=f'dec_order__{order[0]}')]
    ])
    await bot.send_message(chat_id=id, text=text, reply_markup=keyboard, protect_content=True)


@dp.callback_query_handler(lambda query: query.data.startswith('acc_order__'))
async def handle_accept_query(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('__')[1])
    order = await get_order(order_id)
    await bot.delete_message(chat_id=driver_group_id, message_id=order[4])
    await delete_order(order_id=order_id)
    await callback_query.answer('✅ Qabul qilindi!')
    try: await bot.delete_message(chat_id=client_group, message_id=order[3])
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(e)
    
    for i in range(3):
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id-i)
        except Exception as e:
            # print(e)
            pass

@dp.callback_query_handler(lambda query: query.data.startswith('dec_order__'))
async def handle_decline_query(callback_query: types.CallbackQuery):
    await delete_old_orders()
    # Extract the order ID from the callback data
    order_id = int(callback_query.data.split('__')[1])
    order = await get_order(order_id)
    lists = order[5].split(',')
    try:
        new_order_list = ','.join(l for l in lists[1:])
    except: new_order_list = ''
    await update_order(order_id=order_id, order_list=new_order_list)
    await update_queue(order_id=order_id)
    try:
        if len(lists)>1:
            id = int(await get_user_info_by_username(lists[1])[0])
            order = await get_order(order_id=order_id)
            await give_client(id=id, order=order)
            await callback_query.answer("🚫 Keyingi odamga o'tkazildi!")
        else:
            await callback_query.answer("Sizdan olib tashlandi, sizdan keyin hech navbatda yo'q ekan")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
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
        resp = await bot.forward_message(chat_id=client_group, from_chat_id=message.chat.id, message_id=message.message_id)
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
        order_id = await save_order(username=username, first_name=first_name, message_id=message_id, order_message_id='0', order_list='', message_text=message_text)
        await drivers_notice(order_id)
        
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(3, e)
        try:
            username = message.from_user.username
            await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n"+message.text)
        except Exception as e:
            bot.send_message(chat_id=1157747787, text=e)
            # print(4, e)
            try:
                username = message.from_user.username
                await bot.send_message(chat_id=driver_group_id, text=f"🚖Zakazchidan xabar: @{username}\n")
            except: await bot.send_message(chat_id=driver_group_id, text="🚖Zakazchidan xabar: ")
    
        
    try:
        await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Xurmatli mijoz sizning zakasingiz \n🚖 Haydovchilar qabul qilindi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055\n💬 Admin: @SHERZOD_QUVA""")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(3, e)

async def update_queue(order_id):
    order = await get_order(order_id)
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
        await check_and_create_message_text_field()
        return True
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print("Error1:", e)
        return False

async def get_message_from_group(chat_id: int, message_id: int):
    try:
        # Retrieve the message from the group
        message = await bot.forward_message(chat_id=chat_id, from_chat_id=client_group, message_id=message_id)
        return message
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print("Error2:", e)
        return None
    
@dp.message_handler(content_types=['text', 'animation', 'audio', 'document', 'photo', 'sticker', 'video','video_note', 'voice', 'contact', 'dice', 'poll', 'venue', 'location','new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo','delete_chat_photo', 'group_chat_created', 'supergroup_chat_created','channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id','pinned_message', 'invoice', 'successful_payment', 'passport_data', 'game','voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited','inline_query', 'chosen_inline_result', 'callback_query', 'shipping_query','pre_checkout_query', 'unknown'])
async def handle_all_messages(message: types.Message, state: FSMContext):
    sender_id = message.from_user.id
    # print(message)
    if str(sender_id) != '1087968824': # 1087968824 is group message.from.id 
        if (sender_id not in await get_users_id('Admin') and sender_id not in await get_users_id('Haydovchi')):
            if str(message.chat.id) == main_group: # client message sended to group
                await forward_message_to_bot(message)
            if str(message.from_user.id) == str(message.chat.id): # client message sended to bot
                await forward_message_to_bot_not_delete(message)
        else: # user is admin or driver
            pass                

@dp.callback_query_handler(lambda query: query.data.startswith('check_turn__'))
async def handle_check_turn_callback(callback_query: types.CallbackQuery):
    sender_id = callback_query.from_user.id
    if sender_id not in await get_users_id('Admin'):
        await callback_query.answer("Bu tugma faqat adminlar uchun!")
        return
    if callback_query.message.chat.id != int(driver_group_id):
        await callback_query.answer("Xabar haydovchilar guruhida bo'lish kerak!")
        return
    # print(1, callback_query)
    order_id = int(callback_query.data.split('__')[1])
    order = await get_order(order_id=order_id)
    if order == -1:
        await callback_query.answer("Bu klient allaqachon haydovchi topgan!")
        return
    # print(2, order)
    try:
        order_list = order[5]
        for index, username in enumerate(order_list.split(',')):
            if index == 0: continue
            user_id = await get_user_info_by_username(username)[0]

            order = await get_order(order_id=order_id)
            await give_client(user_id, order)
            await callback_query.answer("Sizga botda lichka tashlandi: @QuvaToshkent_bot !")
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(e)
        await callback_query.answer("Xatolik kelib chiqdi!")
        return
    await callback_query.answer("Username sizda bo'lishi talab qilinadi!")


@dp.callback_query_handler(lambda query: query.data.startswith('add_turn__'))
async def handle_add_turn_callback(callback_query: types.CallbackQuery):
    sender_id = callback_query.from_user.id
    if (sender_id not in await get_users_id('Admin') and sender_id not in await get_users_id('Haydovchi')):
        await callback_query.answer("Siz haydovchi yoki admin bo'lishingiz kerak!")
        return
    if callback_query.message.chat.id != int(driver_group_id):
        await callback_query.answer("Xabar haydovchilar guruhida bo'lish kerak!")
        return
    # print(1, callback_query)
    order_id = int(callback_query.data.split('__')[1])
    order = await get_order(order_id=order_id)
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
                    order = await get_order(order_id=order_id)
                    await give_client(callback_query.from_user.id, order)
                    await callback_query.answer("Sizga botda lichka tashlandi: @QuvaToshkent_bot !")
                await update_queue(order_id)
    except Exception as e:
        bot.send_message(chat_id=1157747787, text=e)
        # print(e)
        await callback_query.answer("Xatolik kelib chiqdi!")
        return
    await callback_query.answer("Username sizda bo'lishi talab qilinadi!")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
