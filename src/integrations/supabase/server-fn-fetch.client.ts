// Client-only: patch global fetch so server function calls (/_serverFn/*)
// include the current Supabase session bearer token.
import { supabase } from "./client";

declare global {
  // eslint-disable-next-line no-var
  var __serverFnFetchPatched: boolean | undefined;
}

if (typeof window !== "undefined" && !globalThis.__serverFnFetchPatched) {
  globalThis.__serverFnFetchPatched = true;
  const originalFetch = globalThis.fetch.bind(globalThis);

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    let url = "";
    try {
      if (typeof input === "string") url = input;
      else if (input instanceof URL) url = input.toString();
      else url = (input as Request).url;
    } catch {
      /* noop */
    }

    if (url.includes("/_serverFn/")) {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (token) {
        const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));
        if (!headers.has("authorization")) headers.set("authorization", `Bearer ${token}`);
        return originalFetch(input, { ...init, headers });
      }
    }
    return originalFetch(input, init);
  }) as typeof fetch;
}

export {};
