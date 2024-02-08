import logging
from aiogram import Bot, Dispatcher, types, executor
import sqlite3
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


group_id = '-1002128600395'
admins = {1157747787, 5294055251, 1456151744}
API_TOKEN = '6726936671:AAGvsymQGNa6CjDrL1bnl6yhFxN9Q24rXlQ'
bot = Bot(token=API_TOKEN, proxy='http://proxy.server:3128')
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
    try: await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e: print(e)

@dp.message_handler(content_types=['text', 'animation', 'audio', 'document', 'photo', 'sticker', 'video','video_note', 'voice', 'contact', 'dice', 'poll', 'venue', 'location','new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo','delete_chat_photo', 'group_chat_created', 'supergroup_chat_created','channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id','pinned_message', 'invoice', 'successful_payment', 'passport_data', 'game','voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited','inline_query', 'chosen_inline_result', 'callback_query', 'shipping_query','pre_checkout_query', 'unknown'])
async def handle_all_messages(message: types.Message, state: FSMContext):
    sender_id = message.from_user.id
    if sender_id not in get_users_id('Admin') and sender_id not in get_users_id('Haydovchi'):
        await forward_message_to_bot(message)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)



















# {"message_id": 77, 
#  "from": {"id": 1157747787, 
#           "is_bot": False, 
#           "first_name": "Najmiddin", 
#           "username": "Najmiddin_pc", 
#           "language_code": "en"}, 
#  "chat": {"id": -1001902499620, 
#           "title": "Algorithms", 
#           "type": "supergroup"}, 
#  "date": 1706988134, 
#  "photo": [
#      {"file_id": "AgACAgIAAx0CcWXXJAADTWW-kmY0c5erRwqLDTy827W7oYmZAALb0zEb9aX4STaADIH-P1z4AQADAgADcwADNAQ", "file_unique_id": "AQAD29MxG_Wl-El4", "file_size": 1112, "width": 42, "height": 90}, 
#      {"file_id": "AgACAgIAAx0CcWXXJAADTWW-kmY0c5erRwqLDTy827W7oYmZAALb0zEb9aX4STaADIH-P1z4AQADAgADbQADNAQ", "file_unique_id": "AQAD29MxG_Wl-Ely", "file_size": 14747, "width": 148, "height": 320}, 
#      {"file_id": "AgACAgIAAx0CcWXXJAADTWW-kmY0c5erRwqLDTy827W7oYmZAALb0zEb9aX4STaADIH-P1z4AQADAgADeAADNAQ", "file_unique_id": "AQAD29MxG_Wl-El9", "file_size": 60834, "width": 371, "height": 800}, 
#      {"file_id": "AgACAgIAAx0CcWXXJAADTWW-kmY0c5erRwqLDTy827W7oYmZAALb0zEb9aX4STaADIH-P1z4AQADAgADeQADNAQ", "file_unique_id": "AQAD29MxG_Wl-El-", "file_size": 102253, "width": 594, "height": 1280}]
#  }



# # {"message_id": 59, "from": {"id": 1157747787, "is_bot": false, "first_name": "Najmiddin", "username": "Najmiddin_pc", "language_code": "en"}, "chat": {"id": -1001902499620, "title": "Algorithms", "type": "supergroup"}, "date": 1706986340, "text": "Fgg"}

# {
# "update_id": 668010483,
# "my_chat_member": {
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "from": {
# "id": 1157747787,
# "is_bot": False,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "date": 1706983771,
# "old_chat_member": {
# "user": {
# "id": 6921124146,
# "is_bot": True,
# "first_name": "Farg'ona Toshkent",
# "username": "Fergana_tashkentbot"
# },
# "status": "member"
# },
# "new_chat_member": {
# "user": {
# "id": 6921124146,
# "is_bot": True,
# "first_name": "Farg'ona Toshkent",
# "username": "Fergana_tashkentbot"
# },
# "status": "administrator",
# "can_be_edited": False,
# "can_manage_chat": True,
# "can_change_info": True,
# "can_delete_messages": True,
# "can_invite_users": True,
# "can_restrict_members": True,
# "can_pin_messages": True,
# "can_manage_topics": True,
# "can_promote_members": False,
# "can_manage_video_chats": True,
# "is_anonymous": False,
# "can_manage_voice_chats": True
# }
# }
# }
# "update_id": 668010491,
# "my_chat_member": {
# "chat": {
# "id": -1002128600395,
# "title": "Najmiddin and Farg'ona Toshkent",
# "type": "supergroup"
# },
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "date": 1706984398,
# "old_chat_member": {
# "user": {
# "id": 6921124146,
# "is_bot": true,
# "first_name": "Farg'ona Toshkent",
# "username": "Fergana_tashkentbot"
# },
# "status": "member"
# },
# "new_chat_member": {
# "user": {
# "id": 6921124146,
# "is_bot": true,
# "first_name": "Farg'ona Toshkent",
# "username": "Fergana_tashkentbot"
# },
# "status": "administrator",
# "can_be_edited": false,
# "can_manage_chat": true,
# "can_change_info": true,
# "can_delete_messages": true,
# "can_invite_users": true,
# "can_restrict_members": true,
# "can_pin_messages": true,
# "can_manage_topics": true,
# "can_promote_members": false,
# "can_manage_video_chats": true,
# "is_anonymous": false,
# "can_manage_voice_chats": true
# }
# }




# {
# "ok": true,
# "result": [
# {
# "update_id": 668010542,
# "message": {
# "message_id": 93,
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "date": 1706989330,
# "audio": {
# "duration": 26,
# "file_name": "7120-download-iphone-6-original-ringtone-42676.mp3",
# "mime_type": "audio/mpeg",
# "file_id": "CQACAgIAAx0CcWXXJAADXWW-lxJwiXKtKbVsE3LW_vvN64QSAAJFQgAC9aX4SSXGSMXdPx0LNAQ",
# "file_unique_id": "AgADRUIAAvWl-Ek",
# "file_size": 212994
# }
# }
# },
# {
# "update_id": 668010543,
# "message": {
# "message_id": 94,
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "date": 1706989391,
# "document": {
# "file_name": "nef-2023-statement.pdf",
# "mime_type": "application/pdf",
# "thumbnail": {
# "file_id": "AAMCAgADHQJxZdckAANeZb6XT1HbeXFmR3w9_LwfqkNjJbAAAoM-AALVXslLiiDIzwTzDcEBAAdtAAM0BA",
# "file_unique_id": "AQADgz4AAtVeyUty",
# "file_size": 13064,
# "width": 226,
# "height": 320
# },
# "thumb": {
# "file_id": "AAMCAgADHQJxZdckAANeZb6XT1HbeXFmR3w9_LwfqkNjJbAAAoM-AALVXslLiiDIzwTzDcEBAAdtAAM0BA",
# "file_unique_id": "AQADgz4AAtVeyUty",
# "file_size": 13064,
# "width": 226,
# "height": 320
# },
# "file_id": "BQACAgIAAx0CcWXXJAADXmW-l09R23lxZkd8Pfy8H6pDYyWwAAKDPgAC1V7JS4ogyM8E8w3BNAQ",
# "file_unique_id": "AgADgz4AAtVeyUs",
# "file_size": 204492
# }
# }
# },
# {
# "update_id": 668010544,
# "message": {
# "message_id": 95,
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "date": 1706989515,
# "video_note": {
# "duration": 2,
# "length": 384,
# "thumbnail": {
# "file_id": "AAMCAgADHQJxZdckAANfZb6Xy4UVmuonVzfarlyMhKpy8P8AAkxCAAL1pfhJ-0JpIjc50OEBAAdtAAM0BA",
# "file_unique_id": "AQADTEIAAvWl-Ely",
# "file_size": 10409,
# "width": 320,
# "height": 320
# },
# "thumb": {
# "file_id": "AAMCAgADHQJxZdckAANfZb6Xy4UVmuonVzfarlyMhKpy8P8AAkxCAAL1pfhJ-0JpIjc50OEBAAdtAAM0BA",
# "file_unique_id": "AQADTEIAAvWl-Ely",
# "file_size": 10409,
# "width": 320,
# "height": 320
# },
# "file_id": "DQACAgIAAx0CcWXXJAADX2W-l8uFFZrqJ1c32q5cjISqcvD_AAJMQgAC9aX4SftCaSI3OdDhNAQ",
# "file_unique_id": "AgADTEIAAvWl-Ek",
# "file_size": 222461
# }
# }
# },
# {
# "update_id": 668010545,
# "message": {
# "message_id": 96,
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "date": 1706989566,
# "voice": {
# "duration": 1,
# "mime_type": "audio/ogg",
# "file_id": "AwACAgIAAx0CcWXXJAADYGW-l_5mUB-iwwpjzXQm-0cN9RJ7AAJPQgAC9aX4SZ-PGJuz1Hi2NAQ",
# "file_unique_id": "AgADT0IAAvWl-Ek",
# "file_size": 29681
# }
# }
# },
# {
# "update_id": 668010546,
# "message": {
# "message_id": 97,
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "date": 1706989725,
# "poll": {
# "id": "5330192630678554647",
# "question": "Dndjdj",
# "options": [
# {
# "text": "Ejej",
# "voter_count": 0
# },
# {
# "text": "Nn",
# "voter_count": 0
# },
# {
# "text": "N",
# "voter_count": 0
# }
# ],
# "total_voter_count": 0,
# "is_closed": false,
# "is_anonymous": true,
# "type": "regular",
# "allows_multiple_answers": false
# }
# }
# },
# {
# "update_id": 668010547,
# "message": {
# "message_id": 98,
# "from": {
# "id": 1157747787,
# "is_bot": false,
# "first_name": "Najmiddin",
# "username": "Najmiddin_pc",
# "language_code": "en"
# },
# "chat": {
# "id": -1001902499620,
# "title": "Algorithms",
# "type": "supergroup"
# },
# "date": 1706989769,
# "sticker": {
# "width": 512,
# "height": 512,
# "emoji": "😂",
# "set_name": "robocontestuz",
# "is_animated": false,
# "is_video": false,
# "type": "regular",
# "thumbnail": {
# "file_id": "AAMCAgADHQJxZdckAANiZb6YycLeCXlpx2iG6mzr0J-HcwIAAv8PAAK2O6lLN6hTLjbqE88BAAdtAAM0BA",
# "file_unique_id": "AQAD_w8AArY7qUty",
# "file_size": 9778,
# "width": 320,
# "height": 320
# },
# "thumb": {
# "file_id": "AAMCAgADHQJxZdckAANiZb6YycLeCXlpx2iG6mzr0J-HcwIAAv8PAAK2O6lLN6hTLjbqE88BAAdtAAM0BA",
# "file_unique_id": "AQAD_w8AArY7qUty",
# "file_size": 9778,
# "width": 320,
# "height": 320
# },
# "file_id": "CAACAgIAAx0CcWXXJAADYmW-mMnC3gl5acdohups69Cfh3MCAAL_DwACtjupSzeoUy426hPPNAQ",
# "file_unique_id": "AgAD_w8AArY7qUs",
# "file_size": 15868
# }
# }
# }
# ]
# }
