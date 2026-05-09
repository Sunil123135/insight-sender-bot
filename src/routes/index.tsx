import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useEffect, useState } from "react";
import { Loader2, Play, Sparkles, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ItemCard, ItemSkeleton } from "@/components/ItemCard";
import { sourceStore, itemStore, savedStore, profileStore } from "@/lib/storage";
import { DOMAIN_LABELS, type Domain, type ScrapedItem, type Source } from "@/lib/types";
import { scrapeUrl } from "@/lib/scrape.functions";
import { summarizeContent } from "@/lib/summarize.functions";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({ component: Dashboard });

const PROFILES: Array<{ value: Domain | "all"; label: string }> = [
  { value: "all", label: "All domains" },
  { value: "finance", label: DOMAIN_LABELS.finance },
  { value: "supply_chain", label: DOMAIN_LABELS.supply_chain },
  { value: "marketing", label: DOMAIN_LABELS.marketing },
  { value: "ai_content", label: DOMAIN_LABELS.ai_content },
];

function Dashboard() {
  const scrape = useServerFn(scrapeUrl);
  const summarize = useServerFn(summarizeContent);

  const [profile, setProfile] = useState<Domain | "all">("all");
  const [sources, setSources] = useState<Source[]>([]);
  const [items, setItems] = useState<ScrapedItem[]>([]);
  const [saved, setSaved] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [failed, setFailed] = useState<{ source: Source; error: string }[]>([]);

  useEffect(() => {
    setSources(sourceStore.list());
    setItems(itemStore.list());
    setSaved(savedStore.list());
    setProfile(profileStore.get());
  }, []);

  const filteredItems =
    profile === "all" ? items : items.filter((i) => i.domain === profile);

  const targets =
    profile === "all" ? sources : sources.filter((s) => s.domain === profile);

  function changeProfile(p: Domain | "all") {
    setProfile(p);
    profileStore.set(p);
  }

  function toggleSave(id: string) {
    setSaved(savedStore.toggle(id));
  }

  async function runScrape(retrySources?: Source[]) {
    const list = retrySources ?? targets;
    if (list.length === 0) {
      toast.error("No sources to scrape", {
        description: "Add a source or pick a different profile.",
      });
      return;
    }
    setRunning(true);
    setFailed([]);
    setProgress({ done: 0, total: list.length });
    const newFailed: { source: Source; error: string }[] = [];
    const collected: ScrapedItem[] = [];

    for (let i = 0; i < list.length; i++) {
      const src = list[i];
      try {
        const scraped = await scrape({ data: { url: src.url } });
        if (!scraped.ok) {
          newFailed.push({ source: src, error: scraped.error });
          setProgress({ done: i + 1, total: list.length });
          continue;
        }
        const summary = await summarize({
          data: {
            url: src.url,
            domain: src.domain,
            content: scraped.content,
          },
        });
        if (!summary.ok) {
          newFailed.push({ source: src, error: summary.error });
        } else {
          for (const it of summary.items) {
            collected.push({
              id: `${src.id}-${i}-${collected.length}-${Date.now()}`,
              sourceId: src.id,
              sourceName: src.name,
              domain: src.domain,
              url: it.url || src.url,
              title: it.title,
              summary: it.summary,
              why: it.why,
              score: Math.round(it.score),
              takeaways: it.takeaways,
              scrapedAt: new Date().toISOString(),
            });
          }
        }
      } catch (e) {
        newFailed.push({
          source: src,
          error: e instanceof Error ? e.message : "unknown error",
        });
      }
      setProgress({ done: i + 1, total: list.length });
    }

    // Merge: replace items for the scraped sources, keep others
    const scrapedIds = new Set(list.map((s) => s.id));
    const merged = [
      ...collected,
      ...items.filter((it) => !scrapedIds.has(it.sourceId)),
    ].sort((a, b) => b.score - a.score);

    setItems(merged);
    itemStore.set(merged);
    setFailed(newFailed);
    setRunning(false);
    toast.success(`Scrape complete`, {
      description: `${collected.length} item${collected.length === 1 ? "" : "s"} from ${list.length - newFailed.length}/${list.length} sources.`,
    });
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {sources.length} source{sources.length === 1 ? "" : "s"} · {items.length} item{items.length === 1 ? "" : "s"} in cache
          </p>
        </div>
        <Button
          size="lg"
          onClick={() => runScrape()}
          disabled={running}
          className="gap-2"
        >
          {running ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Scraping {progress.done}/{progress.total}
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Scrape Now
            </>
          )}
        </Button>
      </header>

      <div className="ss-card mb-6 flex flex-wrap items-center gap-2 p-3">
        <span className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Interest profile
        </span>
        {PROFILES.map((p) => (
          <button
            key={p.value}
            onClick={() => changeProfile(p.value)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition",
              profile === p.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-card text-foreground/80 hover:border-primary/40"
            )}
          >
            {p.label}
          </button>
        ))}
      </div>

      {running && (
        <div className="mb-6">
          <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
            <span>Scraped {progress.done} of {progress.total}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}

      {failed.length > 0 && (
        <details className="ss-card mb-6 p-4">
          <summary className="flex cursor-pointer items-center gap-2 text-sm font-semibold">
            <AlertTriangle className="h-4 w-4 text-warning-foreground" />
            Failed ({failed.length})
            <button
              onClick={(e) => {
                e.preventDefault();
                runScrape(failed.map((f) => f.source));
              }}
              className="ml-auto rounded-md border border-border px-2 py-1 text-xs font-medium hover:border-primary"
            >
              Retry
            </button>
          </summary>
          <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
            {failed.map((f) => (
              <li key={f.source.id}>
                <span className="font-medium text-foreground/80">{f.source.name}</span> — {f.error}
              </li>
            ))}
          </ul>
        </details>
      )}

      {running && filteredItems.length === 0 ? (
        <div className="grid gap-3">
          <ItemSkeleton />
          <ItemSkeleton />
          <ItemSkeleton />
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="ss-card flex flex-col items-center justify-center px-6 py-16 text-center">
          <Sparkles className="mb-3 h-8 w-8 text-primary" />
          <h2 className="text-lg font-semibold">Nothing scraped yet</h2>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Hit <span className="font-semibold">Scrape Now</span> to fetch your curated sources and get an AI-summarized brief.
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filteredItems.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              saved={saved.includes(item.id)}
              onToggleSave={toggleSave}
            />
          ))}
        </div>
      )}
    </div>
  );
}
