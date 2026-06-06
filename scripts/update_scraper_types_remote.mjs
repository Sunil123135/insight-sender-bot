/**
 * Update legacy scraper types on Neon when local PostgreSQL port 5432 is blocked.
 * Usage: node scripts/update_scraper_types_remote.mjs
 */
import { readFileSync } from "node:fs";
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

async function main() {
  neonConfig.webSocketConstructor = ws;
  const pool = new Pool({ connectionString: loadDatabaseUrl() });
  try {
    const result = await pool.query(`
      UPDATE source_configs
      SET scraper_type = 'chain', updated_at = NOW()
      WHERE scraper_type IN ('apify', 'firecrawl', 'jina')
        AND source_key <> 'arxiv_supply_chain_ai'
    `);
    console.log(`Updated ${result.rowCount ?? 0} source_configs rows to scraper_type=chain`);
  } finally {
    await pool.end();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
