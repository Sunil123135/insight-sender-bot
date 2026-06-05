/**
 * Bootstrap Neon when local port 5432 is blocked (uses WebSocket over 443).
 * Usage: node scripts/setup_neon_remote.mjs
 */
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { neonConfig, Pool } from "@neondatabase/serverless";
import ws from "ws";

const root = dirname(fileURLToPath(import.meta.url));

function loadDatabaseUrl() {
  const fromEnv = process.env.DATABASE_URL;
  if (fromEnv) {
    return fromEnv.replace(/^postgresql\+psycopg:\/\//, "postgresql://");
  }
  const envFile = readFileSync(join(root, "..", ".env"), "utf8");
  const line = envFile.split(/\r?\n/).find((row) => row.startsWith("DATABASE_URL="));
  if (!line) {
    throw new Error("DATABASE_URL not found in .env");
  }
  return line
    .slice("DATABASE_URL=".length)
    .replace(/^"/, "")
    .replace(/"$/, "")
    .replace(/^postgresql\+psycopg:\/\//, "postgresql://");
}

function parseSqlStatements(raw) {
  const skipPrefixes = [
    "INFO ",
    "Purpose:",
    "Author:",
    "Created:",
    "Module:",
  ];
  const cleaned = raw
    .split("\n")
    .filter((line) => !skipPrefixes.some((prefix) => line.startsWith(prefix)))
    .join("\n");
  return cleaned
    .split(";")
    .map((part) => part.trim())
    .filter((part) => part && part !== "BEGIN" && part !== "COMMIT");
}

async function runStatements(pool, statements, label) {
  console.log(`Running ${statements.length} ${label} statements...`);
  for (const statement of statements) {
    const preview =
      statement
        .split("\n")
        .find((line) => line.trim() && !line.startsWith("--"))
        ?.trim() ?? statement;
    console.log(`- ${preview.slice(0, 80)}`);
    try {
      await pool.query(statement);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (message.includes("already exists")) {
        console.log("  (skipped: already exists)");
        continue;
      }
      throw error;
    }
  }
}

async function main() {
  neonConfig.webSocketConstructor = ws;
  const pool = new Pool({ connectionString: loadDatabaseUrl() });

  try {
    const existing = await pool.query(
      "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'articles'",
    );
    if (existing.rowCount === 0) {
      const schema = readFileSync(join(root, "schema.sql"), "utf8");
      await runStatements(pool, parseSqlStatements(schema), "schema");
    } else {
      console.log("Schema already present; skipping migration SQL.");
    }

    const seedExport = spawnSync(
      "python",
      ["-m", "poetry", "run", "python", "scripts/export_seed_sql.py"],
      { cwd: join(root, ".."), encoding: "utf8" },
    );
    if (seedExport.status !== 0) {
      throw new Error(seedExport.stderr || "Failed to export seed SQL");
    }
    await runStatements(pool, parseSqlStatements(seedExport.stdout), "seed");

    const tables = await pool.query(
      "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename",
    );
    const sources = await pool.query("SELECT COUNT(*)::int AS count FROM source_configs");
    const keywords = await pool.query("SELECT COUNT(*)::int AS count FROM keywords_master");
    console.log("Tables:", tables.rows.map((row) => row.tablename).join(", "));
    console.log(`Seeded rows: sources=${sources.rows[0].count}, keywords=${keywords.rows[0].count}`);
  } finally {
    await pool.end();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
