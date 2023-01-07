import discord
import functools
from config import ADMIN_ROLE_ID

intents = discord.Intents.default()
# intents.message_content = True
bot = discord.Bot(intents=intents)
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
        return func(*args, **kwargs)

    return decorated
