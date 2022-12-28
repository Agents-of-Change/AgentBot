from hack_path import hack_path

hack_path()
import discord
from db import db
from config import TOKEN, GUILD_ID
import sys
import logging
import traceback

client = discord.Client()
matches_filename = sys.argv[1]
with open(matches_filename, "r") as f:
    matches = f.readlines()
print(f"{len(matches)} tags")


def parse_tag(tag):
    if not tag.startswith("@"):
        raise AssertionError()
    tag = tag[1:]
    name, discrim = tag.split("#")
    return name, int(discrim)

async def query_member(guild, name, discrim):
    members = await guild.query_members(name)
    members = [m for m in members if m.name == name and m.discriminator == discrim]
    if len(members) != 1:
        raise AssertionError(f"Cannot find member for {name}#{discrim}")
    return members[0]

def uid_from_discord(discord_id):
    cur = db.cursor()
    db.execute("SELECT id FROM users WHERE discordId = ? LIMIT 1", (str(discord_id), ))
    r = cur.fetchone()
    if r is None:
        raise AssertionError(f"discord ID {discord_id} is not unique")
    return r

async def main():
    discord_ids = []
    guild = [i for i in client.guilds if i.id == GUILD_ID][0]
    past_matches = []

    for line in matches:
        print(f"Processing: {line!r}")
        a, b = line.split(" <-> ")
        a = await query_member(guild, *parse_tag(a))
        b = await query_member(guild, *parse_tag(b))
        a_id = uid_from_discord(a.id)
        b_id = uid_from_discord(b.id)
        past_matches.append((a_id, b_id))

    print("Writing to DB...")
    db.executemany("INSERT INTO past_matches (personA, personB) VALUES (?, ?)", past_matches)
    db.commit()
    print("Done!")

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
