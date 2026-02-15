import telebot
import os
import subprocess
import threading
import json
import sys
import datetime
from flask import Flask
from telebot import types

# --- الإعدادات الأساسية (عدل هنا) ---
TOKEN = "8469488876:AAFxGLdbBOB0xYbRcPokw_YFH0VTKaOmRA4"
ADMIN_IDS = [8018653004] # أيدي الأدمن
CHANNEL_USER = "@fareshw" # يوزر القناة للاشتراك الإجباري
CHANNEL_LINK = "https://t.me/fareshw"
UPLOAD_DIR = "hosting_files"
DB_FILE = "system_db.json"

# --- تجهيز البيئة ---
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

def load_db():
    if not os.path.exists(DB_FILE):
        data = {"users": {}, "total_users": [], "banned": [], "settings": {"status": "online"}}
        save_db(data)
        return data
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

bot = telebot.TeleBot(TOKEN)
running_procs = {} # لتتبع العمليات المشغلة حالياً

# --- سيرفر الويب للبقاء حياً 24/7 ---
app = Flask('')
@app.route('/')
def home(): return f"Server is running. Active processes: {len(running_procs)}"

def run_web(): app.run(host='0.0.0.0', port=8080)

# --- فحص الاشتراك الإجباري ---
def is_subscribed(uid):
    try:
        status = bot.get_chat_member(CHANNEL_USER, uid).status
        return status in ['member', 'administrator', 'creator']
    except: return True

# --- لوحات المفاتيح (UI) ---
def main_menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📤 رفع ملف بايثون", callback_data="upload"),
           types.InlineKeyboardButton("📂 ملفاتي المرفوعة", callback_data="my_files"))
    kb.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="user_stats"),
           types.InlineKeyboardButton("🛡️ الدعم الفني", url="https://t.me/fareshw"))
    
    if uid in ADMIN_IDS:
        kb.add(types.InlineKeyboardButton("⚙️ لوحة التحكم (أدمن)", callback_data="admin_panel"))
    return kb

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    db = load_db()
    
    # إضافة المستخدم للقاعدة
    if uid not in db["total_users"]:
        db["total_users"].append(uid)
        save_db(db)

    if uid in db["banned"]:
        return bot.send_message(message.chat.id, "❌ عذراً، لقد تم حظرك من استخدام البوت.")

    if not is_subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ اشترك في القناة", url=CHANNEL_LINK))
        return bot.send_message(message.chat.id, "⚠️ يجب أن تشترك في القناة أولاً لفتح ميزات البوت!", reply_markup=kb)

    bot.send_message(message.chat.id, f"🚀 **أهلاً بك في منصة الاستضافة المتكاملة**\n\nبإمكانك إدارة ملفات البرمجة وتشغيلها 24/7 بسهولة.", 
                     parse_mode="Markdown", reply_markup=main_menu(uid))

# --- لوحة تحكم الأدمن ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id not in ADMIN_IDS: return
    db = load_db()
    
    stats_msg = (
        "⚙️ **لوحة تحكم المدير**\n\n"
        f"👥 عدد المستخدمين: {len(db['total_users'])}\n"
        f"🚫 المحظورين: {len(db['banned'])}\n"
        f"🔥 العمليات النشطة: {len(running_procs)}\n"
        f"📂 إجمالي الملفات: يتم الفحص..."
    )
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📢 إذاعة (إرسال للكل)", callback_data="broadcast"),
        types.InlineKeyboardButton("❌ حظر مستخدم", callback_data="ban_user"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
    )
    bot.edit_message_text(stats_msg, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# --- نظام الرفع والموافقة ---
@bot.callback_query_handler(func=lambda c: c.data == "upload")
def upload_start(call):
    msg = bot.send_message(call.message.chat.id, "📤 أرسل ملف البايثون (`.py`) الآن:")
    bot.register_next_step_handler(msg, save_file_step)

def save_file_step(message):
    if not message.document or not message.document.file_name.endswith(".py"):
        return bot.send_message(message.chat.id, "❌ خطأ: يرجى إرسال ملف بصيغة .py فقط.")
    
    uid = str(message.from_user.id)
    fname = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    data = bot.download_file(file_info.file_path)
    
    user_path = os.path.join(UPLOAD_DIR, uid)
    if not os.path.exists(user_path): os.makedirs(user_path)
    
    full_path = os.path.join(user_path, fname)
    with open(full_path, "wb") as f: f.write(data)
    
    db = load_db()
    if uid not in db["users"]: db["users"][uid] = {}
    db["users"][uid][fname] = {"status": "pending", "path": full_path, "time": str(datetime.datetime.now())}
    save_db(db)

    bot.send_message(message.chat.id, "✅ تم الرفع! بانتظار موافقة الإدارة...")
    
    for admin in ADMIN_IDS:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{uid}_{fname}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"decline_{uid}_{fname}"))
        bot.send_document(admin, data, caption=f"📥 طلب جديد من: {uid}\nاسم الملف: {fname}", reply_markup=kb)

# --- نظام الإذاعة (للمدير) ---
@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast_prompt(call):
    msg = bot.send_message(call.message.chat.id, "📢 أرسل الرسالة التي تريد توجيهها للكل:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    db = load_db()
    count = 0
    for user in db["total_users"]:
        try:
            bot.send_message(user, f"📢 **إشعار من الإدارة:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except: continue
    bot.send_message(message.chat.id, f"✅ تمت الإذاعة لـ {count} مستخدم.")

# --- تشغيل وإيقاف الملفات ---
@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    data = call.data
    db = load_db()

    if data.startswith("accept_"):
        _, target_uid, fname = data.split("_")
        db["users"][target_uid][fname]["status"] = "approved"
        save_db(db)
        bot.send_message(target_uid, f"✅ تمت الموافقة على ملفك: {fname}")
        bot.answer_callback_query(call.id, "تم القبول")

    elif data == "my_files":
        files = db["users"].get(uid, {})
        if not files: return bot.answer_callback_query(call.id, "لا توجد ملفات.")
        kb = types.InlineKeyboardMarkup()
        for f in files:
            kb.add(types.InlineKeyboardButton(f"📄 {f}", callback_data=f"manage_{f}"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text("📂 ملفاتك المرفوعة:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif data.startswith("manage_"):
        fname = data.split("_")[1]
        status = db["users"][uid][fname]["status"]
        kb = types.InlineKeyboardMarkup()
        if status == "approved":
            kb.add(types.InlineKeyboardButton("▶️ تشغيل", callback_data=f"run_{fname}"),
                   types.InlineKeyboardButton("⏹ إيقاف", callback_data=f"stop_{fname}"))
        kb.add(types.InlineKeyboardButton("🗑️ حذف الملف", callback_data=f"del_{fname}"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="my_files"))
        bot.edit_message_text(f"📄 ملف: {fname}\nالحالة: {status}", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif data.startswith("run_"):
        fname = data.split("_")[1]
        path = db["users"][uid][fname]["path"]
        if path in running_procs: return bot.answer_callback_query(call.id, "يعمل بالفعل!")
        
        proc = subprocess.Popen([sys.executable, path])
        running_procs[path] = proc
        bot.answer_callback_query(call.id, "🚀 انطلق البوت!")

    elif data == "back_home":
        bot.edit_message_text("🏠 القائمة الرئيسية", call.message.chat.id, call.message.message_id, reply_markup=main_menu(int(uid)))

# --- التشغيل النهائي ---
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("✅ System Online...")
    bot.infinity_polling()
