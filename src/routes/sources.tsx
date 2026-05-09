import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Plus, Trash2, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sourceStore, SEED_SOURCES } from "@/lib/storage";
import { DOMAIN_LABELS, type Domain, type Source } from "@/lib/types";

export const Route = createFileRoute("/sources")({ component: SourcesPage });

const DOMAINS: Domain[] = ["finance", "supply_chain", "marketing", "ai_content"];

function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [domain, setDomain] = useState<Domain>("finance");

  useEffect(() => setSources(sourceStore.list()), []);

  function update(next: Source[]) {
    setSources(next);
    sourceStore.set(next);
  }

  function add() {
    if (!name.trim() || !url.trim()) {
      toast.error("Name and URL are required");
      return;
    }
    try {
      new URL(url);
    } catch {
      toast.error("Invalid URL");
      return;
    }
    const id = `${domain}-${Date.now()}`;
    update([...sources, { id, name: name.trim(), url: url.trim(), domain }]);
    setName("");
    setUrl("");
    toast.success("Source added");
  }

  function remove(id: string) {
    update(sources.filter((s) => s.id !== id));
  }

  function resetSeeds() {
    update(SEED_SOURCES);
    toast.success("Reset to curated seed sources");
  }

  const grouped = DOMAINS.map((d) => ({
    domain: d,
    items: sources.filter((s) => s.domain === d),
  }));

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Sources</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            URLs to scrape during each run. Stored in this browser.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={resetSeeds} className="gap-2">
          <RotateCcw className="h-3.5 w-3.5" />
          Reset to seed list
        </Button>
      </header>

      <section className="ss-card mb-8 p-4 md:p-5">
        <h2 className="mb-3 text-sm font-semibold">Add a source</h2>
        <div className="grid gap-2 md:grid-cols-[1fr_1.5fr_auto_auto]">
          <Input
            placeholder="Name (e.g. Reuters Markets)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            placeholder="https://example.com/articles"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value as Domain)}
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {DOMAIN_LABELS[d]}
              </option>
            ))}
          </select>
          <Button onClick={add} className="gap-2">
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </div>
      </section>

      <div className="space-y-6">
        {grouped.map(({ domain: d, items }) => (
          <section key={d}>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {DOMAIN_LABELS[d]} · {items.length}
            </h3>
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No sources yet.</p>
            ) : (
              <ul className="ss-card divide-y divide-border overflow-hidden">
                {items.map((s) => (
                  <li key={s.id} className="flex items-center gap-3 px-4 py-3">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">{s.name}</div>
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block truncate text-xs text-muted-foreground hover:text-primary"
                      >
                        {s.url}
                      </a>
                    </div>
                    <button
                      onClick={() => remove(s.id)}
                      aria-label="Remove source"
                      className="rounded-md p-2 text-muted-foreground transition hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
