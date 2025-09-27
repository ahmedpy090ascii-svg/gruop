import telebot
import json
import asyncio
import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from datetime import datetime

TOKEN = "6177009557:AAEi4g8P0xpISUpodXDIjX8cbf_TWeCDvz4"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 1319444402
SESSIONS_FILE = "sessions.json"

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def is_allowed(user_id):
    return True

def load_sessions():
    try:
        with open(SESSIONS_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

def save_session(new_session, user_id):
    sessions = load_sessions()
    if not any(sess['session'] == new_session for sess in sessions):
        sessions.append({"session": new_session, "user_id": user_id})
        save_json(SESSIONS_FILE, sessions)

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("‹ اضافة حساب ›", callback_data="add_account"),
        InlineKeyboardButton("‹ عرض الحسابات ›", callback_data="show_accounts")
    )
    markup.add(InlineKeyboardButton("‹ انشاء مجموعات ›", callback_data="create_groups"))
    markup.row(
        InlineKeyboardButton("‹ Source DrOx ›", url="https://t.me/ABNabbasbot"),
        InlineKeyboardButton("‹ Developer ›", url="https://t.me/BBwKK")
    )
    return markup

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "⌁︙ مرحباً بك في لوحة التحكم :", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "add_account")
def handle_add(call):
    bot.edit_message_text("⌁︙ ارسل لي جلسة ( تليثون ) الحساب :", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: process_session(m, call.from_user.id))

def process_session(message, user_id):
    session = message.text.strip()
    if len(session) < 20:
        bot.send_message(message.chat.id, "⌁︙الجلسة لا تعمل تأكد انها نشطة او تكون تليثون .")
        return

    async def validate_and_save():
        try:
            client = TelegramClient(StringSession(session), 100000, 'placeholder')
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                bot.send_message(message.chat.id, "⌁︙الجلسة غير مفعّلة .")
                return
            await client(functions.channels.JoinChannelRequest(channel='c1111o'))
            user = await client.get_me()
            save_session(session, user_id)
            await client.disconnect()
            bot.send_message(message.chat.id, f"⌁︙تم تسجيل الدخول : {user.first_name or ''} @{user.username or 'لا يوجد'}")
        except Exception as e:
            bot.send_message(message.chat.id, f"خطأ: {str(e)}")

    asyncio.run(validate_and_save())

@bot.callback_query_handler(func=lambda call: call.data == "create_groups")
def handle_create_groups(call):
    sessions = load_sessions()
    user_sessions = [s for s in sessions if s.get("user_id") == call.from_user.id]

    if not user_sessions:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("‹ رجوع ›", callback_data="back"))
        bot.edit_message_text("⌁︙لا توجد جلسات .", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return

    bot.edit_message_text("⌁︙جاري إنشاء 50 مجموعة ...", call.message.chat.id, call.message.message_id)

    for i, session in enumerate(user_sessions, start=1):
        asyncio.run(async_create_50_groups(session["session"], call.message.chat.id))

async def async_create_50_groups(session_string, chat_id):
    try:
        client = TelegramClient(StringSession(session_string), 100000, 'placeholder')
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            bot.send_message(chat_id, "⌁︙الجلسة غير مفعّلة.")
            return

        today = datetime.now().strftime("%d-%m-%Y")
        description = "‹ By @bbwkk - @AbnAbbasbot ›"

        for i in range(50):
            title = f"{today} - {i+1}"
            result = await client(functions.channels.CreateChannelRequest(
                title=title,
                about=description,
                megagroup=True
            ))
            group = result.chats[0]
            for _ in range(10):
                await client.send_message(group.id, description)
            invite = await client(functions.messages.ExportChatInviteRequest(group.id))
            bot.send_message(
                chat_id,
                f"⌁︙تم إنشاء المجموعة رقم {i+1} — [رابط الدعوة]({invite.link})",
                parse_mode="Markdown"
            )

            # بعد إرسال الرابط، يغادر الحساب المجموعة
            try:
                await client(functions.channels.LeaveChannelRequest(group.id))
            except Exception as e:
                bot.send_message(chat_id, f"⌁︙خطأ أثناء مغادرة المجموعة: {str(e)}")

        await client.disconnect()
    except Exception as e:
        bot.send_message(chat_id, f"خطأ: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "show_accounts")
def handle_show_accounts(call):
    sessions = load_sessions()
    user_sessions = [s for s in sessions if s.get("user_id") == call.from_user.id]

    if not user_sessions:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("‹ رجوع ›", callback_data="back"))
        bot.edit_message_text("⌁︙لا توجد جلسات .", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return

    markup = InlineKeyboardMarkup()
    for i, session in enumerate(user_sessions):
        # عرض رقم الحساب واسم الحساب (أو username)
        try:
            client = TelegramClient(StringSession(session["session"]), 100000, 'placeholder')
            asyncio.run(client.connect())
            user = asyncio.run(client.get_me())
            client.disconnect()
            name_display = f"{user.first_name or ''} @{user.username or 'لا يوجد'}"
        except:
            name_display = "غير متصل"
        markup.row(
            InlineKeyboardButton(f"{i+1} - {name_display}", callback_data=f"acc_{i+1}"),
            InlineKeyboardButton("🗑", callback_data=f"delete_acc_{i}")
        )
    markup.add(InlineKeyboardButton("‹ رجوع ›", callback_data="back"))
    bot.edit_message_text("⌁︙الحسابات:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_acc_"))
def delete_account(call):
    index = int(call.data.split("_")[-1])
    sessions = load_sessions()

    user_sessions = [s for s in sessions if s.get("user_id") == call.from_user.id]
    if index < len(user_sessions):
        session_to_delete = user_sessions[index]
        sessions.remove(session_to_delete)
        save_json(SESSIONS_FILE, sessions)
        bot.answer_callback_query(call.id, "⌁︙تم حذف الجلسة بنجاح")
    else:
        bot.answer_callback_query(call.id, "⌁︙فشل في العثور على الجلسة", show_alert=True)

    handle_show_accounts(call)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def go_back(call):
    bot.edit_message_text(
        "⌁︙ مرحباً بك في لوحة التحكم :",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu()
    )

def create_all_groups_periodically():
    while True:
        print("⌁︙بدء مهمة إنشاء المجموعات التلقائية.")
        sessions = load_sessions()
        for i, sess in enumerate(sessions, start=1):
            try:
                asyncio.run(async_create_50_groups(sess["session"], ADMIN_ID))
            except Exception as e:
                print(f"⌁︙خطأ في الجلسة رقم {i}: {e}")
        print("⌁︙تم إنشاء جميع المجموعات، الانتظار 12 ساعة...")
        time.sleep(43200)

threading.Thread(target=create_all_groups_periodically, daemon=True).start()

bot.polling()