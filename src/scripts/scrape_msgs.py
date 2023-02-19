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
client = discord.Client()
_, guild_id, counts_json, db_filename = sys.argv
guild_id = int(guild_id)
with open(counts_json, "rb") as f:
    counts_json = json.load(f)
db = sqlite3.connect(db_filename)

db.execute("PRAGMA foreign_keys = ON;")
db.execute(
    """
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discordId TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL
    )
    """
)
db.execute(
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channelId INTEGER NOT NULL,
        threadId INTEGER,
        discordId TEXT NOT NULL UNIQUE,
        authorDiscordId TEXT NOT NULL,
        content TEXT,

        FOREIGN KEY (channelId)
            REFERENCES channels (id)
    )
    """
)
db.commit()


def should_scrape_channel():
    return True


async def scrape_channel():
    pass


async def count_messages(chan: discord.TextChannel):
    params = {"channel_id": chan.id}
    r = await chan._state.http.request(
        discord.Route(
            "GET",
            "/guilds/{guild_id}/messages/search",
            guild_id=chan.guild.id,
        )
    )
    return r["total_results"]


async def main():
    print("Fetching guild...")
    guild = await client.fetch_guild(guild_id)
    print("Fetching channels...")
    channels = await guild.fetch_channels()
    print(f"...fetched {len(channels)} channels")
    with tqdm(total=sum(counts_json.values())) as pbar:
        for channel in channels:
            if not isinstance(channel, discord.abc.Messageable):
                pbar.write(f"Skipping channel {channel.name} ({channel.id})")
                continue
            pbar.write(f"Processing channel {channel.name} ({channel.id})")
            pbar.set_postfix(channel=channel.name)
            cur = db.cursor()
            cur.execute(
                "INSERT INTO channels (discordId, name) VALUES (?, ?)",
                (channel.id, channel.name),
            )
            cid = cur.lastrowid
            db.commit()
            msgs = []
            try:
                async for msg in channel.history(limit=None):
                    msgs.append((cid, None, msg.id, msg.author.id, msg.content))
                    pbar.update(1)
                async for thread in channel.archived_threads(limit=None):
                    async for msg in thread.history(limit=None):
                        msgs.append(
                            (cid, thread.id, msg.id, msg.author.id, msg.content)
                        )
                        pbar.update(1)
            except discord.errors.Forbidden as e:
                pbar.write(f"Forbidden: {e!r}")
            db.executemany(
                """
                INSERT INTO
                    messages (channelId, threadId, discordId, authorDiscordId, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                msgs,
            )
            db.commit()
            pbar.write(f"Wrote {len(msgs)} msgs")
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
