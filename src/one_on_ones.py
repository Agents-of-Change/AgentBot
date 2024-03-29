from db import db
from collections import defaultdict
import random
import discord
from discord.ext.pages import Paginator, Page
from utils import *
from config import INCOMPATIBILITIES
import enum
import math
import asyncio


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


@guild_slash_command()
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


class NotRegisteredError(Exception):
    pass


def fetch_discord_id(uid):
    cur = db.cursor()
    cur.execute("SELECT discordId FROM users WHERE id = ?", (uid,))
    r = cur.fetchone()
    if r is None:
        raise NotRegisteredError(f"UID is not registered: {uid}")
    return r[0]


def fetch_many_discord_ids(uids):
    out = []
    for i in uids:
        out.append(fetch_discord_id(i))
    return out


def fetch_user_id(disc_id):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE discordId = ?", (str(disc_id),))
    r = cur.fetchone()
    if r is None:
        raise NotRegisteredError(f"Discord ID is not registered: {disc_id}")
    return r[0]


def index_incompatibilities():
    incompatibilites = defaultdict(lambda: defaultdict(lambda: False))
    for a, b in INCOMPATIBILITIES:
        a = fetch_user_id(a)
        b = fetch_user_id(b)
        incompatibilites[a][b] = True
        incompatibilites[b][a] = True
    return incompatibilites


def matches_for_user(past_matches, incompatibilities, matchable_ids, person_id):
    r = [
        uid
        for uid in matchable_ids
        if uid != person_id and not incompatibilities[person_id][uid]
    ]
    user_past_matches = [past_matches[person_id][uid] for uid in r]
    min_past_matches = min(user_past_matches) if len(user_past_matches) else 0
    return set(uid for uid in r if past_matches[person_id][uid] <= min_past_matches)


def generate_matches():
    seed = math.floor(asyncio.get_event_loop().time()) % 1000
    r = random.Random(seed)
    past_matches = index_past_matches()
    incompatibilities = index_incompatibilities()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE matchable = TRUE")
    matchable_ids = [i[0] for i in cur.fetchall()]
    # This might help avoid the same people not getting picked every time
    matches_by_len = defaultdict(lambda: [])
    for uid in matchable_ids:
        user_matches = matches_for_user(
            past_matches, incompatibilities, matchable_ids, uid
        )
        matches_by_len[len(user_matches)].append((uid, user_matches))

    for matches_len, users in matches_by_len.items():
        matches_by_len[matches_len] = r.sample(users, len(users))

    user_matches = []
    for k, users in sorted(matches_by_len.items(), key=lambda i: i[0]):
        user_matches += users

    matches = []
    unmatched = []
    matched = set()
    for uid, possible_matches in user_matches:
        if uid in matched:
            continue
        possible_matches -= matched  # remove all items in matched from the set
        possible_matches = list(possible_matches)
        if not possible_matches:
            unmatched.append(uid)
            continue
        match = r.choice(possible_matches)
        matches.append((uid, match))
        matched.add(uid)
        matched.add(match)
    return seed, matches, unmatched


def write_matches(matches):
    db.executemany(
        """
            INSERT INTO
                past_matches (date, personA, personB)
            VALUES (
                strftime('%Y-%m-%d', 'now'), ?, ?
            )
        """,
        matches,
    )
    db.commit()


def matches_with_discord_ids(matches):
    uids = []
    for a, b in matches:
        uids.append(a)
        uids.append(b)
    discord_ids = fetch_many_discord_ids(uids)
    uid_to_discord_id = dict(zip(uids, discord_ids))
    return [(uid_to_discord_id[a], uid_to_discord_id[b]) for a, b in matches]


@admin_guild_slash_command()
async def roll_one_on_ones(ctx):
    seed, matches, unmatched = generate_matches()
    discord_matches = matches_with_discord_ids(matches)
    msg = [f"New pairings! RNG seed: {seed}", ""]
    msg += [mention(a) + " <-> " + mention(b) for a, b in discord_matches]
    if unmatched:
        msg += [
            "",
            "Unmatched: "
            + " ".join(mention(i) for i in fetch_many_discord_ids(unmatched)),
        ]
    # Don't record matches yet, let them be manually recorded.
    # write_matches(matches)
    await ctx.send_response("\n".join(msg))


def auto_register_user(disc_id):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO users (discordId, matchable) VALUES (?, FALSE) RETURNING id",
        (disc_id,),
    )
    r = cur.fetchone()
    db.commit()
    return r[0]


@guild_slash_command(
    description="Record a 1-on-1 pairing. Invalid users will be automatically registered with matchable=False."
)
async def record_pair(
    ctx,
    user_a: discord.Option(input_type=discord.SlashCommandOptionType.user),
    user_b: discord.Option(input_type=discord.SlashCommandOptionType.user),
):
    user_a_discord, user_b_discord = map(id_from_mention, (user_a, user_b))
    if not any(
        (
            ctx.author.id == user_a_discord,
            ctx.author.id == user_b_discord,
            is_admin(ctx.author),
        )
    ):
        return await ctx.respond(
            "You must be an admin to record a match that does not involve you"
        )

    db_ids = []
    msgs = []
    for disc_id in (user_a_discord, user_b_discord):
        try:
            db_id = fetch_user_id(disc_id)
            msg = ""
        except NotRegisteredError:
            db_id = auto_register_user(disc_id)
            msg = " (auto registered)"
        db_ids.append(db_id)
        msgs.append(msg)

    user_a_id, user_b_id = db_ids
    user_a_msg, user_b_msg = msgs
    write_matches([(user_a_id, user_b_id)])
    await ctx.send_response(
        f":writing_hand: Recorded pair between {mention(user_a_discord)}{user_a_msg} and {mention(user_b_discord)}{user_b_msg}",
        allowed_mentions=discord.AllowedMentions.none(),
    )


@guild_slash_command(description="")
async def unrecord_pair(
    ctx,
    match_id: discord.Option(
        description="ID from match history",
        input_type=discord.SlashCommandOptionType.integer,
    ),
):
    try:
        match_id = int(match_id)
    except ValueError:
        return await ctx.respond("ID is not a valid integer", ephemeral=True)

    cur = db.execute(
        """
        SELECT
            date, uA.id, uA.discordId, uB.id, uB.discordId
        FROM past_matches m
        LEFT JOIN users uA ON m.personA = uA.id
        LEFT JOIN users uB ON m.personB = uB.id
        WHERE m.id = ?
        """,
        (match_id,),
    )
    r = cur.fetchone()
    if r is None:
        return await ctx.respond("Cannot find a match with that ID", ephemeral=True)
    date, user_a_id, user_a_discord, user_b_id, user_b_discord = r
    user_a_discord, user_b_discord = map(int, (user_a_discord, user_b_discord))

    if not any(
        (
            ctx.author.id == user_a_discord,
            ctx.author.id == user_b_discord,
            is_admin(ctx.author),
        )
    ):
        return await ctx.respond(
            "You must be an admin to unrecord a match that does not involve you. "
            + f"(You are trying to remove a match between {mention(user_a_discord)} and {mention(user_b_discord)})",
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=True,
        )

    # fine with this being destructive because it can be easily re-created
    db.execute(
        """
            DELETE FROM past_matches WHERE id = ?
        """,
        (match_id,),
    )
    return await ctx.send_response(
        f"Pairing ID {match_id} on {date} between {mention(user_a_discord)} and {mention(user_b_discord)} has been deleted.",
        allowed_mentions=discord.AllowedMentions.none(),
    )


def last_matches_paginated(page):
    limit = 10
    offset = limit * page
    cur = db.cursor()
    cur.execute(
        """
            SELECT
                m.id, date, uA.discordId, uB.discordId
            FROM past_matches m
            LEFT JOIN users uA ON uA.id = m.personA
            LEFT JOIN users uB ON uB.id = m.personB
            ORDER BY date, m.id DESC
            LIMIT ?
            OFFSET ?
        """,
        (limit, offset),
    )
    return cur.fetchall()


@guild_slash_command(description="List previous 1-1 pairings")
async def match_history(
    ctx: discord.context.ApplicationContext,
    user: discord.Option(
        input_type=discord.SlashCommandOptionType.user, required=False
    ),
):
    if user:
        user_discord = id_from_mention(user)
    else:
        user_discord = ctx.author.id
    try:
        user_id = fetch_user_id(user_discord)
    except NotRegisteredError:
        return await ctx.send_response(
            f"{user} is not signed up for 1-on-1s",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    cur = db.execute(
        """
        SELECT
            m.id, date, uA.discordId, uB.discordId
        FROM past_matches m
        LEFT JOIN users uA ON m.personA = uA.id
        LEFT JOIN users uB ON m.personB = uB.id
        WHERE m.personA = ? OR m.personB = ?
        ORDER BY date, m.id DESC
        """,
        (user_id, user_id),
    )
    matches = cur.fetchall()
    pages = []
    for start_i in range(0, len(matches), 15):
        lines = [
            f"{i + 1}. {mention(discord_a)} <-> {mention(discord_b)} (ID: {mid})"
            for i, (mid, date, discord_a, discord_b) in enumerate(
                matches[start_i : start_i + 15]
            )
        ]
        embed = discord.Embed(
            title="1-on-1s history",
            description="\n".join(lines),
        ).set_footer(
            text="Use `/unrecord_pair <ID>` to remove a match from your history"
        )
        pages.append(Page(embeds=[embed]))
    paginator = Paginator(pages=pages)
    await paginator.respond(
        ctx.interaction,
        ephemeral=False,
    )
