import type { Tables } from "@/integrations/supabase/types";
import { ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

type Item = Tables<"items">;

function scoreClass(score: number) {
  if (score >= 8) return "bg-success text-success-foreground";
  if (score >= 5) return "bg-warning text-warning-foreground";
  return "bg-muted text-muted-foreground";
}

const LENSES: Array<{ key: keyof Item; label: string; color: string }> = [
  { key: "whats_new",      label: "What's new",      color: "text-sky-500" },
  { key: "whats_changing", label: "What's changing", color: "text-violet-500" },
  { key: "whats_coming",   label: "What's next",     color: "text-pink-500" },
  { key: "for_me",         label: "For you",         color: "text-emerald-500" },
  { key: "to_learn",       label: "To learn",        color: "text-amber-500" },
  { key: "monetize",       label: "Monetize",        color: "text-red-500" },
];

export function ItemCard({ item }: { item: Item }) {
  const takeaways = (item.takeaways as string[] | null) ?? [];
  return (
    <article className="ss-card group overflow-hidden p-0 transition hover:shadow-md">
      {item.image_url && (
        <div className="aspect-[16/7] w-full overflow-hidden bg-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={item.image_url}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover transition group-hover:scale-[1.02]"
            onError={(e) => ((e.currentTarget.style.display = "none"))}
          />
        </div>
      )}
      <div className="p-5">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-muted-foreground">
          <span className="font-semibold text-foreground/70">{item.source_name}</span>
          <span
            className={cn(
              "ml-auto rounded-full px-2 py-0.5 text-[11px] font-semibold",
              scoreClass(item.score)
            )}
          >
            {item.score}/10
          </span>
        </div>
        <h3 className="mb-2 text-base font-semibold leading-snug">
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-start gap-1 text-foreground hover:text-primary"
          >
            {item.title}
            <ExternalLink className="mt-1 h-3.5 w-3.5 opacity-0 transition group-hover:opacity-60" />
          </a>
        </h3>
        <p className="mb-3 text-sm text-foreground/85">{item.summary}</p>

        <dl className="mb-3 grid gap-1.5">
          {LENSES.map(({ key, label, color }) => {
            const val = item[key] as string | null;
            if (!val) return null;
            return (
              <div key={key} className="flex gap-2 text-sm">
                <dt
                  className={cn(
                    "min-w-[110px] shrink-0 text-[10px] font-bold uppercase tracking-wider",
                    color
                  )}
                >
                  {label}
                </dt>
                <dd className="text-foreground/85">{val}</dd>
              </div>
            );
          })}
        </dl>

        {takeaways.length > 0 && (
          <ul className="list-disc space-y-1 pl-5 text-sm text-foreground/80">
            {takeaways.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}

export function ItemSkeleton() {
  return (
    <div className="ss-card animate-pulse p-5">
      <div className="mb-3 h-3 w-32 rounded bg-muted" />
      <div className="mb-2 h-4 w-3/4 rounded bg-muted" />
      <div className="mb-1.5 h-3 w-full rounded bg-muted" />
      <div className="h-3 w-5/6 rounded bg-muted" />
    </div>
  );
}
