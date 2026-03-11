import telebot
import json
import time
import random
import schedule
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8751822734:AAGm-ULu8vBX5ChKlgIw1NTau242_7L6uvw"

bot = telebot.TeleBot(TOKEN)

DB = "database.json"

def load():
    with open(DB) as f:
        return json.load(f)

def save(data):
    with open(DB,"w") as f:
        json.dump(data,f,indent=2)

db = load()

# START

@bot.message_handler(commands=["start"])
def start(m):

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "➕ Add To Group",
            url=f"https://t.me/{bot.get_me().username}?startgroup=true"
        )
    )

    bot.send_message(
        m.chat.id,
        "🤖 Professional Group Manager Bot",
        reply_markup=kb
    )

# ACTIVATE GROUP

@bot.message_handler(commands=["activate"])
def activate(m):

    gid = m.chat.id

    if gid not in db["groups"]:

        db["groups"].append(gid)
        save(db)

        bot.send_message(
            gid,
            "✅ Bot activated in this group"
        )

# WELCOME

@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):

    text = db["welcome"]

    for u in m.new_chat_members:

        msg = text.replace("{name}",u.first_name)\
                  .replace("{group}",m.chat.title)

        bot.send_message(m.chat.id,msg)

# GOODBYE

@bot.message_handler(content_types=["left_chat_member"])
def bye(m):

    text = db["goodbye"]

    name = m.left_chat_member.first_name

    bot.send_message(
        m.chat.id,
        text.replace("{name}",name)
    )

# BAN

@bot.message_handler(commands=["ban"])
def ban(m):

    if not m.reply_to_message:
        return

    uid = m.reply_to_message.from_user.id

    bot.ban_chat_member(m.chat.id,uid)

    bot.send_message(m.chat.id,"🚫 User banned")

# MUTE

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

    bot.send_message(m.chat.id,"🔇 User muted")

# WARN

@bot.message_handler(commands=["warn"])
def warn(m):

    if not m.reply_to_message:
        return

    uid = str(m.reply_to_message.from_user.id)

    if uid not in db["warnings"]:
        db["warnings"][uid] = 0

    db["warnings"][uid] += 1

    save(db)

    bot.send_message(
        m.chat.id,
        f"⚠ Warn {db['warnings'][uid]}/3"
    )

    if db["warnings"][uid] >= 3:

        bot.ban_chat_member(m.chat.id,int(uid))

        bot.send_message(m.chat.id,"🚫 User banned")

# BAD WORD FILTER

@bot.message_handler(func=lambda m:True)
def filter_msg(m):

    if not m.text:
        return

    for w in db["badwords"]:

        if w in m.text.lower():

            bot.delete_message(
                m.chat.id,
                m.message_id
            )

            bot.send_message(
                m.chat.id,
                "🚫 Bad word detected"
            )

            return

# ANTI LINK

@bot.message_handler(func=lambda m:"http" in m.text if m.text else False)
def link_filter(m):

    if db["antilink"]:

        bot.delete_message(
            m.chat.id,
            m.message_id
        )

        bot.send_message(
            m.chat.id,
            "🚫 Links not allowed"
        )

# TAG ALL

@bot.message_handler(commands=["tagall"])
def tagall(m):

    bot.send_message(
        m.chat.id,
        "📢 Attention everyone!"
    )

# STATS

@bot.message_handler(commands=["stats"])
def stats(m):

    members = bot.get_chat_members_count(m.chat.id)

    bot.send_message(
        m.chat.id,
        f"📊 Members: {members}"
    )

# AI GROUP CHAT

def auto_chat():

    msgs = [

        "🔥 Who is active today?",
        "😂 Send memes",
        "👀 Anyone online?",
        "💬 Let's talk!",
        "🎉 Group seems quiet today"

    ]

    for g in db["groups"]:

        try:
            bot.send_message(
                g,
                random.choice(msgs)
            )
        except:
            pass

schedule.every(30).minutes.do(auto_chat)

def scheduler():

    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=scheduler).start()

print("BOT RUNNING")

bot.infinity_polling()
