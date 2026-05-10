import { Link, useLocation } from "@tanstack/react-router";
import { Activity, Database, Calendar, Radio } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: Activity },
  { to: "/sources", label: "Sources", icon: Database },
  { to: "/schedule", label: "Schedule", icon: Calendar },
] as const;

export function Sidebar() {
  const loc = useLocation();
  return (
    <>
      <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-sidebar-border md:bg-sidebar md:px-4 md:py-6">
        <Link to="/" className="mb-8 flex items-center gap-2 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Radio className="h-4 w-4" />
          </div>
          <div className="leading-tight">
            <div className="text-base font-bold tracking-tight">ScrapeSignal</div>
            <div className="text-[11px] text-muted-foreground">Daily AI brief · 7am IST</div>
          </div>
        </Link>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = loc.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground/80 hover:bg-sidebar-accent hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto rounded-xl border border-border bg-accent/40 p-3 text-[11px] leading-relaxed text-muted-foreground">
          New models · AI · consciousness · spirituality · vision · LLMs. Auto-delivered every morning.
        </div>
      </aside>

      <nav className="fixed inset-x-0 bottom-0 z-50 flex border-t border-border bg-card md:hidden">
        {NAV.map(({ to, label, icon: Icon }) => {
          const active = loc.pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex flex-1 flex-col items-center justify-center gap-1 py-2 text-[11px] font-medium",
                active ? "text-primary" : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
