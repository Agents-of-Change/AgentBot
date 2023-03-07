import discord
import functools
import re
from config import ADMIN_ROLE_ID, GUILD_ID

intents = discord.Intents.default()
# intents.message_content = True
bot = discord.Bot(intents=intents, auto_sync_commands=False)
guild_slash_command = functools.partial(bot.slash_command, guild_ids=[GUILD_ID])


def is_admin(author):
    return any(r.id == ADMIN_ROLE_ID for r in author.roles)


def mention(discord_id):
    return f"<@{discord_id}>"


def admin_only(func):
    @functools.wraps(func)
    async def decorated(ctx, *args, **kwargs):
        if not is_admin(ctx.author):
            await ctx.respond("You do not have the required role")
            return
        return await func(ctx, *args, **kwargs)

    return decorated


def id_from_mention(mention):
    m = re.match(r"<@!?([0-9]{15,20})>$", mention)
    if m is None:
        raise ValueError(f"Value is not a mention: {mention!r}")
    return int(m.group(1))
