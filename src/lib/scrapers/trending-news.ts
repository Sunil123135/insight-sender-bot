// Trending tech news scraper — inspired by tlavette/TrendingNews (Cheerio/Mongoose pattern)
import type { ScrapedArticle } from "./types";

const UA = "InsightSenderBot/1.0";

const NEWS_FEEDS = [
  {
    name: "Google News · AI",
    url: "https://news.google.com/rss/search?q=artificial+intelligence+machine+learning&hl=en-US&gl=US&ceid=US:en",
  },
  {
    name: "Google News · LLM",
    url: "https://news.google.com/rss/search?q=large+language+model&hl=en-US&gl=US&ceid=US:en",
  },
  {
    name: "ArXiv · cs.AI",
    url: "https://rss.arxiv.org/rss/cs.AI",
  },
];

function parseRssItems(xml: string, source: string): ScrapedArticle[] {
  const articles: ScrapedArticle[] = [];
  const itemRe = /<item>([\s\S]*?)<\/item>/gi;
  let match: RegExpExecArray | null;
  while ((match = itemRe.exec(xml)) !== null) {
    const block = match[1];
    const title = block.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/i)?.[1]?.trim();
    const link = block.match(/<link>([\s\S]*?)<\/link>/i)?.[1]?.trim();
    const desc = block.match(/<description>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>/i)?.[1]
      ?.replace(/<[^>]+>/g, "")
      .trim();
    if (!title || !link) continue;
    articles.push({
      title: title.replace(/<[^>]+>/g, ""),
      url: link,
      source,
      description: desc ?? "",
      score: 5,
      tags: ["news"],
    });
    if (articles.length >= 15) break;
  }
  return articles;
}

export async function scrapeTrendingNews(): Promise<ScrapedArticle[]> {
  const all: ScrapedArticle[] = [];
  const seen = new Set<string>();

  for (const feed of NEWS_FEEDS) {
    try {
      const res = await fetch(feed.url, { headers: { "User-Agent": UA } });
      if (!res.ok) continue;
      const xml = await res.text();
      for (const article of parseRssItems(xml, feed.name)) {
        const key = article.url.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        all.push(article);
      }
    } catch {
      /* skip feed */
    }
  }

  return all;
}

export function articlesToMarkdown(articles: ScrapedArticle[]): string {
  return articles
    .map(
      (a) =>
        `## ${a.title}\nURL: ${a.url}\nSource: ${a.source}\n${a.description}\n`,
    )
    .join("\n---\n");
}
