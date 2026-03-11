import telebot
import json
import time
import random
import schedule
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8751822734:AAGm-ULu8vBX5ChKlgIw1NTau242_7L6uvw"
bot = telebot.TeleBot(TOKEN)

DB_FILE = "database.json"

# ---------------- DATABASE ----------------

def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except:
        return {
            "groups": [],
            "badwords": ["spam","scam"],
            "warnings": {},
            "welcome":"👋 Welcome {name} to {group}",
            "goodbye":"👋 Goodbye {name}"
        }

def save_db(data):
    with open(DB_FILE,"w") as f:
        json.dump(data,f,indent=2)

db = load_db()

# ---------------- START ----------------

@bot.message_handler(commands=["start"])
def start(m):

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("➕ Add to Group",
        url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    )

    kb.add(
        InlineKeyboardButton("⚙ Settings",callback_data="settings")
    )

    bot.send_message(
        m.chat.id,
        "🤖 Group Manager Bot\n\nI help manage Telegram groups.",
        reply_markup=kb
    )

# ---------------- SETTINGS PANEL ----------------

@bot.callback_query_handler(func=lambda c: c.data=="settings")
def settings(c):

    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("👋 Welcome","welcome"),
        InlineKeyboardButton("👋 Goodbye","goodbye")
    )

    kb.add(
        InlineKeyboardButton("🚫 Badwords","bad"),
        InlineKeyboardButton("⚠ Warns","warn")
    )

    kb.add(
        InlineKeyboardButton("🌙 Night Mode","night"),
        InlineKeyboardButton("📊 Stats","stats")
    )

    kb.add(
        InlineKeyboardButton("❌ Close","close")
    )

    bot.edit_message_text(
        "⚙ SETTINGS PANEL",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb
    )

# ---------------- WELCOME ----------------

@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):

    text = db["welcome"]

    for user in m.new_chat_members:

        msg = text.replace("{name}",user.first_name)\
                  .replace("{group}",m.chat.title)

        bot.send_message(m.chat.id,msg)

# ---------------- GOODBYE ----------------

@bot.message_handler(content_types=["left_chat_member"])
def bye(m):

    text = db["goodbye"]

    name = m.left_chat_member.first_name

    bot.send_message(
        m.chat.id,
        text.replace("{name}",name)
    )

# ---------------- BAN ----------------

@bot.message_handler(commands=["ban"])
def ban(m):

    if not m.reply_to_message:
        return

    uid = m.reply_to_message.from_user.id

    bot.ban_chat_member(m.chat.id,uid)

    bot.send_message(m.chat.id,"🚫 User banned")

# ---------------- MUTE ----------------

@bot.message_handler(commands=["mute"])
def mute(m):

    if not m.reply_to_message:
        return

    uid = m.reply_to_message.from_user.id

    bot.restrict_chat_member(
        m.chat.id,
        uid,
        until_date=time.time()+3600
    )

    bot.send_message(m.chat.id,"🔇 Muted 1 hour")

# ---------------- WARN ----------------

@bot.message_handler(commands=["warn"])
def warn(m):

    if not m.reply_to_message:
        return

    uid = str(m.reply_to_message.from_user.id)

    if uid not in db["warnings"]:
        db["warnings"][uid] = 0

    db["warnings"][uid] += 1

    save_db(db)

    bot.send_message(
        m.chat.id,
        f"⚠ Warn {db['warnings'][uid]}/3"
    )

    if db["warnings"][uid] >= 3:

        bot.ban_chat_member(m.chat.id,int(uid))

        bot.send_message(m.chat.id,"🚫 User banned")

# ---------------- BAD WORD FILTER ----------------

@bot.message_handler(func=lambda m:True)
def filter_bad(m):

    for w in db["badwords"]:

        if w in m.text.lower():

            bot.delete_message(
                m.chat.id,
                m.message_id
            )

            bot.send_message(
                m.chat.id,
                "🚫 Bad word not allowed"
            )

            return

# ---------------- TAG ALL ----------------

@bot.message_handler(commands=["tagall"])
def tagall(m):

    bot.send_message(
        m.chat.id,
        "📢 Attention everyone!"
    )

# ---------------- STATS ----------------

@bot.message_handler(commands=["stats"])
def stats(m):

    members = bot.get_chat_members_count(m.chat.id)

    bot.send_message(
        m.chat.id,
        f"📊 Group Stats\nMembers: {members}"
    )

# ---------------- AUTO CHAT ----------------

def auto_chat():

    msgs = [
        "🔥 Who is active?",
        "😂 Send memes",
        "👀 Anyone online?",
        "💬 Let's talk!"
    ]

    for g in db["groups"]:

        try:
            bot.send_message(g,random.choice(msgs))
        except:
            pass

schedule.every(40).minutes.do(auto_chat)

# ---------------- GROUP ACTIVATE ----------------

@bot.message_handler(commands=["activate"])
def activate(m):

    gid = m.chat.id

    if gid not in db["groups"]:

        db["groups"].append(gid)

        save_db(db)

        bot.send_message(
            m.chat.id,
            "✅ Group activated"
        )

# ---------------- SCHEDULER ----------------

def scheduler():

    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=scheduler).start()

# ---------------- RUN ----------------

print("BOT STARTED")

bot.infinity_polling()
