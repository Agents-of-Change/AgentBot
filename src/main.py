import logging
from sqlite3 import OperationalError
import asyncio
from web import start_app
from config import TOKEN, GUILD_ID
from utils import *
from one_on_ones import *


logging.basicConfig(level=logging.DEBUG)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.event
async def on_connect():
    try:
        print("Syncing commands...")
        await bot.sync_commands()
        print("Sync done")
    except Exception:
        logging.exception("Error while syncing commands")


@guild_slash_command()
async def hello(ctx):
    await ctx.respond("Hello!")


@bot.user_command(name="Jump to Introduction", guild_ids=[GUILD_ID])
async def jump_to_introduction(ctx, member):
    await ctx.respond(f"Hello world! <@{member.id}>")


def check_db_conn():
    try:
        db.execute("SELECT 1 FROM users")
        db.execute("SELECT 1 FROM past_matches")
    except OperationalError as e:
        raise AssertionError(
            "Error: DB not setup properly. Run scripts/db_setup.py"
        ) from e


async def main():
    check_db_conn()
    await start_app()
    try:
        await bot.start(TOKEN)
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
