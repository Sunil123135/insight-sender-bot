// GitHub Trending scraper — ported from yash-d99/webScrapers + LuizMacedo/keep-up-daily
import type { ScrapedArticle } from "./types";

const UA = "InsightSenderBot/1.0 (+https://github.com/Sunil123135/insight-sender-bot)";

export async function scrapeGitHubTrending(): Promise<ScrapedArticle[]> {
  const res = await fetch("https://github.com/trending?since=daily", {
    headers: { "User-Agent": UA },
  });
  if (!res.ok) throw new Error(`GitHub trending ${res.status}`);
  const html = await res.text();
  const articles: ScrapedArticle[] = [];
  const seen = new Set<string>();

  const rowRe =
    /<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>([\s\S]*?)<\/article>/gi;
  let rowMatch: RegExpExecArray | null;
  while ((rowMatch = rowRe.exec(html)) !== null) {
    const block = rowMatch[1];
    const linkMatch = block.match(/<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
    if (!linkMatch) continue;
    const path = linkMatch[1].trim();
    const repoUrl = `https://github.com${path}`;
    if (seen.has(repoUrl)) continue;
    seen.add(repoUrl);

    const title = path.replace(/^\//, "").replace(/<[^>]+>/g, "").trim();
    const descMatch = block.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
    const description = descMatch
      ? descMatch[1].replace(/<[^>]+>/g, "").trim()
      : "";

    const langMatch = block.match(/itemprop="programmingLanguage"[^>]*>([^<]+)</i);
    const starsMatch = block.match(/float-sm-right[^>]*>([\s\S]*?)<\/span>/i);
    const starsDigits = starsMatch
      ? (starsMatch[1].match(/\d+/g)?.join("") ?? "0")
      : "0";

    articles.push({
      title,
      url: repoUrl,
      source: "github_trending",
      description,
      score: parseInt(starsDigits, 10) || 0,
      tags: langMatch ? [langMatch[1].trim().toLowerCase()] : [],
    });
  }

  return articles;
}

export function articlesToMarkdown(articles: ScrapedArticle[]): string {
  return articles
    .map(
      (a) =>
        `## ${a.title}\nURL: ${a.url}\nSource: ${a.source}\nScore: ${a.score}\n${a.description}\n`,
    )
    .join("\n---\n");
}
