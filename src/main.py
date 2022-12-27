import discord
from .config import TOKEN, GUILD_ID

intents = discord.Intents.default()
#intents.message_content = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(guild_ids=[GUILD_ID])
async def hello(ctx):
    await ctx.respond("Hello!")



bot.run(TOKEN)
