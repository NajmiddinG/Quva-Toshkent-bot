import logging
from aiogram import Bot, Dispatcher, types, executor
import sqlite3
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


# bot = Bot(token=API_TOKEN, proxy='http://server:3128') # for pythonanywhere
group_id = '-1001999379495'
main_group = '-1001866888083'
admins = {1157747787, 5294055251, 1456151744}
API_TOKEN = '6726936671:AAGvsymQGNa6CjDrL1bnl6yhFxN9Q24rXlQ'
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


def get_users(role):
    try:
        c.execute('''SELECT user_id, username, first_name FROM users where user_type = ?''', (role,))
        return set([row for row in c.fetchall()])
    except Exception as e:
        print(e)
        return set()

def get_users_id(role):
    try:
        c.execute('''SELECT user_id FROM users where user_type = ?''', (role,))
        return set([row[0] for row in c.fetchall()])
    except Exception as e:
        print(e)
        return set()

def get_user_info_by_id(user_id):
    try:
        c.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
        user_info = c.fetchone()
        return user_info  # Returns a tuple with user information (user_id, username, first_name, user_type) or None if user not found
    except Exception as e:
        print(e)
        return None

def get_user_info_by_username(username):
    try:
        c.execute('''SELECT * FROM users WHERE username = ?''', (username,))
        user_info = c.fetchone()
        return user_info  # Returns a tuple with user information (user_id, username, first_name, user_type) or None if user not found
    except Exception as e:
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
        print("Error:", e)


def add_role_to_user(username, role):
    try:
        c.execute("SELECT * FROM users WHERE username=?", (username,))
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
        print(e)
        return f"""Xatolik yuz berdi"""

def delete_user(username):
    try:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        print(f"User with username '{username}' deleted.")
    except Exception as e:
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
    await message.reply(add_role_to_user(username, 'Admin'))
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
    await message.reply(add_role_to_user(username, 'Foydalanuvchi'))
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
    await message.reply(add_role_to_user(username, 'Haydovchi'))
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
    await message.reply(add_role_to_user(username, 'Foydalanuvchi'))
    await state.finish()

async def forward_message_to_bot(message: types.Message):
    # try: await bot.send_message(chat_id='-1002128600395', text=f"{message.chat.title} guruhudan habar\n📲 Bog'lanish: @{message.from_user.username}")
    # except Exception as e: print(e)
    try: await bot.forward_message(chat_id=group_id, from_chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e: print(e)
    try:
        await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Xurmatli mijoz sizning zakasingiz \n🚖 Haydovchilar qabul qilindi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055, +998911290055\n💬 Admin: @Quva_Toshkent_admin""")
    except:
        pass
    try:
        success_text = f"""✅ Xurmatli #{message.from_user.first_name} sizning zakasingiz \n🚖 Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055, +998911290055\n💬 Admin: @Quva_Toshkent_admin"""
        await bot.send_message(chat_id=main_group, text=success_text)
    except:
        success_text = f"""✅ Xurmatli #{message.from_user.id} sizning zakasingiz \n🚖 Haydovchilar guruhiga tushdi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055, +998911290055\n💬 Admin: @Quva_Toshkent_admin"""
        await bot.send_message(chat_id=main_group, text=success_text)
    try: await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e: print(e)

async def forward_message_to_bot_not_delete(message: types.Message):
    try: await bot.forward_message(chat_id=group_id, from_chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e: print(e)
    try:
        await bot.send_message(chat_id=message.from_user.id, text=f"""✅ Xurmatli mijoz sizning zakasingiz \n🚖 Haydovchilar qabul qilindi.\n💬 Lichkangizga ishonchli 🚕 shoferlarimiz aloqaga chiqadi.\n📞 Murojaat uchun tel: +998916580055, +998911290055\n💬 Admin: @Quva_Toshkent_admin""")
    except:
        pass

@dp.message_handler(content_types=['text', 'animation', 'audio', 'document', 'photo', 'sticker', 'video','video_note', 'voice', 'contact', 'dice', 'poll', 'venue', 'location','new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo','delete_chat_photo', 'group_chat_created', 'supergroup_chat_created','channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id','pinned_message', 'invoice', 'successful_payment', 'passport_data', 'game','voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited','inline_query', 'chosen_inline_result', 'callback_query', 'shipping_query','pre_checkout_query', 'unknown'])
async def handle_all_messages(message: types.Message, state: FSMContext):
    sender_id = message.from_user.id
    if (sender_id not in get_users_id('Admin') and sender_id not in get_users_id('Haydovchi')):
        if str(message.chat.id) == str(main_group):
            await forward_message_to_bot(message)
        if str(message.from_user.id) == str(message.chat.id):
            await forward_message_to_bot_not_delete(message)
        

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
