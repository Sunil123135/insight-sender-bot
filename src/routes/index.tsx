import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Loader2, Play, Sparkles, Mail, Webhook } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ItemCard, ItemSkeleton } from "@/components/ItemCard";
import { listLatestItems, listBriefs, triggerRunNow, getSchedule } from "@/lib/data.functions";

export const Route = createFileRoute("/")({ component: Dashboard });

function Dashboard() {
  const fetchItems = useServerFn(listLatestItems);
  const fetchBriefs = useServerFn(listBriefs);
  const fetchSchedule = useServerFn(getSchedule);
  const runNow = useServerFn(triggerRunNow);
  const qc = useQueryClient();
  const [running, setRunning] = useState(false);

  const itemsQ = useQuery({ queryKey: ["items"], queryFn: () => fetchItems() });
  const briefsQ = useQuery({ queryKey: ["briefs"], queryFn: () => fetchBriefs() });
  const schedQ = useQuery({ queryKey: ["schedule"], queryFn: () => fetchSchedule() });

  const items = itemsQ.data ?? [];
  const lastBrief = briefsQ.data?.[0];

  const run = useMutation({
    mutationFn: () => runNow(),
    onMutate: () => setRunning(true),
    onSuccess: (res) => {
      const ok = (res as { ok?: boolean }).ok;
      if (ok) toast.success("Brief sent", { description: `Delivered ${(res as { itemCount?: number }).itemCount ?? 0} items.` });
      else toast.error("Run finished with issues", { description: (res as { error?: string }).error ?? "see history" });
      qc.invalidateQueries({ queryKey: ["items"] });
      qc.invalidateQueries({ queryKey: ["briefs"] });
    },
    onError: (e: Error) => toast.error("Run failed", { description: e.message }),
    onSettled: () => setRunning(false),
  });

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Today's Brief</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {schedQ.data ? (
              <>
                Daily at <span className="font-semibold text-foreground/90">7:00 AM IST</span> →{" "}
                <span className="font-semibold text-foreground/90">{schedQ.data.recipient_email}</span>
                {" · "}
                channel: <span className="font-semibold text-foreground/90">{schedQ.data.channel}</span>
              </>
            ) : (
              "Loading schedule…"
            )}
          </p>
        </div>
        <Button size="lg" onClick={() => run.mutate()} disabled={running} className="gap-2">
          {running ? (
            <><Loader2 className="h-4 w-4 animate-spin" />Running…</>
          ) : (
            <><Play className="h-4 w-4" />Run & Send Now</>
          )}
        </Button>
      </header>

      {lastBrief && (
        <div className="ss-card mb-6 flex flex-wrap items-center gap-3 p-4 text-sm">
          <div className="flex items-center gap-2">
            {lastBrief.channel.includes("email") || lastBrief.channel === "both" ? (
              <Mail className="h-4 w-4 text-primary" />
            ) : null}
            {lastBrief.channel.includes("n8n") || lastBrief.channel === "both" ? (
              <Webhook className="h-4 w-4 text-primary" />
            ) : null}
          </div>
          <div className="flex-1">
            <div className="font-semibold">
              Last brief · {new Date(lastBrief.generated_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}
            </div>
            <div className="text-xs text-muted-foreground">
              {lastBrief.item_count} items · status {lastBrief.status}
              {lastBrief.detail && ` · ${lastBrief.detail}`}
            </div>
          </div>
        </div>
      )}

      {itemsQ.isLoading || running ? (
        <div className="grid gap-3"><ItemSkeleton /><ItemSkeleton /><ItemSkeleton /></div>
      ) : items.length === 0 ? (
        <div className="ss-card flex flex-col items-center justify-center px-6 py-16 text-center">
          <Sparkles className="mb-3 h-8 w-8 text-primary" />
          <h2 className="text-lg font-semibold">No brief yet</h2>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Tap <span className="font-semibold">Run & Send Now</span> to generate the first brief — it'll also auto-deliver every morning at 7 AM IST.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {items.map((it) => <ItemCard key={it.id} item={it} />)}
        </div>
      )}
    </div>
  );
}
