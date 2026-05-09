import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const InputSchema = z.object({
  url: z.string().url(),
});

const TIMEOUT_MS = 15_000;

async function fetchWithTimeout(url: string, init?: RequestInit, ms = TIMEOUT_MS) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(t);
  }
}

/**
 * Fetch an article/listing using Jina Reader (https://r.jina.ai/<url>),
 * returning clean markdown. Falls back to raw fetch on failure.
 */
export const scrapeUrl = createServerFn({ method: "POST" })
  .inputValidator((d) => InputSchema.parse(d))
  .handler(async ({ data }) => {
    const jinaKey = process.env.JINA_API_KEY;
    const target = `https://r.jina.ai/${data.url}`;
    try {
      const res = await fetchWithTimeout(target, {
        headers: jinaKey ? { Authorization: `Bearer ${jinaKey}` } : {},
      });
      if (!res.ok) throw new Error(`Jina ${res.status}`);
      const text = await res.text();
      return { ok: true as const, content: text.slice(0, 18_000), source: "jina" as const };
    } catch (err) {
      // Fallback: raw fetch
      try {
        const res = await fetchWithTimeout(data.url, {
          headers: { "User-Agent": "ScrapeSignal/1.0 (+https://lovable.dev)" },
        });
        if (!res.ok) throw new Error(`raw ${res.status}`);
        const text = await res.text();
        // crude: strip HTML
        const stripped = text
          .replace(/<script[\s\S]*?<\/script>/gi, "")
          .replace(/<style[\s\S]*?<\/style>/gi, "")
          .replace(/<[^>]+>/g, " ")
          .replace(/\s+/g, " ")
          .trim();
        return { ok: true as const, content: stripped.slice(0, 18_000), source: "raw" as const };
      } catch (e) {
        return {
          ok: false as const,
          error: err instanceof Error ? err.message : "fetch failed",
        };
      }
    }
  });
