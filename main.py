import asyncio
import logging
import sys
import sqlite3
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

# Чтение токена из переменных окружения Bot-Host
TOKEN = os.getenv("TOKEN_BOT") 
CREATOR_ID = 5254144715

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("admin_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            warns INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username):
    conn = sqlite3.connect("admin_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins, warns FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, username, coins, warns) VALUES (?, ?, 0, 0)", (user_id, username))
        conn.commit()
        return 0, 0
    return row[0], row[1]

def update_db(user_id, username, field, value):
    conn = sqlite3.connect("admin_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {field} = ?, username = ? WHERE user_id = ?", (value, username, user_id))
    conn.commit()
    conn.close()

def is_creator(message: Message) -> bool:
    return message.from_user.id == CREATOR_ID

@dp.message(Command("coin"))
async def add_coins(message: Message, command: CommandObject):
    if not is_creator(message):
        return
    if not message.reply_to_message:
        await message.reply("❌ Эта команда должна быть ответом на сообщение пользователя!")
        return
    if not command.args or not command.args.isdigit():
        await message.reply("❌ Напишите число после команды, например: `/coin 50`", parse_mode="Markdown")
        return
        
    amount = int(command.args)
    target_user = message.reply_to_message.from_user
    username = f"@{target_user.username}" if target_user.username else target_user.full_name
    
    current_coins, warns = get_or_create_user(target_user.id, username)
    new_coins = current_coins + amount
    update_db(target_user.id, username, "coins", new_coins)
    
    await message.reply(f"📝 Администратору {username} зачислено {amount} A-Coins! Текущий баланс: {new_coins}")

@dp.message(Command("take"))
async def take_coins(message: Message, command: CommandObject):
    if not is_creator(message):
        return
    if not message.reply_to_message:
        await message.reply("❌ Эта команда должна быть ответом на сообщение пользователя!")
        return
    if not command.args or not command.args.isdigit():
        await message.reply("❌ Напишите число после команды, например: `/take 50`", parse_mode="Markdown")
        return
        
    amount = int(command.args)
    target_user = message.reply_to_message.from_user
    username = f"@{target_user.username}" if target_user.username else target_user.full_name
    
    current_coins, warns = get_or_create_user(target_user.id, username)
    new_coins = max(0, current_coins - amount)
    update_db(target_user.id, username, "coins", new_coins)
    
    await message.reply(f"📝 У администратора {username} списано {amount} A-Coins! Текущий баланс: {new_coins}")

@dp.message(Command("awarn"))
async def add_warn(message: Message):
    if not is_creator(message):
        return
    if not message.reply_to_message:
        await message.reply("❌ Эта команда должна быть ответом на сообщение пользователя!")
        return
        
    target_user = message.reply_to_message.from_user
    username = f"@{target_user.username}" if target_user.username else target_user.full_name
    
    coins, current_warns = get_or_create_user(target_user.id, username)
    new_warns = min(5, current_warns + 1)
    update_db(target_user.id, username, "warns", new_warns)
    
    await message.reply(f"⚠️ Администратору {username} выдан A-Warn. Всего: {new_warns}/5.")

@dp.message(Command("unawarn"))
async def remove_warn(message: Message):
    if not is_creator(message):
        return
    if not message.reply_to_message:
        await message.reply("❌ Эта команда должна быть ответом на сообщение пользователя!")
        return
        
    target_user = message.reply_to_message.from_user
    username = f"@{target_user.username}" if target_user.username else target_user.full_name
    
    coins, current_warns = get_or_create_user(target_user.id, username)
    new_warns = max(0, current_warns - 1)
    update_db(target_user.id, username, "warns", new_warns)
    
    await message.reply(f"✅ С администратора {username} снят A-Warn. Всего: {new_warns}/5.")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
