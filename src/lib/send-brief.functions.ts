import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const ItemSchema = z.object({
  title: z.string(),
  url: z.string(),
  source: z.string(),
  domain: z.string(),
  summary: z.string(),
  why: z.string(),
  score: z.number(),
  takeaways: z.array(z.string()),
});

const InputSchema = z.object({
  channel: z.enum(["n8n", "email", "both"]),
  recipientEmail: z.string().email().optional(),
  interestProfile: z.string(),
  items: z.array(ItemSchema).min(1).max(50),
});

function buildHtml(items: z.infer<typeof ItemSchema>[], profile: string) {
  const rows = items
    .map(
      (it) => `
    <div style="border:1px solid #e2e8f0;border-radius:14px;padding:18px;margin:12px 0;background:#ffffff;">
      <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;">${it.source} · score ${it.score}/10</div>
      <h3 style="margin:6px 0 8px;color:#1F3864;font-size:17px;"><a href="${it.url}" style="color:#1F3864;text-decoration:none;">${it.title}</a></h3>
      <p style="margin:0 0 8px;color:#0f172a;font-size:14px;line-height:1.5;">${it.summary}</p>
      <p style="margin:0 0 10px;color:#475569;font-size:13px;"><b>Why it matters:</b> ${it.why}</p>
      ${
        it.takeaways.length
          ? `<ul style="margin:6px 0 0 18px;padding:0;color:#334155;font-size:13px;">${it.takeaways
              .map((t) => `<li style="margin:2px 0;">${t}</li>`)
              .join("")}</ul>`
          : ""
      }
    </div>`
    )
    .join("");
  return `<!doctype html><html><body style="font-family:Inter,Arial,sans-serif;background:#f8fafc;padding:24px;">
    <div style="max-width:640px;margin:0 auto;">
      <h1 style="color:#1F3864;font-size:22px;margin:0 0 4px;">ScrapeSignal Brief</h1>
      <p style="color:#64748b;margin:0 0 16px;font-size:13px;">Profile: ${profile} · ${items.length} item${items.length === 1 ? "" : "s"}</p>
      ${rows}
      <p style="color:#94a3b8;font-size:11px;margin-top:24px;">Sent via ScrapeSignal</p>
    </div></body></html>`;
}

export const sendBrief = createServerFn({ method: "POST" })
  .inputValidator((d) => InputSchema.parse(d))
  .handler(async ({ data }) => {
    const results: { channel: string; ok: boolean; detail?: string }[] = [];
    const payload = {
      generatedAt: new Date().toISOString(),
      interestProfile: data.interestProfile,
      items: data.items,
    };

    if (data.channel === "n8n" || data.channel === "both") {
      const url = process.env.N8N_WEBHOOK_URL;
      if (!url) {
        results.push({ channel: "n8n", ok: false, detail: "N8N_WEBHOOK_URL not set" });
      } else {
        try {
          const res = await fetch(url, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(payload),
          });
          results.push({
            channel: "n8n",
            ok: res.ok,
            detail: res.ok ? `posted (${res.status})` : `webhook ${res.status}`,
          });
        } catch (e) {
          results.push({
            channel: "n8n",
            ok: false,
            detail: e instanceof Error ? e.message : "post failed",
          });
        }
      }
    }

    if (data.channel === "email" || data.channel === "both") {
      const apiKey = process.env.RESEND_API_KEY;
      if (!apiKey) {
        results.push({ channel: "email", ok: false, detail: "RESEND_API_KEY not set" });
      } else if (!data.recipientEmail) {
        results.push({ channel: "email", ok: false, detail: "recipient email required" });
      } else {
        try {
          const html = buildHtml(data.items, data.interestProfile);
          const res = await fetch("https://api.resend.com/emails", {
            method: "POST",
            headers: {
              "content-type": "application/json",
              Authorization: `Bearer ${apiKey}`,
            },
            body: JSON.stringify({
              from: "ScrapeSignal <onboarding@resend.dev>",
              to: [data.recipientEmail],
              subject: `ScrapeSignal Brief — ${data.items.length} item${data.items.length === 1 ? "" : "s"}`,
              html,
            }),
          });
          const body = await res.json().catch(() => ({}));
          results.push({
            channel: "email",
            ok: res.ok,
            detail: res.ok ? `sent (${(body as { id?: string }).id ?? "ok"})` : `resend ${res.status}: ${JSON.stringify(body).slice(0, 200)}`,
          });
        } catch (e) {
          results.push({
            channel: "email",
            ok: false,
            detail: e instanceof Error ? e.message : "send failed",
          });
        }
      }
    }

    return { ok: results.every((r) => r.ok), results };
  });
