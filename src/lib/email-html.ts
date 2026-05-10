// Email HTML builder for the daily brief — runs on the server.
export interface BriefItem {
  title: string;
  url: string;
  source: string;
  summary: string;
  why: string;
  whats_new: string;
  whats_changing: string;
  whats_coming: string;
  for_me: string;
  to_learn: string;
  monetize: string;
  score: number;
  takeaways: string[];
  image_url: string | null;
}

function esc(s: string): string {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function lensRow(label: string, value: string, color: string): string {
  if (!value) return "";
  return `<tr>
    <td style="padding:4px 10px 4px 0;vertical-align:top;width:140px;">
      <span style="display:inline-block;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:${color};">${esc(label)}</span>
    </td>
    <td style="padding:4px 0;font-size:13px;color:#0f172a;line-height:1.55;">${esc(value)}</td>
  </tr>`;
}

function renderItem(it: BriefItem): string {
  const img = it.image_url
    ? `<img src="${esc(it.image_url)}" alt="" style="display:block;width:100%;max-height:240px;object-fit:cover;border-radius:10px;margin:0 0 14px;" />`
    : "";
  const takeaways = it.takeaways.length
    ? `<ul style="margin:10px 0 0 18px;padding:0;color:#334155;font-size:13px;">${it.takeaways
        .map((t) => `<li style="margin:3px 0;">${esc(t)}</li>`)
        .join("")}</ul>`
    : "";
  return `<div style="border:1px solid #e2e8f0;border-radius:14px;padding:18px;margin:14px 0;background:#ffffff;">
    ${img}
    <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">
      ${esc(it.source)} · score ${it.score}/10
    </div>
    <h3 style="margin:0 0 10px;font-size:18px;line-height:1.3;">
      <a href="${esc(it.url)}" style="color:#1F3864;text-decoration:none;">${esc(it.title)}</a>
    </h3>
    <p style="margin:0 0 12px;color:#0f172a;font-size:14px;line-height:1.55;">${esc(it.summary)}</p>
    <table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin-top:6px;">
      ${lensRow("What's new",      it.whats_new,      "#0ea5e9")}
      ${lensRow("What's changing", it.whats_changing, "#8b5cf6")}
      ${lensRow("What's next",     it.whats_coming,   "#ec4899")}
      ${lensRow("For you",         it.for_me,         "#10b981")}
      ${lensRow("To learn",        it.to_learn,       "#f59e0b")}
      ${lensRow("Monetize",        it.monetize,       "#ef4444")}
      ${it.why ? lensRow("Why it matters", it.why, "#475569") : ""}
    </table>
    ${takeaways}
  </div>`;
}

export function buildBriefHtml(items: BriefItem[], date: string): string {
  const sorted = [...items].sort((a, b) => b.score - a.score);
  return `<!doctype html><html><body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:28px 20px;">
    <div style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748b;">Daily Intelligence Brief</div>
      <h1 style="margin:6px 0 0;font-size:26px;color:#0f172a;">ScrapeSignal · ${esc(date)}</h1>
      <p style="margin:6px 0 0;color:#64748b;font-size:13px;">${sorted.length} item${sorted.length === 1 ? "" : "s"} across new models, AI, consciousness, spirituality, vision & LLMs.</p>
    </div>
    ${sorted.map(renderItem).join("")}
    <p style="color:#94a3b8;font-size:11px;margin-top:28px;text-align:center;">Sent automatically by ScrapeSignal · 7:00 AM IST</p>
  </div></body></html>`;
}
