// Server functions for DB-backed dashboard, sources, schedule, and manual run trigger.
// All functions require authentication AND match the allowed email.
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { supabaseAdmin } from "@/integrations/supabase/client.server";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { assertAllowed } from "@/lib/auth-guard";
import { runDaily } from "@/lib/run-daily.server";

export const listSources = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    assertAllowed(context.claims as { email?: string });
    const { data, error } = await supabaseAdmin
      .from("sources")
      .select("*")
      .order("created_at", { ascending: true });
    if (error) throw new Error(error.message);
    return data ?? [];
  });

const SourceInput = z.object({
  name: z.string().min(1).max(120),
  url: z.string().url().max(500),
  domain: z.string().min(1).max(40),
});

export const addSource = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => SourceInput.parse(d))
  .handler(async ({ data, context }) => {
    assertAllowed(context.claims as { email?: string });
    const { data: row, error } = await supabaseAdmin
      .from("sources")
      .insert(data)
      .select()
      .single();
    if (error) throw new Error(error.message);
    return row;
  });

export const deleteSource = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ id: z.string().uuid() }).parse(d))
  .handler(async ({ data, context }) => {
    assertAllowed(context.claims as { email?: string });
    const { error } = await supabaseAdmin.from("sources").delete().eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true };
  });

export const toggleSource = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ id: z.string().uuid(), active: z.boolean() }).parse(d))
  .handler(async ({ data, context }) => {
    assertAllowed(context.claims as { email?: string });
    const { error } = await supabaseAdmin
      .from("sources")
      .update({ active: data.active })
      .eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true };
  });

export const listLatestItems = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    assertAllowed(context.claims as { email?: string });
    const { data: latest } = await supabaseAdmin
      .from("briefs")
      .select("id")
      .order("generated_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (latest?.id) {
      const { data } = await supabaseAdmin
        .from("items")
        .select("*")
        .eq("brief_id", latest.id)
        .order("score", { ascending: false });
      return data ?? [];
    }
    const { data } = await supabaseAdmin
      .from("items")
      .select("*")
      .order("scraped_at", { ascending: false })
      .limit(30);
    return data ?? [];
  });

export const listBriefs = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    assertAllowed(context.claims as { email?: string });
    const { data, error } = await supabaseAdmin
      .from("briefs")
      .select("*")
      .order("generated_at", { ascending: false })
      .limit(20);
    if (error) throw new Error(error.message);
    return data ?? [];
  });

export const getSchedule = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    assertAllowed(context.claims as { email?: string });
    const { data, error } = await supabaseAdmin
      .from("schedule_config")
      .select("*")
      .eq("id", 1)
      .single();
    if (error) throw new Error(error.message);
    return data;
  });

const ScheduleInput = z.object({
  recipient_email: z.string().email(),
  channel: z.enum(["email", "n8n", "both"]),
  enabled: z.boolean(),
});

export const updateSchedule = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => ScheduleInput.parse(d))
  .handler(async ({ data, context }) => {
    assertAllowed(context.claims as { email?: string });
    const { error } = await supabaseAdmin
      .from("schedule_config")
      .update({ ...data, updated_at: new Date().toISOString() })
      .eq("id", 1);
    if (error) throw new Error(error.message);
    return { ok: true };
  });

export const triggerRunNow = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    assertAllowed(context.claims as { email?: string });
    // Run pipeline in the background — scraping + summarizing 20 sources can
    // take several minutes, far beyond the request timeout. Use Cloudflare's
    // waitUntil when available so the worker keeps the promise alive after
    // we return.
    const promise = runDaily().catch((e) => {
      console.error("runDaily background failure:", e);
    });
    const ctx = (globalThis as { __cfCtx?: { waitUntil?: (p: Promise<unknown>) => void } })
      .__cfCtx;
    if (ctx?.waitUntil) {
      ctx.waitUntil(promise);
    }
    return { ok: true as const, queued: true };
  });

