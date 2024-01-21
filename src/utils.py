import discord
import functools
import re
from config import ADMIN_ROLE_ID, GUILD_ID

intents = discord.Intents.default()
# intents.message_content = True
# required for task_add_unupdated_role
intents.members = True
bot = discord.Bot(intents=intents, auto_sync_commands=False)
guild_slash_command = functools.partial(bot.slash_command, guild_ids=[GUILD_ID])

admin_group = bot.create_group("admin", "Admin commands")
admin_guild_slash_command = functools.partial(admin_group.command, guild_ids=[GUILD_ID])


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


def parse_duration(dur: str):
    "Parse a duration of the form 1h 2m 3s into a number of seconds"
    try:
        return sum(
            int(s[:-1]) * {"h": 60 * 60, "m": 60, "s": 1}[s[-1]]
            for s in dur.lower().split()
        )
    except Exception as e:
        raise ValueError(f"Invalid duration: {dur!r}. Format is 1h 20m 30s.") from e
