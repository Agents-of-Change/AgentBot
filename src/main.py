from config import TOKEN, GUILD_ID
from utils import *


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@guild_slash_command
async def hello(ctx):
    await ctx.respond("Hello!")


@bot.user_command(name="Jump to Introduction", guild_ids=[GUILD_ID])
async def jump_to_introduction(ctx, member):
    await ctx.respond(f"Hello world! <@{member.id}>")


bot.run(TOKEN)
