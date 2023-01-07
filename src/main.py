from config import TOKEN, GUILD_ID
from utils import *
from one_on_ones import *
from sqlite3 import OperationalError


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@guild_slash_command()
async def hello(ctx):
    await ctx.respond("Hello!")


@bot.user_command(name="Jump to Introduction", guild_ids=[GUILD_ID])
async def jump_to_introduction(ctx, member):
    await ctx.respond(f"Hello world! <@{member.id}>")


def main():
    try:
        db.execute("SELECT 1 FROM users")
        db.execute("SELECT 1 FROM past_matches")
    except OperationalError as e:
        raise AssertionError(
            "Error: DB not setup properly. Run scripts/db_setup.py"
        ) from e
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
