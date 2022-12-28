import discord
from config import TOKEN, GUILD_ID, INCOMPATIBILITIES
from db import sqlite3, db
from collections import defaultdict
import random

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
        (str(ctx.author.id),),
    )
    db.commit()
    await ctx.respond("You are now signed up for one-on-ones")


async def one_on_ones_leave(ctx):
    db.execute(
        """
            UPDATE users SET matchable = FALSE WHERE discordId = ?
        """,
        (str(ctx.author.id),),
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


def index_past_matches():
    past_matches = defaultdict(lambda: defaultdict(lambda: 0))
    cur = db.cursor()
    cur.execute("SELECT personA, personB FROM past_matches")
    for person_a_id, person_b_id in cur.fetchall():
        past_matches[person_a_id][person_b_id] += 1
        past_matches[person_b_id][person_a_id] += 1
    return past_matches


def discord_id_to_uid(discord_id):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE discordId = ?", (str(discord_id),))
    r = cur.fetchone()
    if r is None:
        raise AssertionError(f"No user with discordId {discord_id!r}")
    return r[0]


def index_incompatibilities():
    incompatibilites = defaultdict(lambda: defaultdict(lambda: False))
    for a, b in INCOMPATIBILITIES:
        a = discord_id_to_uid(a)
        b = discord_id_to_uid(b)
        incompatibilites[a][b] = True
        incompatibilites[b][a] = True
    return incompatibilites


def matches_for_user(past_matches, incompatibilities, matchable_ids, person_id):
    r = [
        uid
        for uid in matchable_ids
        if uid != person_id and not incompatibilities[person_id][uid]
    ]
    min_past_matches = min(past_matches[person_id][uid] for uid in r)
    return set(uid for uid in r if past_matches[person_id][uid] <= min_past_matches)


def generate_matches():
    past_matches = index_past_matches()
    incompatibilities = index_incompatibilities()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE matchable = TRUE")
    matchable_ids = [i[0] for i in cur.fetchall()]
    # This might help avoid the same people not getting picked every time
    random.shuffle(matchable_ids)

    matches = []
    unmatched = []
    matched = set()
    for uid in matchable_ids:
        if uid in matched:
            continue
        possible_matches = matches_for_user(
            past_matches, incompatibilities, matchable_ids, uid
        )
        possible_matches -= matched  # remove all items in matched from the set
        possible_matches = list(possible_matches)
        if not possible_matches:
            unmatched.append(uid)
            continue
        match = random.choice(possible_matches)
        matches.append((uid, match))
        matched.add(uid)
        matched.add(match)
    return matches, unmatched


def write_matches(matches):
    db.executemany("INSERT INTO past_matches (personA, personB) VALUES (?, ?)", matches)
    db.commit()


def fetch_many_discord_ids(uids):
    cur = db.cursor()
    out = []
    for i in uids:
        print(i, type(i))
        db.execute("SELECT discordId FROM users WHERE id = ?", (i, ))
        r = cur.fetchone()
        if r is None:
            raise AssertionError(f"Invalid UID: {i}")
        out.append(r[0])
    return out


def matches_with_discord_ids(matches):
    uids = []
    for a, b in matches:
        uids.append(a)
        uids.append(b)
    discord_ids = fetch_many_discord_ids(uids)
    uid_to_discord_id = dict(zip(uids, discord_ids))
    return [(uid_to_discord_id[a], uid_to_discord_id[b]) for a, b in matches]


async def can_roll_one_on_ones(author):
    # TODO: Role check
    return True


def mention(discord_id):
    return f"<@{discord_id}>"


@bot.slash_command(guild_ids=[GUILD_ID])
async def roll_one_on_ones(ctx):
    matches, unmatched = generate_matches()
    discord_matches = matches_with_discord_ids(matches)
    msg = ["New pairings!", ""]
    msg += [mention(a) + " <-> " + mention(b) for a, b in discord_matches]
    if unmatched:
        msg += [
            "",
            "Unmatched: "
            + " ".join(mention(i) for i in fetch_many_discord_ids(unmatched)),
        ]
    write_matches(matches)
    await ctx.send_response("\n".join(msg), allowed_mentions=discord.AllowedMentions(users=False))


bot.run(TOKEN)
