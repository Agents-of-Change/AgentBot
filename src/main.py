import discord
from config import TOKEN, GUILD_ID
from db import sqlite3, db

intents = discord.Intents.default()
# intents.message_content = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.slash_command(guild_ids=[GUILD_ID])
async def hello(ctx):
    await ctx.respond("Hello!")


async def one_on_ones_join(ctx):
    db.execute(
        """
            INSERT INTO users (discordId, matchable) 
                VALUES (?, TRUE)
            ON CONFLICT(discordId) DO UPDATE SET
                matchable = TRUE
        """, 
        (str(ctx.author.id), )
    )
    db.commit()
    await ctx.respond("You are now signed up for one-on-ones")

async def one_on_ones_leave(ctx):
    db.execute(
        """
            UPDATE users SET matchable = FALSE WHERE discordId = ?
        """,
        (str(ctx.author.id), )
    )
    db.commit()
    await ctx.respond("You are no longer signed up for one-on-ones")


@bot.slash_command(guild_ids=[GUILD_ID])
async def one_on_ones(
    ctx,
    action: discord.Option(
        input_type=discord.SlashCommandOptionType.sub_command, choices=["join", "leave"]
    ),
):
    if action == "join":
        return await one_on_ones_join(ctx)
    if action == "leave":
        return await one_on_ones_leave(ctx)
    await ctx.respond("Invalid option")


bot.run(TOKEN)
