// Daily run pipeline + cron endpoint. Public route — invoked by pg_cron and from the UI.
import { createFileRoute } from "@tanstack/react-router";
import { supabaseAdmin } from "@/integrations/supabase/client.server";
import { scrapeUrlImpl } from "@/lib/scrape.functions";
import { summarizeContentImpl } from "@/lib/summarize.functions";
import { buildBriefHtml, type BriefItem } from "@/lib/email-html";

async function runDaily() {
  const startedAt = new Date().toISOString();
  const { data: cfg } = await supabaseAdmin
    .from("schedule_config")
    .select("*")
    .eq("id", 1)
    .maybeSingle();

  if (!cfg || !cfg.enabled) {
    return { ok: false, error: "schedule disabled or missing config" };
  }

  const { data: sources } = await supabaseAdmin
    .from("sources")
    .select("*")
    .eq("active", true);

  if (!sources || sources.length === 0) {
    return { ok: false, error: "no active sources" };
  }

  const { data: brief } = await supabaseAdmin
    .from("briefs")
    .insert({
      recipient_email: cfg.recipient_email,
      channel: cfg.channel,
      status: "running",
    })
    .select()
    .single();

  const briefId = brief!.id as string;
  const collected: BriefItem[] = [];
  const itemRows: Array<Record<string, unknown>> = [];
  let failures = 0;

  for (const src of sources) {
    try {
      const scraped = await scrapeUrlImpl(src.url);
      if (!scraped.ok) {
        failures++;
        continue;
      }
      const summary = await summarizeContentImpl({
        url: src.url,
        domain: src.domain,
        content: scraped.content,
      });
      if (!summary.ok) {
        failures++;
        continue;
      }
      for (const it of summary.items) {
        const briefItem: BriefItem = {
          title: it.title,
          url: it.url || src.url,
          source: src.name,
          summary: it.summary,
          why: it.why,
          whats_new: it.whats_new,
          whats_changing: it.whats_changing,
          whats_coming: it.whats_coming,
          for_me: it.for_me,
          to_learn: it.to_learn,
          monetize: it.monetize,
          score: Math.round(it.score),
          takeaways: it.takeaways,
          image_url: scraped.imageUrl,
        };
        collected.push(briefItem);
        itemRows.push({
          source_id: src.id,
          source_name: src.name,
          domain: src.domain,
          url: briefItem.url,
          title: briefItem.title,
          summary: briefItem.summary,
          why: briefItem.why,
          whats_new: briefItem.whats_new,
          whats_changing: briefItem.whats_changing,
          whats_coming: briefItem.whats_coming,
          for_me: briefItem.for_me,
          to_learn: briefItem.to_learn,
          monetize: briefItem.monetize,
          takeaways: briefItem.takeaways,
          image_url: briefItem.image_url,
          score: briefItem.score,
          brief_id: briefId,
        });
      }
    } catch {
      failures++;
    }
  }

  // Persist items
  if (itemRows.length > 0) {
    await supabaseAdmin.from("items").insert(itemRows);
  }

  if (collected.length === 0) {
    await supabaseAdmin
      .from("briefs")
      .update({
        status: "failed",
        item_count: 0,
        detail: `no items extracted; ${failures} source failure(s)`,
      })
      .eq("id", briefId);
    return { ok: false, error: "no items extracted", briefId };
  }

  // Top 12 by score for the email
  const top = [...collected].sort((a, b) => b.score - a.score).slice(0, 12);
  const dateLabel = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
  const html = buildBriefHtml(top, dateLabel);

  const results: Array<{ channel: string; ok: boolean; detail: string }> = [];

  // Email via Resend
  if (cfg.channel === "email" || cfg.channel === "both") {
    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
      results.push({ channel: "email", ok: false, detail: "RESEND_API_KEY not set" });
    } else {
      try {
        const res = await fetch("https://api.resend.com/emails", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            from: "ScrapeSignal <onboarding@resend.dev>",
            to: [cfg.recipient_email],
            subject: `ScrapeSignal · ${dateLabel} · ${top.length} items`,
            html,
          }),
        });
        const body = (await res.json().catch(() => ({}))) as { id?: string };
        results.push({
          channel: "email",
          ok: res.ok,
          detail: res.ok ? `sent (${body.id ?? "ok"})` : `resend ${res.status}`,
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

  // n8n webhook
  if (cfg.channel === "n8n" || cfg.channel === "both") {
    const url = process.env.N8N_WEBHOOK_URL;
    if (!url) {
      results.push({ channel: "n8n", ok: false, detail: "N8N_WEBHOOK_URL not set" });
    } else {
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            generatedAt: startedAt,
            recipient: cfg.recipient_email,
            items: top,
            html,
          }),
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

  const allOk = results.every((r) => r.ok);
  await supabaseAdmin
    .from("briefs")
    .update({
      status: allOk ? "sent" : "partial",
      item_count: top.length,
      detail: results.map((r) => `${r.channel}: ${r.detail}`).join(" | "),
    })
    .eq("id", briefId);

  return { ok: allOk, briefId, itemCount: top.length, results, failures };
}

export const Route = createFileRoute("/api/public/hooks/run-daily")({
  server: {
    handlers: {
      POST: async () => {
        try {
          const out = await runDaily();
          return new Response(JSON.stringify(out), {
            status: out.ok ? 200 : 500,
            headers: { "content-type": "application/json" },
          });
        } catch (e) {
          return new Response(
            JSON.stringify({ ok: false, error: e instanceof Error ? e.message : "unknown" }),
            { status: 500, headers: { "content-type": "application/json" } }
          );
        }
      },
      GET: async () =>
        new Response(
          JSON.stringify({ ok: true, hint: "POST to run the daily brief" }),
          { headers: { "content-type": "application/json" } }
        ),
    },
  },
});
