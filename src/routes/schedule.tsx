import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Save, Mail, Webhook, Send, Clock } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getSchedule, updateSchedule, listBriefs } from "@/lib/data.functions";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/schedule")({ component: SchedulePage });

type Channel = "email" | "n8n" | "both";

function SchedulePage() {
  const fetchCfg = useServerFn(getSchedule);
  const update = useServerFn(updateSchedule);
  const fetchBriefs = useServerFn(listBriefs);
  const qc = useQueryClient();

  const cfgQ = useQuery({ queryKey: ["schedule"], queryFn: () => fetchCfg() });
  const briefsQ = useQuery({ queryKey: ["briefs"], queryFn: () => fetchBriefs() });

  const [recipient, setRecipient] = useState("");
  const [channel, setChannel] = useState<Channel>("both");
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (cfgQ.data) {
      setRecipient(cfgQ.data.recipient_email);
      setChannel(cfgQ.data.channel as Channel);
      setEnabled(cfgQ.data.enabled);
    }
  }, [cfgQ.data]);

  const saveM = useMutation({
    mutationFn: () => update({ data: { recipient_email: recipient, channel, enabled } }),
    onSuccess: () => {
      toast.success("Schedule saved");
      qc.invalidateQueries({ queryKey: ["schedule"] });
    },
    onError: (e: Error) => toast.error("Save failed", { description: e.message }),
  });

  const channels: Array<{ value: Channel; label: string; icon: typeof Mail }> = [
    { value: "email", label: "Email only", icon: Mail },
    { value: "n8n", label: "n8n webhook", icon: Webhook },
    { value: "both", label: "Both", icon: Send },
  ];

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Schedule & Delivery</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The brief runs daily at <span className="font-semibold text-foreground/90">7:00 AM IST</span> (01:30 UTC).
        </p>
      </header>

      <section className="ss-card mb-6 p-5 space-y-5">
        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Recipient email
          </label>
          <Input
            type="email"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Delivery channel
          </label>
          <div className="flex flex-wrap gap-2">
            {channels.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setChannel(value)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition",
                  channel === value
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-card hover:border-primary/40"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-input"
          />
          Enabled (daily auto-send at 7 AM IST)
        </label>

        <Button onClick={() => saveM.mutate()} disabled={saveM.isPending} className="gap-2">
          <Save className="h-4 w-4" />Save schedule
        </Button>
      </section>

      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        <Clock className="h-4 w-4" /> Recent runs
      </h2>
      <div className="grid gap-2">
        {briefsQ.data?.length === 0 && (
          <div className="ss-card p-4 text-sm text-muted-foreground">No runs yet.</div>
        )}
        {briefsQ.data?.map((b) => (
          <div key={b.id} className="ss-card flex flex-wrap items-center gap-3 p-3 text-sm">
            <span className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
              b.status === "sent" ? "bg-success text-success-foreground" :
              b.status === "partial" ? "bg-warning text-warning-foreground" :
              b.status === "failed" ? "bg-destructive text-destructive-foreground" :
              "bg-muted text-muted-foreground"
            )}>
              {b.status}
            </span>
            <span className="text-muted-foreground">
              {new Date(b.generated_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}
            </span>
            <span className="font-semibold">{b.item_count} items</span>
            {b.detail && <span className="text-xs text-muted-foreground truncate flex-1">{b.detail}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
