from hack_path import hack_path

hack_path()
import discord
from db import db
from config import TOKEN, GUILD_ID
import sys
import logging
import traceback

client = discord.Client()
tags_filename = sys.argv[1]
with open(tags_filename, "r") as f:
    tags = f.readlines()
print(f"{len(tags)} tags")


async def main():
    discord_ids = []
    guild = [i for i in client.guilds if i.id == GUILD_ID][0]

    for tag in tags:
        tag = tag.strip()
        print(f"Processing: {tag!r}")
        name, discrim = tag.split("#")
        members = await guild.query_members(name, limit=1)
        members = [m for m in members if m.name == name and m.discriminator == discrim]
        if len(members) != 1:
            raise AssertionError(f"Cannot find member for tag: {tag!r}")
        member = members[0]
        discord_ids.append(member.id)

    print(f"Writing {len(discord_ids)} IDs into database...")
    cur = db.cursor()
    params = [(str(i),) for i in discord_ids]
    cur.executemany("INSERT INTO users (discordId, matchable) VALUES (?, TRUE)", params)
    db.commit()
    print(f"Done!")


@client.event
async def on_ready():
    try:
        await main()
    except:
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client.run(TOKEN)
