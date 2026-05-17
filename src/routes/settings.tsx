import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Save, KeyRound, AtSign, ExternalLink, CheckCircle2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getResendSettings, updateResendFromAddress } from "@/lib/data.functions";

export const Route = createFileRoute("/settings")({ component: SettingsPage });

function SettingsPage() {
  const fetchSettings = useServerFn(getResendSettings);
  const updateFrom = useServerFn(updateResendFromAddress);
  const qc = useQueryClient();

  const q = useQuery({ queryKey: ["resend-settings"], queryFn: () => fetchSettings() });
  const [fromAddress, setFromAddress] = useState("");

  useEffect(() => {
    if (q.data) setFromAddress(q.data.fromAddress);
  }, [q.data]);

  const saveM = useMutation({
    mutationFn: () => updateFrom({ data: { from_address: fromAddress.trim() } }),
    onSuccess: () => {
      toast.success("From address updated");
      qc.invalidateQueries({ queryKey: ["resend-settings"] });
    },
    onError: (e: Error) => toast.error("Save failed", { description: e.message }),
  });

  const usingTestSender = fromAddress.includes("onboarding@resend.dev");

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Resend Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your Resend API key and the verified sender address used for daily briefs.
        </p>
      </header>

      {/* API Key */}
      <section className="ss-card mb-6 p-5">
        <div className="mb-3 flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold uppercase tracking-wide">API Key</h2>
        </div>

        {q.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : q.data?.hasApiKey ? (
          <div className="flex items-start gap-2 rounded-lg border border-success/30 bg-success/10 p-3 text-sm">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-success" />
            <div>
              <div className="font-medium text-foreground">Configured</div>
              <div className="text-xs text-muted-foreground">
                Your Resend API key is stored as a server secret. For security, it is never displayed in the app.
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-destructive" />
            <div>
              <div className="font-medium text-foreground">Not configured</div>
              <div className="text-xs text-muted-foreground">
                Ask the assistant in chat: "update my Resend API key" to securely set it.
              </div>
            </div>
          </div>
        )}

        <p className="mt-3 text-xs text-muted-foreground">
          To rotate the key, message the assistant — keys are stored as encrypted server secrets and
          cannot be edited from this UI. Get a fresh key at{" "}
          <a
            href="https://resend.com/api-keys"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-0.5 text-primary underline"
          >
            resend.com/api-keys <ExternalLink className="h-3 w-3" />
          </a>
          .
        </p>
      </section>

      {/* From Address */}
      <section className="ss-card p-5 space-y-4">
        <div className="flex items-center gap-2">
          <AtSign className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold uppercase tracking-wide">Verified "From" Address</h2>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            From address
          </label>
          <Input
            value={fromAddress}
            onChange={(e) => setFromAddress(e.target.value)}
            placeholder="ScrapeSignal <brief@mail.yourdomain.com>"
            disabled={q.isLoading}
          />
          <p className="mt-1.5 text-xs text-muted-foreground">
            Format: <code className="rounded bg-muted px-1 py-0.5">Name &lt;email@domain&gt;</code> or just{" "}
            <code className="rounded bg-muted px-1 py-0.5">email@domain</code>.
          </p>
        </div>

        {usingTestSender && (
          <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning" />
            <div className="text-foreground/90">
              You're using Resend's test sender (<code>onboarding@resend.dev</code>). It can only deliver
              to the email address that owns your Resend account. To send to anyone, verify a domain at{" "}
              <a
                href="https://resend.com/domains"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-0.5 text-primary underline"
              >
                resend.com/domains <ExternalLink className="h-3 w-3" />
              </a>{" "}
              then update this field to use it.
            </div>
          </div>
        )}

        <Button
          onClick={() => saveM.mutate()}
          disabled={saveM.isPending || !fromAddress.trim() || fromAddress === q.data?.fromAddress}
          className="gap-2"
        >
          <Save className="h-4 w-4" />
          Save from address
        </Button>
      </section>
    </div>
  );
}
