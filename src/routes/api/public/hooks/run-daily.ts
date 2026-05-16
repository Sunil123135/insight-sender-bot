// Daily run cron endpoint — invoked by pg_cron. Delegates to the shared runDaily implementation.
import { createFileRoute } from "@tanstack/react-router";
import { runDaily } from "@/lib/run-daily.server";

function timingSafeEq(a: string, b: string) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function authorized(request: Request) {
  const expected = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!expected) return false;
  const header = request.headers.get("authorization") ?? "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  return token.length > 0 && timingSafeEq(token, expected);
}

export const Route = createFileRoute("/api/public/hooks/run-daily")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        if (!authorized(request)) {
          return new Response(JSON.stringify({ ok: false, error: "unauthorized" }), {
            status: 401,
            headers: { "content-type": "application/json" },
          });
        }
        try {
          const out = await runDaily();
          return new Response(JSON.stringify(out), {
            status: out.ok ? 200 : 500,
            headers: { "content-type": "application/json" },
          });
        } catch (e) {
          return new Response(
            JSON.stringify({ ok: false, error: e instanceof Error ? e.message : "unknown" }),
            { status: 500, headers: { "content-type": "application/json" } }
          );
        }
      },
      GET: async () =>
        new Response(
          JSON.stringify({ ok: true, hint: "POST with bearer token to run the daily brief" }),
          { headers: { "content-type": "application/json" } }
        ),
    },
  },
});
