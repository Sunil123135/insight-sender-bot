// Keep Up Daily aggregate scraper — ported from LuizMacedo/keep-up-daily API sources
import type { ScrapedArticle } from "./types";

const UA = "InsightSenderBot/1.0";
const TIMEOUT = 15_000;

async function fetchJson<T>(url: string): Promise<T> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), TIMEOUT);
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": UA },
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`${url} → ${res.status}`);
    return (await res.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

async function scrapeHackerNews(limit = 20): Promise<ScrapedArticle[]> {
  const ids = await fetchJson<number[]>(
    "https://hacker-news.firebaseio.com/v0/topstories.json",
  );
  const articles: ScrapedArticle[] = [];
  for (const id of ids.slice(0, limit)) {
    try {
      const item = await fetchJson<{
        type?: string;
        title?: string;
        url?: string;
        by?: string;
        score?: number;
        descendants?: number;
      }>(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
      if (!item || item.type !== "story" || !item.title) continue;
      articles.push({
        title: item.title,
        url: item.url ?? `https://news.ycombinator.com/item?id=${id}`,
        source: "hackernews",
        description: "",
        author: item.by ?? "",
        score: item.score ?? 0,
      });
    } catch {
      /* skip */
    }
  }
  return articles;
}

async function scrapeDevto(limit = 15): Promise<ScrapedArticle[]> {
  const data = await fetchJson<
    Array<{
      title: string;
      url: string;
      description: string;
      positive_reactions_count: number;
      user: { name: string };
      tag_list: string[];
    }>
  >(`https://dev.to/api/articles?per_page=${limit}&top=7`);
  return data.map((a) => ({
    title: a.title,
    url: a.url,
    source: "devto",
    description: a.description ?? "",
    author: a.user?.name ?? "",
    score: a.positive_reactions_count ?? 0,
    tags: a.tag_list ?? [],
  }));
}

async function scrapeReddit(subreddit: string, limit = 10): Promise<ScrapedArticle[]> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), TIMEOUT);
  let data: {
    data: {
      children: Array<{
        data: {
          title: string;
          url: string;
          selftext: string;
          score: number;
          author: string;
          permalink: string;
        };
      }>;
    };
  };
  try {
    const res = await fetch(
      `https://www.reddit.com/r/${subreddit}/hot.json?limit=${limit}`,
      { headers: { "User-Agent": UA }, signal: controller.signal },
    );
    if (!res.ok) return [];
    data = (await res.json()) as typeof data;
  } catch {
    return [];
  } finally {
    clearTimeout(t);
  }
  return data.data.children
    .filter((c) => c.data.title && !c.data.title.startsWith("[deleted]"))
    .map((c) => ({
      title: c.data.title,
      url: c.data.url.startsWith("http")
        ? c.data.url
        : `https://www.reddit.com${c.data.permalink}`,
      source: `reddit/${subreddit}`,
      description: (c.data.selftext ?? "").slice(0, 300),
      author: c.data.author,
      score: c.data.score ?? 0,
    }));
}

async function scrapeLobsters(limit = 15): Promise<ScrapedArticle[]> {
  const data = await fetchJson<
    Array<{
      title: string;
      url: string;
      score: number;
      comments_count: number;
      submitter_user: { username: string };
      description?: string;
    }>
  >(`https://lobste.rs/hottest.json`);
  return data.slice(0, limit).map((s) => ({
    title: s.title,
    url: s.url,
    source: "lobsters",
    description: s.description ?? "",
    author: s.submitter_user?.username ?? "",
    score: s.score ?? 0,
  }));
}

function dedupe(articles: ScrapedArticle[]): ScrapedArticle[] {
  const seen = new Set<string>();
  return articles.filter((a) => {
    const key = a.url.replace(/\/$/, "").toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export async function scrapeKeepUpDaily(): Promise<ScrapedArticle[]> {
  const results = await Promise.allSettled([
    scrapeHackerNews(),
    scrapeDevto(),
    scrapeReddit("programming"),
    scrapeReddit("MachineLearning"),
    scrapeLobsters(),
  ]);

  const all: ScrapedArticle[] = [];
  for (const r of results) {
    if (r.status === "fulfilled") all.push(...r.value);
  }
  return dedupe(all).sort((a, b) => b.score - a.score);
}

export function articlesToMarkdown(articles: ScrapedArticle[]): string {
  return articles
    .map(
      (a) =>
        `## ${a.title}\nURL: ${a.url}\nSource: ${a.source}\nScore: ${a.score}\nAuthor: ${a.author ?? "—"}\n${a.description}\n`,
    )
    .join("\n---\n");
}
