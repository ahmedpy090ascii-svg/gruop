import asyncio
import random
import string
import re
from datetime import datetime
import aiohttp
from telethon import TelegramClient, events, Button, functions
from telethon.sessions import StringSession

BOT_TOKEN = '5829861326:AAEzlipz1HV7FjWsn71HQjw4HWA_DCRl5kM'
API_ID = 13618444
API_HASH = '715b4336809df845976854b2e004b846'

#المتغيرات العامة
session_string = None
hunter_client = None
is_hunting = False
selected_mode = None
account_info = "( ماكو جلسة )"
hunting_task = None
counter = 0
channel = None
semaphore = asyncio.Semaphore(5)
TIMEOUT = 10
waiting_for_session = {}  # لتتبع من ينتظر جلسة

# إحصائيات الصيد
hunt_stats = {
    "total_checked": 0,
    "taken": 0,
    "sold": 0,
    "unavailable": 0,
    "unknown": 0,
    "successful_captures": 0
}
#جلسه البوت
bot = TelegramClient('conttrrol_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def create_channel():
    global channel, hunter_client, session_string
    try:
        result = await hunter_client(functions.channels.CreateChannelRequest(
            title="AbnAbbas",
            about="nothing❗",
            megagroup=False
        ))
        channel = result.chats[0]
        print("✓ تم إنشاء قناة جديدة بنجاح")
        return True
    except Exception as e:
        error_msg = str(e)
        if "CHANNELS_TOO_MUCH" in error_msg:
            print("❌ وصلت للحد الأقصى من القنوات المسموح بها")
        elif "USERNAME_INVALID" in error_msg:
            print("❌ اسم القناة غير مقبول")
        else:
            print(f"❌ فشل إنشاء القناة: {error_msg}")
        return False

async def send_video_with_description(client, current_time, user, clicks, is_flood=False, flood_time_remaining=None):
    try:
        video_url = "https://t.me/nnwnnnw/32"
        video_message = f"""
╭───⌁【 𖠶 𝙵𝙻𝙾𝙾𝙳 𝚄𝚂𝙴𝚁 】⌁───╮
│
│ 👤 USERNAME ⤳ @{user}
│
│ ⏳ TIME ⤳ {current_time}
│ 🔻 Flood Ends In ⤳ {flood_time_remaining}s
│
│ 🎢 PY ⤳ @bbwkk
╰──────────────────────────╯
"""
        await client.send_file("bbwkk", video_url, caption=video_message)
    except Exception as e:
        print(f"فشل إرسال الفيديو: {str(e)}")

async def assign_username_to_channel(client, username, clicks):
    global channel
    try:
        if channel is None:
            if not await create_channel():
                print(f"❌ فشل إنشاء قناة جديدة للمستخدم @{username}")
                return False

        channel_entity = await client.get_input_entity(channel)  
        await client(functions.channels.UpdateUsernameRequest(channel_entity, username))  
        print(f"✓ تم تثبيت @{username} في القناة بنجاح")  
        
        about_text = f"الوقت| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  
        await client(functions.messages.EditChatAboutRequest(peer=channel_entity, about=about_text))  
        await send_video_with_description(client, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username, clicks)  
        
        channel = None 
        return True  
    except Exception as e:  
        error_msg = str(e)  
        if "too many public channels" in error_msg:  
            alert_message = f"⛔ خطأ في صيد @{username}\nانت تمتلك العديد من القنوات العامة!"  
            await client.send_message("me", alert_message)  
            return False  
        elif "A wait of" in error_msg:  
            wait_time = int(error_msg.split("A wait of ")[1].split(" seconds")[0].strip())  
            asyncio.create_task(send_video_with_description(client, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username, clicks, is_flood=True, flood_time_remaining=wait_time))  
            return False  
        else:  
            return False

async def check_username(session, user, client, clicks):
    global counter, hunt_stats
    try:
        async with semaphore:
            async with session.get(f"https://fragment.com/username/{user}", timeout=TIMEOUT) as response:
                html = await response.text()
                hunt_stats["total_checked"] += 1
                
                if '<span class="tm-section-header-status tm-status-taken">Taken</span>' in html:
                    hunt_stats["taken"] += 1
                    print(f"[{counter + 1}] -> {user} -> Taken")
                elif '<span class="tm-section-header-status tm-status-unavail">Sold</span>' in html:
                    hunt_stats["sold"] += 1
                    print(f"[{counter + 1}] -> {user} -> Sold")
                elif '<div class="table-cell-status-thin thin-only tm-status-unavail">Unavailable</div>' in html:
                    hunt_stats["unavailable"] += 1
                    print(f"[{counter + 1}] -> {user} -> Unavailable")
                    success = await assign_username_to_channel(client, user, clicks)
                    if success: 
                        hunt_stats["successful_captures"] += 1
                        return True
                else:
                    hunt_stats["unknown"] += 1
                    print(f"[{counter + 1}] -> {user} -> Unknown")
                counter += 1
    except:
        pass

def generate_usernames(count=500, mode=None):
    usernames = []
    for _ in range(count):
        # نمط aabbc 
        a = random.choice(string.ascii_lowercase)
        b = random.choice([c for c in string.ascii_lowercase if c != a])
        c = random.choice([d for d in string.ascii_lowercase if d != a and d != b])
        username = f"{b}{b}{a}{c}{c}"
        usernames.append(username)
    return usernames

async def check_usernames_loop(client, mode):
    global is_hunting
    while is_hunting:
        connector = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            usernames = generate_usernames(500)
            tasks = [check_username(session, user, client, clicks=counter) for user in usernames]
            await asyncio.gather(*tasks)

def main_btns():
    h_text = "[ إيقاف الصيد إ" if is_hunting else "[ تفعيل الصيد ] "
    return [
        [Button.inline(f"[ النمط: aabbc ]", b"inf1")],
        [Button.inline("( إضف جلسة )", b"add"), Button.inline("( حذف جلسة )", b"del")],
        [Button.inline(h_text, b"toggle")],
        [Button.inline("( الاحصائيات )", b"stats"),Button.inline(f"{account_info}", b"inf2")]
    ]

def get_start_message(name):
    return f'• أهلين! {name}\n\nانا بوت اختصاصي صيد معرفات 😽\n\nالبوت آمن وخاصتاً على الحسابات الأساسيه !'

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    name = sender.first_name
    await event.respond(get_start_message(name), buttons=main_btns())

@bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id in waiting_for_session))
async def handle_session_input(event):
    global session_string, hunter_client, account_info, waiting_for_session
    user_id = event.sender_id
    
    if user_id not in waiting_for_session:
        return
    
    # حذف الرسالة التي تحتوي على الجلسة
    try:
        await event.delete()
    except:
        pass
    
    session_text = event.text.strip()
    
    try:
        cl = TelegramClient(StringSession(session_text), API_ID, API_HASH)
        await cl.connect()
        if await cl.is_user_authorized():
            me = await cl.get_me()
            session_string = session_text
            hunter_client = cl
            account_info = f"( {me.first_name} )"
            
            # إعادة الرسالة الأصلية
            sender = await event.get_sender()
            name = sender.first_name
            await event.respond(f"✅ تم تفعيل: {account_info}", alert=True)
            await event.respond(get_start_message(name), buttons=main_btns())
        else:
            await event.respond("❌ جلسة غير صالحة!", alert=True)
            sender = await event.get_sender()
            name = sender.first_name
            await event.respond(get_start_message(name), buttons=main_btns())
    except Exception as e:
        await event.respond(f"❌ فشل الاتصال: {str(e)}", alert=True)
        sender = await event.get_sender()
        name = sender.first_name
        await event.respond(get_start_message(name), buttons=main_btns())
    
    # إزالة المستخدم من قائمة الانتظار
    if user_id in waiting_for_session:
        del waiting_for_session[user_id]

@bot.on(events.CallbackQuery)
async def handler(event):
    global session_string, hunter_client, is_hunting, selected_mode, account_info, hunting_task, channel, hunt_stats, waiting_for_session

    if event.data == b"add":  
        user_id = event.sender_id
        
        if user_id in waiting_for_session:
            # إذا كان المستخدم بالفعل في وضع الانتظار، نرجع للواجهة الرئيسية
            del waiting_for_session[user_id]
            sender = await event.get_sender()
            name = sender.first_name
            await event.edit(get_start_message(name), buttons=main_btns())
            await event.answer("تم إلغاء طلب إضافة الجلسة", alert=True)
            return
        
        # إضافة المستخدم لقائمة الانتظار
        waiting_for_session[user_id] = True
        
        # تعديل الرسالة الحالية
        add_session_message = "أرسل الجلسة (String Session):"
        back_button = [[Button.inline("( رجوع )", b"cancel_add_session")]]
        await event.edit(add_session_message, buttons=back_button)
        await event.answer()

    elif event.data == b"cancel_add_session":
        user_id = event.sender_id
        # إزالة المستخدم من قائمة الانتظار
        if user_id in waiting_for_session:
            del waiting_for_session[user_id]
        
        # العودة للواجهة الرئيسية
        sender = await event.get_sender()
        name = sender.first_name
        await event.edit(get_start_message(name), buttons=main_btns())
        await event.answer("تم الإلغاء", alert=True)

    elif event.data == b"del":  
        if not hunter_client: 
            await event.answer("ماكو جلسة اساسا! ", alert=True)  
        else:  
            session_string, hunter_client, account_info, is_hunting = None, None, "( ماكو جلسة )", False  
            hunt_stats = {k: 0 for k in hunt_stats}
            await event.answer(" تم الحذف", alert=True)  
            sender = await event.get_sender()
            name = sender.first_name
            await event.edit(get_start_message(name), buttons=main_btns())

    elif event.data == b"toggle":  
        if not hunter_client: 
            await event.answer(" أضف جلسة أولاً!", alert=True)  
        else:  
            if not is_hunting:  
                is_hunting = True  
                hunt_stats = {k: 0 for k in hunt_stats}
                if await create_channel():  
                    hunting_task = asyncio.create_task(check_usernames_loop(hunter_client, selected_mode))  
                    await event.answer("( بدء الصيد )", alert=True)  
                else:  
                    is_hunting = False  
                    await event.answer("❌ فشل إنشاء قناة!", alert=True)  
            else:  
                is_hunting = False  
                if hunting_task: 
                    hunting_task.cancel()  
                await event.answer("( توقف الصيد )", alert=True)  
            
            sender = await event.get_sender()
            name = sender.first_name
            await event.edit(get_start_message(name), buttons=main_btns())
    
    elif event.data == b"stats":
        if not hunter_client:
            await event.answer("إضف جلسة أولاً!", alert=True)
        else:
            stats_message = f"""
 **إحصائيات الصيد**

🔹 **( The number ) :** {hunt_stats['total_checked']}
🔹 ** (Taken):** {hunt_stats['taken']}
🔹 **(Sold):** {hunt_stats['sold']}
🔹 ** (Unavailable):** {hunt_stats['unavailable']}
🔹 **(Good):** {hunt_stats['successful_captures']}
🔹 **( Unknown ):** {hunt_stats['unknown']}

 **الحالة:** {'( نشط )' if is_hunting else ' ( متوقف )'}
            """
            back_button = [[Button.inline("( رجوع )", b"back_to_main")]]
            await event.edit(stats_message, buttons=back_button)
            await event.answer()

    elif event.data == b"back_to_main":
        # عند الضغط على زر الرجوع، نعود للواجهة الرئيسية
        sender = await event.get_sender()
        name = sender.first_name
        await event.edit(get_start_message(name), buttons=main_btns())
        await event.answer()
        
    elif event.data == b"inf1":
        await event.answer("النمط الحالي: aabbc", alert=True)
        
    elif event.data == b"inf2":
        await event.answer(account_info, alert=True)

print("Control System Online")
bot.run_until_disconnected()
