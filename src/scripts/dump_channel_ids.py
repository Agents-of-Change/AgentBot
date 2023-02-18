import sys

import discord
import json

from hack_path import hack_path

hack_path()
from config import TOKEN

_, guild_id = sys.argv
client = discord.Client()


async def main():
    print("Fetching guild...")
    guild = await client.fetch_guild(guild_id)
    print("Fetching channels...")
    channels = await guild.fetch_channels()
    print(f"...fetched {len(channels)} channels")
    c = channels[0]
    print(json.dumps([str(c.id) for c in channels]))


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
