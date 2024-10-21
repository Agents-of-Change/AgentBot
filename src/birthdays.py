from datetime import date
from db import db
from utils import bot, mention
from config import GUILD_ID

async def check_birthdays():
    today = date.today()
    cur = db.cursor()
    cur.execute("""
        SELECT u.discordId, b.birthday
        FROM birthdays b
        JOIN users u ON b.user_id = u.id
        WHERE strftime('%m-%d', b.birthday) = ?
    """, (today.strftime('%m-%d'),))
    
    birthdays = cur.fetchall()
    
    if not birthdays:
        return
    
    guild = bot.get_guild(GUILD_ID)
    general_channel = discord.utils.get(guild.text_channels, name="general")
    
    for discord_id, birthday in birthdays:
        age = today.year - birthday.year
        await channel.send(f"Happy {age}th birthday, {mention(discord_id)}! 🎉🎂")

async def add_birthday(discord_id: str, birthday: date):
    user_id = db.execute("SELECT id FROM users WHERE discordId = ?", (discord_id,)).fetchone()[0]
    db.execute("INSERT OR REPLACE INTO birthdays (user_id, birthday) VALUES (?, ?)", (user_id, birthday))
    db.commit()