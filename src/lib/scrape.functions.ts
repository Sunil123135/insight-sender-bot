import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const InputSchema = z.object({ url: z.string().url() });
const TIMEOUT_MS = 20_000;

async function fetchWithTimeout(url: string, init?: RequestInit, ms = TIMEOUT_MS) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(t);
  }
}

function extractImageFromHtml(html: string, baseUrl: string): string | null {
  const patterns = [
    /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+name=["']og:image["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i,
    /<meta[^>]+name=["']twitter:image["'][^>]+content=["']([^"']+)["']/i,
    /<link[^>]+rel=["']image_src["'][^>]+href=["']([^"']+)["']/i,
  ];
  for (const re of patterns) {
    const m = html.match(re);
    if (m && m[1]) {
      try {
        return new URL(m[1], baseUrl).toString();
      } catch {
        return m[1];
      }
    }
  }
  // first <img src>
  const img = html.match(/<img[^>]+src=["']([^"']+)["']/i);
  if (img && img[1]) {
    try {
      return new URL(img[1], baseUrl).toString();
    } catch {
      return null;
    }
  }
  return null;
}

export async function scrapeUrlImpl(url: string) {
  const jinaKey = process.env.JINA_API_KEY;
  let content = "";
  let imageUrl: string | null = null;
  try {
    const res = await fetchWithTimeout(`https://r.jina.ai/${url}`, {
      headers: jinaKey ? { Authorization: `Bearer ${jinaKey}` } : {},
    });
    if (!res.ok) throw new Error(`Jina ${res.status}`);
    content = (await res.text()).slice(0, 18_000);
  } catch {
    try {
      const res = await fetchWithTimeout(url, {
        headers: { "User-Agent": "ScrapeSignal/1.0 (+https://lovable.dev)" },
      });
      if (!res.ok) throw new Error(`raw ${res.status}`);
      const text = await res.text();
      content = text
        .replace(/<script[\s\S]*?<\/script>/gi, "")
        .replace(/<style[\s\S]*?<\/style>/gi, "")
        .replace(/<[^>]+>/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, 18_000);
    } catch (e) {
      return { ok: false as const, error: e instanceof Error ? e.message : "fetch failed" };
    }
  }

  // Best-effort image extraction from raw HTML (separate request, non-fatal)
  try {
    const res = await fetchWithTimeout(
      url,
      { headers: { "User-Agent": "ScrapeSignal/1.0" } },
      8_000
    );
    if (res.ok) {
      const html = await res.text();
      imageUrl = extractImageFromHtml(html.slice(0, 60_000), url);
    }
  } catch {
    /* non-fatal */
  }

  return { ok: true as const, content, imageUrl };
}

export const scrapeUrl = createServerFn({ method: "POST" })
  .inputValidator((d) => InputSchema.parse(d))
  .handler(async ({ data }) => scrapeUrlImpl(data.url));
