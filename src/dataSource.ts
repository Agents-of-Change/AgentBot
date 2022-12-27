import { DataSource } from "typeorm";
import { CONFIG } from "./config";

export const AppDataSource = new DataSource({
  type: "better-sqlite3",
  database: CONFIG.DATABASE_FILENAME,
})
