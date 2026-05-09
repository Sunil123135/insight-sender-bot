import type { ScrapedItem } from "@/lib/types";
import { DOMAIN_LABELS } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ExternalLink, Star } from "lucide-react";

function scoreClass(score: number) {
  if (score >= 8) return "bg-success text-success-foreground";
  if (score >= 5) return "bg-warning text-warning-foreground";
  return "bg-muted text-muted-foreground";
}

interface Props {
  item: ScrapedItem;
  saved: boolean;
  onToggleSave: (id: string) => void;
}

export function ItemCard({ item, saved, onToggleSave }: Props) {
  return (
    <article className="ss-card group p-5 transition hover:shadow-md">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-muted-foreground">
        <span className="font-semibold text-foreground/70">{item.sourceName}</span>
        <span>·</span>
        <span>{DOMAIN_LABELS[item.domain]}</span>
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
      <p className="mb-2 text-sm text-foreground/85">{item.summary}</p>
      <p className="mb-3 text-sm text-muted-foreground">
        <span className="font-semibold text-foreground/80">Why it matters: </span>
        {item.why}
      </p>
      {item.takeaways.length > 0 && (
        <ul className="mb-3 list-disc space-y-1 pl-5 text-sm text-foreground/80">
          {item.takeaways.map((t, i) => (
            <li key={i}>{t}</li>
          ))}
        </ul>
      )}
      <div className="flex items-center justify-end">
        <button
          onClick={() => onToggleSave(item.id)}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
            saved
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border bg-card hover:border-primary/40 hover:text-primary"
          )}
          aria-label={saved ? "Unsave" : "Save"}
        >
          <Star className={cn("h-3.5 w-3.5", saved && "fill-current")} />
          {saved ? "Saved" : "Save"}
        </button>
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
