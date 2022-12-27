import { z } from "zod";

const schema = z.object({
  TOKEN: z.string(),
  DATABASE_FILENAME: z.string(),
});
export const CONFIG = schema.parse(process.env);
