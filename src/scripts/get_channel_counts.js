/**
 * Get token from authorization header in devtools network tab (in minecraft)
 * Get channel_ids from bot using dump_channel_ids.py and fill that variable in
 * Run this script in discord.com JS console (in minecraft)
 */

(async function () {
  const guildId = "GUILD_ID_HERE";
  async function countMsgs(cid) {
    const r = await fetch(
      `https://discord.com/api/v9/guilds/${guildId}/messages/search?channel_id=${cid}`,
      { headers: { authorization: "TOKEN_HERE" } }
    );
    if (r.status != 200) throw new Error("status " + r.status);
    const j = await r.json();
    return j["total_results"];
  }
  r = {};
  channel_ids = [
    /* fill in from dump_channel_ids.py */
  ];
  sleep = (t) => new Promise((r) => setTimeout(r, t));
  for (const cid of channel_ids) {
    console.log(cid);
    try {
      const count = await countMsgs(cid);
      console.log(count);
      r[cid] = count;
    } catch (e) {
      // ignore errors because I kept getting 403 errors from channels the bot has
      //  access to but my account doesn't or non-text channels
      console.error(e);
    }
    await sleep(500);
  }
  console.log(JSON.stringify(r));
})();
