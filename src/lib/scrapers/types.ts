export interface ScrapedArticle {
  title: string;
  url: string;
  source: string;
  description: string;
  score: number;
  author?: string;
  tags?: string[];
}

export interface ScrapeResult {
  ok: true;
  content: string;
  imageUrl: string | null;
  articles: ScrapedArticle[];
  scraper: string;
}

export interface ScrapeError {
  ok: false;
  error: string;
}

export type ScraperOutput = ScrapeResult | ScrapeError;

export const DEFAULT_SCRAPER_SOURCES = [
  {
    name: "Keep Up Daily (HN + Dev.to + Reddit)",
    url: "scraper://keep-up-daily",
    domain: "ai_content",
  },
  {
    name: "GitHub Trending (webScrapers)",
    url: "scraper://github-trending",
    domain: "ai_content",
  },
  {
    name: "YouTube Metadata (yt-dlp)",
    url: "scraper://youtube-feed",
    domain: "ai_content",
  },
  {
    name: "Trending Tech News",
    url: "scraper://trending-news",
    domain: "ai_content",
  },
] as const;
