import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Plus, Trash2, Power } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { listSources, addSource, deleteSource, toggleSource } from "@/lib/data.functions";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/sources")({ component: SourcesPage });

const DOMAINS = [
  { value: "ai_content", label: "AI & Content" },
  { value: "finance", label: "Finance" },
  { value: "supply_chain", label: "Supply Chain" },
  { value: "marketing", label: "Marketing" },
];

function SourcesPage() {
  const list = useServerFn(listSources);
  const add = useServerFn(addSource);
  const del = useServerFn(deleteSource);
  const toggle = useServerFn(toggleSource);
  const qc = useQueryClient();

  const q = useQuery({ queryKey: ["sources"], queryFn: () => list() });
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [domain, setDomain] = useState("ai_content");

  const addM = useMutation({
    mutationFn: () => add({ data: { name, url, domain } }),
    onSuccess: () => {
      toast.success("Source added");
      setName(""); setUrl("");
      qc.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: (e: Error) => toast.error("Add failed", { description: e.message }),
  });

  const delM = useMutation({
    mutationFn: (id: string) => del({ data: { id } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  const toggleM = useMutation({
    mutationFn: (v: { id: string; active: boolean }) => toggle({ data: v }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Sources</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pages that get scraped every morning. Toggle off to skip without deleting.
        </p>
      </header>

      <section className="ss-card mb-6 grid gap-2 p-4 md:grid-cols-[1fr_1fr_140px_auto] md:items-center">
        <Input placeholder="Source name" value={name} onChange={(e) => setName(e.target.value)} />
        <Input placeholder="https://…" value={url} onChange={(e) => setUrl(e.target.value)} />
        <select
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-2 text-sm"
        >
          {DOMAINS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
        </select>
        <Button
          onClick={() => addM.mutate()}
          disabled={!name || !url || addM.isPending}
          className="gap-1"
        >
          <Plus className="h-4 w-4" />Add
        </Button>
      </section>

      <div className="grid gap-2">
        {q.isLoading && <div className="text-sm text-muted-foreground">Loading…</div>}
        {q.data?.map((s) => (
          <div
            key={s.id}
            className={cn(
              "ss-card flex items-center gap-3 p-3",
              !s.active && "opacity-60"
            )}
          >
            <div className="flex-1 min-w-0">
              <div className="truncate text-sm font-semibold">{s.name}</div>
              <a href={s.url} target="_blank" rel="noreferrer" className="truncate text-xs text-muted-foreground hover:text-primary block">
                {s.url}
              </a>
            </div>
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{s.domain}</span>
            <button
              onClick={() => toggleM.mutate({ id: s.id, active: !s.active })}
              className={cn(
                "rounded-md border p-1.5 transition",
                s.active ? "border-primary text-primary" : "border-border text-muted-foreground hover:border-primary"
              )}
              aria-label={s.active ? "Disable" : "Enable"}
            >
              <Power className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => delM.mutate(s.id)}
              className="rounded-md border border-border p-1.5 text-muted-foreground hover:border-destructive hover:text-destructive"
              aria-label="Delete"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
