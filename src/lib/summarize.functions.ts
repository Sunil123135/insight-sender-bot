import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const InputSchema = z.object({
  url: z.string().url(),
  domain: z.string().min(1),
  content: z.string().min(20).max(20_000),
});

const ItemSchema = z.object({
  title: z.string(),
  url: z.string(),
  summary: z.string(),
  why: z.string().default(""),
  whats_new: z.string().default(""),
  whats_changing: z.string().default(""),
  whats_coming: z.string().default(""),
  for_me: z.string().default(""),
  to_learn: z.string().default(""),
  monetize: z.string().default(""),
  score: z.number().min(0).max(10),
  takeaways: z.array(z.string()).max(5).default([]),
});
const ResponseSchema = z.object({ items: z.array(ItemSchema).max(8) });

export type SummarizedItem = z.infer<typeof ItemSchema>;

async function callClaude(system: string, user: string, retry = true): Promise<string> {
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
      max_tokens: 2500,
      system,
      messages: [{ role: "user", content: user }],
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    if (retry && res.status >= 500) return callClaude(system, user, false);
    throw new Error(`Claude ${res.status}: ${body.slice(0, 300)}`);
  }
  const data = (await res.json()) as { content: Array<{ type: string; text?: string }> };
  return data.content.map((c) => c.text ?? "").join("");
}

async function callOpenAI(system: string, user: string): Promise<string> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY is not configured");
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      max_tokens: 2500,
      messages: [
        { role: "system", content: system },
        { role: "user", content: user },
      ],
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`OpenAI ${res.status}: ${body.slice(0, 300)}`);
  }
  const data = (await res.json()) as { choices: Array<{ message: { content: string } }> };
  return data.choices.map((c) => c.message?.content ?? "").join("");
}

async function callModel(system: string, user: string): Promise<{ raw: string; provider: "claude" | "openai" }> {
  try {
    const raw = await callClaude(system, user);
    return { raw, provider: "claude" };
  } catch (e) {
    if (!process.env.OPENAI_API_KEY) throw e;
    console.warn("Claude failed, falling back to OpenAI:", e instanceof Error ? e.message : e);
    const raw = await callOpenAI(system, user);
    return { raw, provider: "openai" };
  }
}

function extractJson(text: string): unknown {
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = fence ? fence[1] : text;
  const start = candidate.search(/[{[]/);
  if (start === -1) throw new Error("no JSON in model output");
  const slice = candidate.slice(start);
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

const SYSTEM = `You are a senior intelligence analyst building a daily brief for a curious operator who tracks new AI models, artificial intelligence, consciousness, spirituality, vision systems, and large language models.
You read scraped pages (often listings) and surface the highest-signal items.
For each item you analyze through six lenses: what's NEW, what's CHANGING, what's ABOUT TO HAPPEN, WHAT'S IN IT FOR ME (the reader), what they CAN LEARN, and how they could MONETIZE it.
Be concrete and specific. Prefer named models, papers, organizations, and dates over vague claims. Skip filler.
ALWAYS respond with strict JSON matching the requested schema. No prose, no markdown fences.`;

export async function summarizeContentImpl(args: {
  url: string;
  domain: string;
  content: string;
}): Promise<{ ok: true; items: SummarizedItem[] } | { ok: false; error: string }> {
  const user = `Source URL: ${args.url}
Domain focus: ${args.domain} (themes: new AI models, artificial intelligence, consciousness, spirituality, computer vision, language models)

Scraped content (markdown / text, may include multiple articles or a listing):
"""
${args.content}
"""

Extract up to 5 distinct, high-signal items. For each:
- title: original headline if present, else a tight headline (<= 90 chars)
- url: most specific article URL in the content; if none, use "${args.url}"
- summary: 2-3 sentences on what happened
- why: 1 sentence on why it matters
- whats_new: one sentence — what is genuinely new here
- whats_changing: one sentence — what is shifting in the field because of this
- whats_coming: one sentence — what this signals for the next 1-6 months
- for_me: one sentence — what's in it for a curious AI/consciousness/vision practitioner
- to_learn: one sentence — concrete concept, paper, or skill to study
- monetize: one sentence — a plausible way to turn this into income (product, consulting, content, etc.)
- score: integer 0-10 relevance (10 = must-read)
- takeaways: 2-3 short bullet strings

Respond with JSON ONLY:
{"items":[{"title":"","url":"","summary":"","why":"","whats_new":"","whats_changing":"","whats_coming":"","for_me":"","to_learn":"","monetize":"","score":0,"takeaways":[""]}]}`;

  let raw: string;
  try {
    raw = await callClaude(SYSTEM, user);
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "claude failed" };
  }
  let parsed: unknown;
  try {
    parsed = extractJson(raw);
  } catch {
    try {
      const raw2 = await callClaude(SYSTEM, user + "\n\nReminder: VALID JSON only.");
      parsed = extractJson(raw2);
    } catch {
      return { ok: false, error: "could not parse JSON from model" };
    }
  }
  const safe = ResponseSchema.safeParse(parsed);
  if (!safe.success) return { ok: false, error: "model JSON did not match schema" };
  return { ok: true, items: safe.data.items };
}

export const summarizeContent = createServerFn({ method: "POST" })
  .inputValidator((d) => InputSchema.parse(d))
  .handler(async ({ data }) => summarizeContentImpl(data));
