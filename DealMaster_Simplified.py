
# DealMaster Telegram Bot

import telebot
from telebot import types
from datetime import datetime, timedelta
import sqlite3
import threading
import pytz

# --- CONFIGURATION ---
TOKEN = '8010650634:AAGClUpEvE_1NnsPA6qKETbfrD5CITUj5Fw'
CHANNEL_USERNAME = '@DealMaster_Official'
ADMIN_ID = 2095987863  # Replace with your Telegram user ID
IST = pytz.timezone('Asia/Kolkata')

bot = telebot.TeleBot(TOKEN)
conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()

# --- DATABASE SETUP ---
cursor.execute("""CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id TEXT,
    description TEXT,
    link TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    post_time TEXT,
    status TEXT
)""")

conn.commit()

# --- UTILITY FUNCTIONS ---

def is_admin(user_id):
    return user_id == ADMIN_ID

def convert_to_ist(dt):
    return IST.localize(dt)

def schedule_post(product_id, post_time):
    delay = (post_time - datetime.now(IST)).total_seconds()
    if delay > 0:
        threading.Timer(delay, post_product, args=[product_id]).start()
        return True
    return False

def post_product(product_id):
    cursor.execute("SELECT image_id, description, link FROM products WHERE id=?", (product_id,))
    row = cursor.fetchone()
    if not row:
        return
    image_id, description, link = row
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Buy Now", url=link))
    bot.send_photo(CHANNEL_USERNAME, photo=image_id, caption=description, reply_markup=markup)
    cursor.execute("UPDATE schedules SET status='posted' WHERE product_id=?", (product_id,))
    conn.commit()

# --- BOT COMMANDS AND HANDLERS ---

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 You are not authorized.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 Upload Product", "⏰ Schedule Post")
    bot.send_message(message.chat.id, "👋 Welcome Admin!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛒 Upload Product")
def upload_product(message):
    if not is_admin(message.from_user.id): return
    user_state[message.chat.id] = {'step': 'awaiting_image'}
    bot.send_message(message.chat.id, "📸 Please send the product image.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if not is_admin(message.from_user.id): return
    state = user_state.get(message.chat.id, {}).get('step')
    if state != 'awaiting_image':
        return
    file_id = message.photo[-1].file_id
    user_state[message.chat.id]['image_id'] = file_id
    user_state[message.chat.id]['step'] = 'awaiting_description'
    bot.send_message(message.chat.id, "✏️ Now send the product description.")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('step') == 'awaiting_description')
def handle_description(message):
    user_state[message.chat.id]['description'] = message.text
    user_state[message.chat.id]['step'] = 'awaiting_link'
    bot.send_message(message.chat.id, "🔗 Send the product link.")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('step') == 'awaiting_link')
def handle_link(message):
    chat_id = message.chat.id
    user_state[chat_id]['link'] = message.text

    data = user_state[chat_id]
    cursor.execute("INSERT INTO products (image_id, description, link) VALUES (?, ?, ?)",
                   (data['image_id'], data['description'], data['link']))
    conn.commit()
    bot.send_message(chat_id, "✅ Product saved successfully!")
    user_state.pop(chat_id, None)

@bot.message_handler(func=lambda m: m.text == "⏰ Schedule Post")
def ask_schedule_id(message):
    if not is_admin(message.from_user.id): return
    user_state[message.chat.id] = {'step': 'awaiting_schedule_id'}
    bot.send_message(message.chat.id, "🆔 Enter product ID to schedule:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('step') == 'awaiting_schedule_id')
def receive_schedule_id(message):
    chat_id = message.chat.id
    try:
        product_id = int(message.text)
        user_state[chat_id]['product_id'] = product_id
        user_state[chat_id]['step'] = 'awaiting_schedule_time'
        bot.send_message(chat_id, "⏳ Send post time in format `YYYY-MM-DD HH:MM` (IST):")
    except ValueError:
        bot.send_message(chat_id, "❌ Invalid ID. Please send a number.")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('step') == 'awaiting_schedule_time')
def receive_schedule_time(message):
    chat_id = message.chat.id
    try:
        post_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        post_time = IST.localize(post_time)
        product_id = user_state[chat_id]['product_id']
        cursor.execute("INSERT INTO schedules (product_id, post_time, status) VALUES (?, ?, ?)",
                       (product_id, post_time.isoformat(), 'scheduled'))
        conn.commit()
        scheduled = schedule_post(product_id, post_time)
        if scheduled:
            bot.send_message(chat_id, f"✅ Post scheduled for {post_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            bot.send_message(chat_id, "❌ Time must be in the future.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")
    user_state.pop(chat_id, None)

# --- RUN BOT ---
print("Bot is running...")
bot.polling(none_stop=True)
