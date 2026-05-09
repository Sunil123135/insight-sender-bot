import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useEffect, useMemo, useState } from "react";
import { Send, Loader2, Mail, Webhook, Inbox } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ItemCard } from "@/components/ItemCard";
import { itemStore, savedStore, profileStore } from "@/lib/storage";
import type { ScrapedItem } from "@/lib/types";
import { sendBrief } from "@/lib/send-brief.functions";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/brief")({ component: BriefPage });

type Channel = "n8n" | "email" | "both";

function BriefPage() {
  const send = useServerFn(sendBrief);
  const [items, setItems] = useState<ScrapedItem[]>([]);
  const [saved, setSaved] = useState<string[]>([]);
  const [channel, setChannel] = useState<Channel>("n8n");
  const [recipient, setRecipient] = useState("");
  const [sending, setSending] = useState(false);
  const profile = useMemo(() => profileStore.get(), []);

  useEffect(() => {
    setItems(itemStore.list());
    setSaved(savedStore.list());
  }, []);

  function toggleSave(id: string) {
    setSaved(savedStore.toggle(id));
  }

  const savedItems = items
    .filter((i) => saved.includes(i.id))
    .sort((a, b) => b.score - a.score);

  async function handleSend() {
    if (savedItems.length === 0) {
      toast.error("No saved items", { description: "Save items from the Dashboard first." });
      return;
    }
    if ((channel === "email" || channel === "both") && !recipient) {
      toast.error("Recipient email required");
      return;
    }
    setSending(true);
    try {
      const res = await send({
        data: {
          channel,
          recipientEmail: recipient || undefined,
          interestProfile: profile,
          items: savedItems.map((i) => ({
            title: i.title,
            url: i.url,
            source: i.sourceName,
            domain: i.domain,
            summary: i.summary,
            why: i.why,
            score: i.score,
            takeaways: i.takeaways,
          })),
        },
      });
      for (const r of res.results) {
        if (r.ok) toast.success(`${r.channel}: ${r.detail}`);
        else toast.error(`${r.channel} failed`, { description: r.detail });
      }
    } catch (e) {
      toast.error("Send failed", {
        description: e instanceof Error ? e.message : "unknown error",
      });
    } finally {
      setSending(false);
    }
  }

  const channels: { value: Channel; label: string; icon: typeof Mail }[] = [
    { value: "n8n", label: "n8n webhook", icon: Webhook },
    { value: "email", label: "Email (Resend)", icon: Mail },
    { value: "both", label: "Both", icon: Send },
  ];

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Today's Brief</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {savedItems.length} saved item{savedItems.length === 1 ? "" : "s"} · profile {profile}
        </p>
      </header>

      <section className="ss-card mb-6 p-4 md:p-5">
        <div className="mb-3 flex flex-wrap gap-2">
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
        {(channel === "email" || channel === "both") && (
          <Input
            type="email"
            placeholder="recipient@example.com"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            className="mb-3"
          />
        )}
        <Button onClick={handleSend} disabled={sending} className="gap-2 w-full md:w-auto">
          {sending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Sending…
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              Send Brief
            </>
          )}
        </Button>
        <p className="mt-2 text-xs text-muted-foreground">
          n8n posts the brief JSON to your <code>N8N_WEBHOOK_URL</code>. Email goes via Resend
          from <code>onboarding@resend.dev</code>.
        </p>
      </section>

      {savedItems.length === 0 ? (
        <div className="ss-card flex flex-col items-center justify-center px-6 py-16 text-center">
          <Inbox className="mb-3 h-8 w-8 text-primary" />
          <h2 className="text-lg font-semibold">No saved items yet</h2>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Open the Dashboard, run a scrape, and tap <span className="font-semibold">Save</span> on the items you want in the brief.
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {savedItems.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              saved
              onToggleSave={toggleSave}
            />
          ))}
        </div>
      )}
    </div>
  );
}
