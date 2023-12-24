import logging
from sqlite3 import OperationalError
import asyncio
from web import start_app
from config import (
    TOKEN,
    GUILD_ID,
    LOCKOUT_ROLE_ID,
    INTRODUCED_ROLE_ID,
    UNUPDATED_ROLE_ID,
    INTRODUCTIONS_CHANNEL_ID,
)
from utils import *
from one_on_ones import *
import time
import asyncio
import discord
import discord.errors
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)


async def background(every=10):
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
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
            try:
                user = await guild.fetch_member(user_id)
            except discord.errors.NotFound:
                pass
            await user.remove_roles(guild.get_role(role_id))

        db.executemany(
            "DELETE FROM timed_roles WHERE id = ?", ((_id,) for _id, _ in res)
        )


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    asyncio.create_task(background())
    asyncio.create_task(task_add_unupdated_role())


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
        if dur > 60 * 60 * 24 * 7:
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
        (lockout_end,) = db.execute(
            "SELECT remove_role_at FROM timed_roles WHERE id = ?", (id,)
        ).fetchone()
        await ctx.respond(f"You will be able to chat again <t:{lockout_end}:R>")
    except Exception as e:
        await ctx.respond(f"Error: {e}")


async def latest_intro_message(member_id: int):
    member_id = int(member_id)
    channel_id = INTRODUCTIONS_CHANNEL_ID
    channel = bot.get_channel(channel_id)

    introduction_message = await channel.history(limit=None, oldest_first=False).find(
        lambda m: m.author.id == member_id
        and m.channel.type == discord.ChannelType.text
    )
    return introduction_message


@bot.user_command(name="Jump to Introduction", guild_ids=[GUILD_ID])
async def jump_to_introduction(ctx, member):
    introduction_message = await latest_intro_message(member.id)

    if introduction_message:
        response = f"{member.mention}'s introduction: {introduction_message.jump_url}"
    else:
        response = f"{member.mention} has not posted an introduction message"

    await ctx.response.send_message(response, ephemeral=True)


async def task_add_unupdated_role():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    introduced_role = guild.get_role(INTRODUCED_ROLE_ID)
    unupdated_role = guild.get_role(UNUPDATED_ROLE_ID)
    print(f"Introduced role: {introduced_role.name!r}")
    print(f"Unupdated role: {unupdated_role.name!r}")

    if introduced_role is None:
        raise AssertionError("Role with INTRODUCED_ROLE_ID does not exist")
    if unupdated_role is None:
        raise AssertionError("Role with UNUPDATED_ROLE_ID does not exist")

    print("Scraping intros history")
    intros = {}
    intros_channel = bot.get_channel(INTRODUCTIONS_CHANNEL_ID)
    async for message in intros_channel.history(limit=None, oldest_first=True):
        dt = message.created_at
        if message.edited_at is not None:
            dt = message.edited_at
        intros[message.author.id] = datetime.now(timezone.utc) - dt

    old_len = len(intros)
    pairs = [(member, intros.get(member.id, timedelta.max)) for member in introduced_role.members]
    print(f"{old_len} introducted members, {len(pairs)} with role")

    for member, deltat in pairs:
        if deltat.days < 6 * 30:
            continue
        print(f"Adding role to {member.id} ({member.display_name!r}) deltat={deltat!r}")
        await member.add_roles(unupdated_role)

    print("done")


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
