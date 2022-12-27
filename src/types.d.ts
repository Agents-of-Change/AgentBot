import {
  CacheType,
  ChatInputCommandInteraction,
  RESTPostAPIApplicationCommandsJSONBody,
} from "discord.js";

export interface CommandMeta {
  name: string;
  toJSON: () => RESTPostAPIApplicationCommandsJSONBody;
}

export type CommandType = {
  meta: CommandMeta;
  handler: (
    interaction: ChatInputCommandInteraction<CacheType>
  ) => Promise<void>;
};
