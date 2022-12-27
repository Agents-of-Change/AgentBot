import {
  ActivityType,
  CacheType,
  ChatInputCommandInteraction,
} from "discord.js";
import { COMMANDS } from "../allCommands";
import { client } from "../client";
import { CONFIG } from "../config";
import { CommandType } from "../types";

const commandsMap: Map<string, CommandType> = new Map();
for (const cmd of COMMANDS) {
  commandsMap.set(cmd.meta.name, cmd);
}

async function handleCommandError(
  interaction: ChatInputCommandInteraction<CacheType>,
  e: any
) {
  console.error(`Error in command ${interaction.commandName}`, e);
  const msg = "An unexpected error occurred while running that command";
  if (interaction.deferred || interaction.replied) {
    await interaction.editReply(msg);
  } else {
    await interaction.reply(msg);
  }
}

client.on("interactionCreate", async (interaction) => {
  if (interaction.isCommand() && interaction.isChatInputCommand()) {
    const cmd = await commandsMap.get(interaction.commandName);
    if (!cmd) return;
    try {
      await cmd.handler(interaction);
    } catch (e) {
      await handleCommandError(interaction, e);
    }
  }
});

client.on("ready", async () => {
  console.log(`Sucessfully logged in as ${client.user!.tag}`);
  client.user!.setActivity("the discord", { type: ActivityType.Watching });
});

async function main() {
  console.log("Starting bot...");
  await client.login(CONFIG.TOKEN);
}

main();
