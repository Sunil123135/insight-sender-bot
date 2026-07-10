// Default scraper orchestrator — routes URLs to the right scraper
import {
  scrapeGitHubTrending,
  articlesToMarkdown as ghMd,
} from "./github-trending";
import {
  scrapeKeepUpDaily,
  articlesToMarkdown as kudMd,
} from "./keep-up-daily";
import {
  scrapeYouTubeFeed,
  scrapeYouTubeUrl,
  articlesToMarkdown as ytMd,
} from "./youtube";
import {
  scrapeTrendingNews,
  articlesToMarkdown as newsMd,
} from "./trending-news";
import { buildScrapersHtml } from "./html-output";
import type { ScraperOutput, ScrapedArticle } from "./types";

export const SCRAPER_PROTOCOL = "scraper://";

export function isScraperUrl(url: string): boolean {
  return url.startsWith(SCRAPER_PROTOCOL);
}

export function scraperIdFromUrl(url: string): string {
  return url.slice(SCRAPER_PROTOCOL.length);
}

function ok(
  scraper: string,
  articles: ScrapedArticle[],
  content: string,
  imageUrl: string | null = null,
): ScraperOutput {
  return { ok: true, content, imageUrl, articles, scraper };
}

export async function runBuiltinScraper(scraperId: string): Promise<ScraperOutput> {
  try {
    switch (scraperId) {
      case "github-trending": {
        const articles = await scrapeGitHubTrending();
        return ok("webScrapers/github-trending", articles, ghMd(articles));
      }
      case "keep-up-daily": {
        const articles = await scrapeKeepUpDaily();
        return ok("keep-up-daily", articles, kudMd(articles));
      }
      case "youtube-feed": {
        const articles = await scrapeYouTubeFeed();
        return ok("yt-dlp/youtube-feed", articles, ytMd(articles));
      }
      case "trending-news": {
        const articles = await scrapeTrendingNews();
        return ok("TrendingNews", articles, newsMd(articles));
      }
      default:
        return { ok: false, error: `unknown scraper: ${scraperId}` };
    }
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "scraper failed" };
  }
}

export async function scrapeWithDefaultScrapers(url: string): Promise<ScraperOutput | null> {
  if (isScraperUrl(url)) {
    return runBuiltinScraper(scraperIdFromUrl(url));
  }

  if (/youtube\.com\/watch|youtu\.be\//i.test(url)) {
    const { content, imageUrl, article } = await scrapeYouTubeUrl(url);
    if (!content) return null;
    return ok("yt-dlp", article ? [article] : [], content, imageUrl);
  }

  if (/github\.com\/trending/i.test(url)) {
    const articles = await scrapeGitHubTrending();
    return ok("webScrapers/github-trending", articles, ghMd(articles));
  }

  return null;
}

export async function runAllDefaultScrapers(): Promise<{
  sections: Array<{ name: string; articles: ScrapedArticle[] }>;
  html: string;
  combinedContent: string;
}> {
  const sections: Array<{ name: string; articles: ScrapedArticle[] }> = [];

  const runners = [
    { name: "Keep Up Daily", fn: scrapeKeepUpDaily },
    { name: "GitHub Trending", fn: scrapeGitHubTrending },
    { name: "YouTube (yt-dlp)", fn: scrapeYouTubeFeed },
    { name: "Trending News", fn: scrapeTrendingNews },
  ] as const;

  for (const { name, fn } of runners) {
    try {
      const articles = await fn();
      if (articles.length > 0) sections.push({ name, articles });
    } catch (e) {
      console.warn(`Scraper ${name} failed:`, e);
    }
  }

  const dateLabel = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });

  const html = buildScrapersHtml(sections, dateLabel);
  const combinedContent = sections
    .map((s) => `# ${s.name}\n\n${s.articles.map((a) => `## ${a.title}\n${a.url}\n${a.description}`).join("\n\n")}`)
    .join("\n\n---\n\n")
    .slice(0, 18_000);

  return { sections, html, combinedContent };
}

export { buildScrapersHtml };
