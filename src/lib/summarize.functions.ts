import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const InputSchema = z.object({
  url: z.string().url(),
  domain: z.enum(["finance", "supply_chain", "marketing", "ai_content"]),
  content: z.string().min(20).max(20_000),
});

const ItemSchema = z.object({
  title: z.string(),
  url: z.string(),
  summary: z.string(),
  why: z.string(),
  score: z.number().min(0).max(10),
  takeaways: z.array(z.string()).max(5),
});

const ResponseSchema = z.object({
  items: z.array(ItemSchema).max(8),
});

const DOMAIN_LENS: Record<string, string> = {
  finance: "a finance professional tracking markets, macro, deals and corporate news",
  supply_chain: "a supply chain operator tracking logistics, freight, sourcing and disruptions",
  marketing: "a marketing leader tracking campaigns, channels, brand and ad-tech",
  ai_content: "an AI / content strategist tracking model releases, research and product launches",
};

async function callClaude(systemPrompt: string, userPrompt: string, retry = true): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY is not configured");

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5",
      max_tokens: 1500,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    if (retry && res.status >= 500) return callClaude(systemPrompt, userPrompt, false);
    throw new Error(`Claude ${res.status}: ${body.slice(0, 300)}`);
  }
  const data = (await res.json()) as { content: Array<{ type: string; text?: string }> };
  return data.content.map((c) => c.text ?? "").join("");
}

function extractJson(text: string): unknown {
  // Try fenced block first
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = fence ? fence[1] : text;
  // Find the first {...} or [...] body
  const start = candidate.search(/[{[]/);
  if (start === -1) throw new Error("no JSON in model output");
  const slice = candidate.slice(start);
  // Walk braces
  let depth = 0,
    end = -1,
    inStr = false,
    esc = false;
  const open = slice[0];
  const close = open === "{" ? "}" : "]";
  for (let i = 0; i < slice.length; i++) {
    const ch = slice[i];
    if (inStr) {
      if (esc) esc = false;
      else if (ch === "\\") esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') inStr = true;
    else if (ch === open) depth++;
    else if (ch === close) {
      depth--;
      if (depth === 0) {
        end = i + 1;
        break;
      }
    }
  }
  if (end === -1) throw new Error("unterminated JSON");
  return JSON.parse(slice.slice(0, end));
}

export const summarizeContent = createServerFn({ method: "POST" })
  .inputValidator((d) => InputSchema.parse(d))
  .handler(async ({ data }) => {
    const lens = DOMAIN_LENS[data.domain];
    const system = `You are a senior analyst building a daily intelligence brief for ${lens}.
You read scraped pages (often listings of multiple articles) and extract the most signal-dense items.
You ALWAYS respond with strict JSON matching the requested schema. No prose, no markdown fences.`;

    const user = `Source URL: ${data.url}
Domain: ${data.domain}

Scraped content (markdown / text, may include multiple articles or a listing):
"""
${data.content}
"""

Extract up to 5 distinct, high-signal items relevant to ${data.domain}. For each item:
- title: original headline if present, otherwise a tight summary headline (<= 90 chars)
- url: the most specific article URL you can find in the content; if none, use the source URL "${data.url}"
- summary: 2-3 sentences on what happened
- why: 1 sentence on why it matters for ${data.domain}
- score: integer 0-10 relevance to ${data.domain} (10 = must-read)
- takeaways: 2-3 short bullet strings

Respond with this JSON only:
{"items":[{"title":"","url":"","summary":"","why":"","score":0,"takeaways":[""]}]}`;

    let raw: string;
    try {
      raw = await callClaude(system, user);
    } catch (e) {
      return { ok: false as const, error: e instanceof Error ? e.message : "claude failed" };
    }

    let parsed: unknown;
    try {
      parsed = extractJson(raw);
    } catch {
      // one retry asking for JSON only
      try {
        const raw2 = await callClaude(
          system,
          user + "\n\nReminder: respond with VALID JSON only. No commentary."
        );
        parsed = extractJson(raw2);
      } catch (e) {
        return { ok: false as const, error: "could not parse JSON from model" };
      }
    }

    const safe = ResponseSchema.safeParse(parsed);
    if (!safe.success) {
      return { ok: false as const, error: "model JSON did not match schema" };
    }
    return { ok: true as const, items: safe.data.items };
  });
