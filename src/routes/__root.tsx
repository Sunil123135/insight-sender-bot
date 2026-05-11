import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";

import { useEffect, useState } from "react";

import appCss from "../styles.css?url";
import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { ALLOWED_EMAIL } from "@/lib/auth-guard";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong on our end. You can try refreshing or head back home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "ScrapeSignal — Daily intelligence brief" },
      { name: "description", content: "Scrape curated sources across Finance, Supply Chain, Marketing, and AI/Content. Get an AI-summarized brief delivered via email or n8n." },
      { name: "author", content: "ScrapeSignal" },
      { property: "og:title", content: "ScrapeSignal — Daily intelligence brief" },
      { property: "og:description", content: "Scrape curated sources across Finance, Supply Chain, Marketing, and AI/Content. Get an AI-summarized brief delivered via email or n8n." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "twitter:site", content: "@Lovable" },
      { name: "twitter:title", content: "ScrapeSignal — Daily intelligence brief" },
      { name: "twitter:description", content: "Scrape curated sources across Finance, Supply Chain, Marketing, and AI/Content. Get an AI-summarized brief delivered via email or n8n." },
      { property: "og:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/09585fe4-028a-4035-9277-f67b5458d68c/id-preview-3bcb9dc7--ea40cd0b-1860-4730-a636-c2c5953c8993.lovable.app-1778317852002.png" },
      { name: "twitter:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/09585fe4-028a-4035-9277-f67b5458d68c/id-preview-3bcb9dc7--ea40cd0b-1860-4730-a636-c2c5953c8993.lovable.app-1778317852002.png" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  const router = useRouter();
  const [authState, setAuthState] = useState<"loading" | "in" | "out">("loading");

  useEffect(() => {
    let mounted = true;
    const check = (email: string | undefined) => {
      if (!mounted) return;
      setAuthState(email?.toLowerCase() === ALLOWED_EMAIL.toLowerCase() ? "in" : "out");
    };
    supabase.auth.getSession().then(({ data }) => check(data.session?.user?.email));
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      check(session?.user?.email);
      router.invalidate();
    });
    return () => { mounted = false; sub.subscription.unsubscribe(); };
  }, [router]);

  const path = router.state.location.pathname;
  const isLoginRoute = path === "/login";

  return (
    <QueryClientProvider client={queryClient}>
      {isLoginRoute || authState === "in" ? (
        <div className="min-h-screen md:flex">
          {!isLoginRoute && <Sidebar />}
          <main className="flex-1 px-4 pb-20 pt-6 md:px-10 md:pb-10">
            <Outlet />
          </main>
        </div>
      ) : authState === "loading" ? (
        <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>
      ) : (
        <RedirectToLogin />
      )}
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}

function RedirectToLogin() {
  const router = useRouter();
  useEffect(() => { router.navigate({ to: "/login" }); }, [router]);
  return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Redirecting…</div>;
}
