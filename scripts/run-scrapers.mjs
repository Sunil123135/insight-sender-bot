#!/usr/bin/env node
/**
 * Run all vendored Python/yt-dlp scrapers and output JSON + HTML.
 * Scrapers: yt-dlp, webScrapers, keep-up-daily, TrendingNews
 */
import { spawn } from "node:child_process";
import { writeFile, mkdir, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const OUT_DIR = join(ROOT, "output");
const SCRAPERS = join(ROOT, "scrapers");
const IS_WIN = process.platform === "win32";
const PY = IS_WIN ? "python" : "python3";
const PIP = IS_WIN ? "pip" : "pip3";

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, {
      cwd: opts.cwd ?? ROOT,
      shell: false,
      env: process.env,
    });
    let stdout = "";
    let stderr = "";
    proc.stdout?.on("data", (d) => (stdout += d));
    proc.stderr?.on("data", (d) => (stderr += d));
    proc.on("close", (code) => {
      if (code === 0) resolve({ stdout, stderr });
      else
        reject(
          new Error(`${cmd} ${args.join(" ")} exited ${code}: ${stderr.slice(0, 500)}`),
        );
    });
  });
}

async function runKeepUpDaily() {
  const kudDir = join(SCRAPERS, "keep-up-daily");
  await run(PIP, ["install", "-q", "-r", join(kudDir, "requirements.txt")]);
  try {
    await run(PY, ["-m", "scraper"], { cwd: kudDir });
  } catch (e) {
    console.warn("    keep-up-daily scraper warning:", e.message?.slice(0, 120));
  }
  const today = new Date().toISOString().slice(0, 10);
  const dataPath = join(kudDir, "data", `${today}.json`);
  try {
    const raw = await readFile(dataPath, "utf8");
    return { source: "keep-up-daily", data: JSON.parse(raw) };
  } catch {
    // Fall back to most recent data file
    const { readdir } = await import("node:fs/promises");
    const files = (await readdir(join(kudDir, "data"))).filter((f) => f.match(/^\d{4}-\d{2}-\d{2}\.json$/)).sort();
    if (files.length === 0) return { source: "keep-up-daily", data: { articles: [] } };
    const raw = await readFile(join(kudDir, "data", files[files.length - 1]), "utf8");
    return { source: "keep-up-daily", data: JSON.parse(raw) };
  }
}

async function runWebScrapers() {
  const script = join(SCRAPERS, "webScrapers", "scraper.py");
  await run(PIP, ["install", "-q", "requests", "beautifulsoup4"]);
  const { stdout } = await run(PY, [script]);
  const repos = [];
  const lines = stdout.split("\n").filter(Boolean);
  let current = {};
  for (const line of lines) {
    if (line.startsWith("Developer name:")) current.developer = line.split(":")[1]?.trim();
    else if (line.startsWith("Repo name:")) current.repo = line.split(":")[1]?.trim();
    else if (line.startsWith("Stars:")) {
      current.stars = line.split(":")[1]?.trim();
      if (current.developer && current.repo) {
        repos.push({
          title: `${current.developer}/${current.repo}`,
          url: `https://github.com/${current.developer}/${current.repo}`,
          source: "webScrapers",
          score: parseInt(current.stars?.replace(/\D/g, "") || "0", 10),
        });
      }
      current = {};
    }
  }
  return { source: "webScrapers", data: { repos } };
}

async function runYtDlp() {
  await run(PIP, ["install", "-q", "yt-dlp"]);
  const target = "https://www.youtube.com/@TwoMinutePapers/videos";
  const { stdout } = await run(PY, [
    "-m",
    "yt_dlp",
    "--dump-json",
    "--playlist-end",
    "5",
    "--no-download",
    target,
  ]);
  const entries = stdout
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      try {
        const j = JSON.parse(line);
        return {
          title: j.title,
          url: j.webpage_url || j.url,
          source: "yt-dlp",
          description: j.description?.slice(0, 200) ?? "",
          author: j.uploader,
          score: j.view_count ? Math.min(10, Math.floor(j.view_count / 100000)) : 5,
        };
      } catch {
        return null;
      }
    })
    .filter(Boolean);
  return { source: "yt-dlp", data: { videos: entries } };
}

async function runTrendingNews() {
  const feeds = [
    "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
    "https://rss.arxiv.org/rss/cs.AI",
  ];
  const articles = [];
  for (const feedUrl of feeds) {
    try {
      const res = await fetch(feedUrl, { headers: { "User-Agent": "InsightSenderBot/1.0" } });
      const xml = await res.text();
      const items = xml.match(/<item>[\s\S]*?<\/item>/gi) ?? [];
      for (const item of items.slice(0, 10)) {
        const title = item
          .match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/i)?.[1]
          ?.trim();
        const link = item.match(/<link>([\s\S]*?)<\/link>/i)?.[1]?.trim();
        if (title && link) {
          articles.push({
            title: title.replace(/<[^>]+>/g, ""),
            url: link,
            source: "TrendingNews",
          });
        }
      }
    } catch {
      /* skip */
    }
  }
  return { source: "TrendingNews", data: { articles } };
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildHtml(results, date) {
  const sections = results
    .map((r) => {
      const items = r.data?.articles ?? r.data?.repos ?? r.data?.videos ?? [];
      const cards = items
        .map(
          (a) =>
            `<article style="border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:10px 0;">
              <div style="font-size:11px;color:#64748b;">${esc(a.source)}</div>
              <h3 style="margin:6px 0;font-size:16px;"><a href="${esc(a.url)}" style="color:#1F3864;text-decoration:none;">${esc(a.title)}</a></h3>
              ${a.description ? `<p style="font-size:13px;color:#334155;">${esc(a.description)}</p>` : ""}
            </article>`,
        )
        .join("");
      const err = r.error ? `<p style="color:#ef4444;font-size:13px;">Error: ${esc(r.error)}</p>` : "";
      return `<section><h2 style="color:#0f172a;border-bottom:2px solid #1F3864;padding-bottom:4px;">${esc(r.source)} (${items.length})</h2>${err}${cards}</section>`;
    })
    .join("");
  return `<!doctype html><html><head><meta charset="utf-8"/><title>Scraper Report · ${esc(date)}</title></head>
    <body style="margin:0;padding:20px;background:#f8fafc;font-family:system-ui,sans-serif;">
    <div style="max-width:720px;margin:0 auto;">
      <h1 style="color:#0f172a;">InsightSenderBot Scraper Report · ${esc(date)}</h1>
      <p style="color:#64748b;">yt-dlp · webScrapers · keep-up-daily · TrendingNews</p>
      ${sections}
    </div></body></html>`;
}

async function main() {
  const date = new Date().toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata" });
  console.log("Running default scrapers…");

  const runners = [
    ["keep-up-daily", runKeepUpDaily],
    ["webScrapers", runWebScrapers],
    ["yt-dlp", runYtDlp],
    ["TrendingNews", runTrendingNews],
  ];

  const results = [];
  for (const [name, fn] of runners) {
    try {
      console.log(`  → ${name}`);
      results.push(await fn());
      console.log(`    ✓ ${name}`);
    } catch (e) {
      console.warn(`    ✗ ${name}:`, e.message);
      results.push({ source: name, data: {}, error: e.message });
    }
  }

  await mkdir(OUT_DIR, { recursive: true });
  const safeDate = date.replace(/[/\\:]/g, "-");
  const jsonPath = join(OUT_DIR, `scrape-${safeDate}.json`);
  const htmlPath = join(OUT_DIR, `scrape-${safeDate}.html`);
  await writeFile(jsonPath, JSON.stringify({ date, results }, null, 2));
  await writeFile(htmlPath, buildHtml(results, date));
  console.log(`\nOutput:\n  JSON: ${jsonPath}\n  HTML: ${htmlPath}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
