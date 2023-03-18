import sys
import sqlite3
import logging

import discord
from tqdm import tqdm
import json

from hack_path import hack_path

hack_path()
from config import TOKEN

logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
_, guild_id, counts_json, db_filename = sys.argv
guild_id = int(guild_id)
with open(counts_json, "rb") as f:
    counts_json = json.load(f)
db = sqlite3.connect(db_filename)

db.execute("PRAGMA foreign_keys = ON;")
db.execute(
    """
    CREATE TABLE IF NOT EXISTS threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discordId TEXT UNIQUE,
        channelDiscordId TEXT NOT NULL,
        name TEXT NOT NULL
    )
    """
)
db.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discordId TEXT UNIQUE,
        nickname TEXT,
        username TEXT NOT NULL,
        discriminator TEXT NOT NULL,
        profileUrl TEXT NOT NULL
    )
    """
)
db.execute(
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        threadId INTEGER NOT NULL,
        discordId TEXT NOT NULL UNIQUE,
        authorDiscordId TEXT NOT NULL,
        content TEXT,

        FOREIGN KEY (channelId)
            REFERENCES channels (id)
    )
    """
)
db.commit()


def commit_writes(pbar, msgs, authors):
    db.executemany(
        """
        INSERT INTO
            messages (threadId, discordId, authorDiscordId, content)
        VALUES (?, ?, ?, ?)
        """,
        msgs,
    )
    db.executemany(
        """
        INSERT INTO
            users (discordId, nickname, username, discriminator, profileUrl)
        VALUES (?, ?, ?, ?, ?)
        """,
        authors,
    )
    db.commit()
    pbar.write(f"Wrote {len(msgs)} msgs, {len(authors)} authors")


async def proc_thread(pbar: tqdm, seen_authors, thread: discord.Thread):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO threads (discordId, channelDiscordId, name) VALUES (?, ?, ?)",
        (thread.id, thread.parent_id, thread.name),
    )
    tid = cur.lastrowid
    db.commit()
    msgs = []
    authors = []
    async for msg in thread.history(limit=None):
        if msg.author.id not in seen_authors:
            seen_authors.add(msg.author.id)
            authors.append(
                (
                    msg.author.id,
                    msg.author.nick,
                    msg.author.name,
                    msg.author.discriminator,
                    msg.author.display_avatar.url,
                )
            )
        msgs.append((tid, msg.id, msg.author.id, msg.content))
        pbar.update(1)
    commit_writes(pbar, msgs, authors)


async def proc_channel(pbar: tqdm, seen_authors, channel: discord.TextChannel):
    if not isinstance(channel, discord.abc.Messageable):
        pbar.write(f"Skipping channel {channel.name} ({channel.id})")
        return
    pbar.write(f"Processing channel {channel.name} ({channel.id})")
    pbar.set_postfix(channel=channel.name)
    cur = db.cursor()
    cur.execute(
        "INSERT INTO threads (discordId, channelDiscordId, name) VALUES (?, ?, ?)",
        (None, channel.id, channel.name),
    )
    cid = cur.lastrowid
    db.commit()
    msgs = []
    authors = []
    try:
        async for msg in channel.history(limit=None):
            if msg.author.id not in seen_authors:
                seen_authors.add(msg.author.id)
                authors.append(
                    (
                        msg.author.id,
                        msg.author.nick,
                        msg.author.name,
                        msg.author.discriminator,
                        msg.author.display_avatar.url,
                    )
                )
            msgs.append((cid, msg.id, msg.author.id, msg.content))
            pbar.update(1)
        async for thread in channel.archived_threads(limit=None):
            await proc_thread(pbar, seen_authors, thread)
    except discord.errors.Forbidden as e:
        pbar.write(f"Forbidden: {e!r}")
    except AttributeError as e:
        if str(e) != "'VoiceChannel' object has no attribute 'archived_threads'":
            raise e
    commit_writes(pbar, authors, msgs)


async def main():
    print("Fetching guild...")
    guild = await client.fetch_guild(guild_id)
    print("Fetching channels...")
    channels = await guild.fetch_channels()
    threads = await guild.active_threads()
    print(f"...fetched {len(channels)} channels, {len(threads)} active threads")
    authors = set()
    with tqdm(total=sum(counts_json.values())) as pbar:
        for channel in channels:
            await proc_channel(pbar, authors, channel)
        for thread in threads:
            await proc_thread(pbar, authors, thread)
    print("Done!")


main_started = False


@client.event
async def on_connect():
    global main_started
    if not main_started:
        main_started = True
        await main()
        await client.close()


if __name__ == "__main__":
    client.run(TOKEN)
