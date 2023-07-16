import logging
from sqlite3 import OperationalError
import asyncio
from web import start_app
from config import TOKEN, GUILD_ID, LOCKOUT_ROLE_ID
from utils import *
from one_on_ones import *
import time
import asyncio
import discord

logging.basicConfig(level=logging.INFO)


async def background(every=10):
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(every)
        res = db.execute(
            "SELECT id, user_id, role_id FROM timed_roles WHERE role_id = ? AND remove_role_at < ?",
            (
                LOCKOUT_ROLE_ID,
                int(time.time()),
            ),
        )
        for _, user_id, role_id in res:
            guild = bot.get_guild(GUILD_ID)
            user = await guild.fetch_member(user_id)
            await user.remove_roles(guild.get_role(role_id))

        db.executemany("DELETE FROM timed_roles WHERE id = ?", ((_id,) for _id, _ in res))


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    asyncio.create_task(background())


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


@guild_slash_command()
async def lockout(ctx, duration: str):
    # Give them the lockout role
    await ctx.user.add_roles(ctx.guild.get_role(LOCKOUT_ROLE_ID))

    try:
        dur = parse_duration(duration)
        if dur < 10:
            raise ValueError("Duration must be at least 10 seconds")
        if dur > 60*60*24*7:
            raise ValueError("Duration must be less than 7 days")
    except ValueError as e:
        await ctx.respond(f"Error: {e}")
        return

    lockout_end = int(time.time()) + dur

    # Add the date for removing the role based on the time they specify to the db
    try:
        id = db.execute(
            """
            INSERT INTO timed_roles (user_id, role_id, remove_role_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET remove_role_at=MAX(excluded.remove_role_at, remove_role_at);
            """,
            (ctx.user.id, LOCKOUT_ROLE_ID, lockout_end),
        ).lastrowid
        lockout_end, = db.execute("SELECT remove_role_at FROM timed_roles WHERE id = ?", (id,)).fetchone()
        await ctx.respond(f"You will be able to chat again <t:{lockout_end}:R>")
    except Exception as e:
        await ctx.respond(f"Error: {e}")


@bot.user_command(name="Jump to Introduction", guild_ids=[GUILD_ID])
async def jump_to_introduction(ctx, member):
    # Replace with the ID of the #introductions channel
    channel_id = 1021569666398826586
    channel = bot.get_channel(channel_id)

    introduction_message = await channel.history(limit=None, oldest_first=True).find(
        lambda m: m.author == member and m.channel.type == discord.ChannelType.text
    )

    if introduction_message:
        response = f"{member.mention}'s introduction: {introduction_message.jump_url}"
    else:
        response = f"{member.mention} has not posted an introduction message"

    await ctx.response.send_message(response, ephemeral=True)


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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
