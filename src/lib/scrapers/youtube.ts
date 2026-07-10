// YouTube metadata scraper — yt-dlp compatible output via oEmbed + page metadata
// Full yt-dlp CLI runs via scripts/run-scrapers.mjs for local/CI use.
import type { ScrapedArticle } from "./types";

const UA = "InsightSenderBot/1.0";

const AI_CHANNELS = [
  { name: "Two Minute Papers", id: "UCbfYPyITb-1l9b6xm9TjzWg" },
  { name: "AI Explained", id: "UCNJ1Ymd5yFuUPtn21xtRbbw" },
  { name: "Yannic Kilcher", id: "UCZHmQk67mSJgfCCTn7xBfew" },
];

interface OEmbedResponse {
  title: string;
  author_name: string;
  thumbnail_url: string;
  html: string;
}

async function fetchOEmbed(videoUrl: string): Promise<OEmbedResponse | null> {
  try {
    const res = await fetch(
      `https://www.youtube.com/oembed?url=${encodeURIComponent(videoUrl)}&format=json`,
      { headers: { "User-Agent": UA } },
    );
    if (!res.ok) return null;
    return (await res.json()) as OEmbedResponse;
  } catch {
    return null;
  }
}

async function fetchChannelVideos(channelId: string): Promise<string[]> {
  try {
    const res = await fetch(`https://www.youtube.com/channel/${channelId}/videos`, {
      headers: { "User-Agent": UA },
    });
    if (!res.ok) return [];
    const html = await res.text();
    const ids = new Set<string>();
    const re = /"videoId":"([a-zA-Z0-9_-]{11})"/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(html)) !== null) {
      ids.add(m[1]);
      if (ids.size >= 5) break;
    }
    return [...ids];
  } catch {
    return [];
  }
}

export async function scrapeYouTubeFeed(): Promise<ScrapedArticle[]> {
  const articles: ScrapedArticle[] = [];

  for (const channel of AI_CHANNELS) {
    const videoIds = await fetchChannelVideos(channel.id);
    for (const vid of videoIds) {
      const url = `https://www.youtube.com/watch?v=${vid}`;
      const meta = await fetchOEmbed(url);
      if (!meta) continue;
      articles.push({
        title: meta.title,
        url,
        source: `youtube/${channel.name}`,
        description: `By ${meta.author_name}`,
        score: 5,
        author: meta.author_name,
        tags: ["youtube", "ai"],
      });
    }
  }

  return articles;
}

export async function scrapeYouTubeUrl(url: string): Promise<{
  content: string;
  imageUrl: string | null;
  article: ScrapedArticle | null;
}> {
  const meta = await fetchOEmbed(url);
  if (!meta) {
    return { content: "", imageUrl: null, article: null };
  }
  const article: ScrapedArticle = {
    title: meta.title,
    url,
    source: "youtube",
    description: `Channel: ${meta.author_name}`,
    score: 5,
    author: meta.author_name,
    tags: ["youtube"],
  };
  const content = [
    `# ${meta.title}`,
    `URL: ${url}`,
    `Channel: ${meta.author_name}`,
    `Thumbnail: ${meta.thumbnail_url}`,
  ].join("\n");
  return { content, imageUrl: meta.thumbnail_url, article };
}

export function articlesToMarkdown(articles: ScrapedArticle[]): string {
  return articles
    .map(
      (a) =>
        `## ${a.title}\nURL: ${a.url}\nSource: ${a.source}\nAuthor: ${a.author ?? "—"}\n${a.description}\n`,
    )
    .join("\n---\n");
}
