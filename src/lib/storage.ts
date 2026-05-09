import type { Source, ScrapedItem, Domain } from "./types";

const SOURCES_KEY = "scrapesignal.sources.v1";
const SAVED_KEY = "scrapesignal.saved.v1";
const ITEMS_KEY = "scrapesignal.items.v1";
const PROFILE_KEY = "scrapesignal.profile.v1";

export const SEED_SOURCES: Source[] = [
  // Finance
  { id: "fin-reuters", name: "Reuters Business", url: "https://www.reuters.com/business/", domain: "finance" },
  { id: "fin-ft", name: "FT Markets", url: "https://www.ft.com/markets", domain: "finance" },
  { id: "fin-stratechery", name: "Stratechery", url: "https://stratechery.com/", domain: "finance" },
  // Supply Chain
  { id: "sc-dive", name: "Supply Chain Dive", url: "https://www.supplychaindive.com/", domain: "supply_chain" },
  { id: "sc-freightwaves", name: "FreightWaves", url: "https://www.freightwaves.com/", domain: "supply_chain" },
  // Marketing
  { id: "mkt-brew", name: "Marketing Brew", url: "https://www.marketingbrew.com/", domain: "marketing" },
  { id: "mkt-hubspot", name: "HubSpot Marketing Blog", url: "https://blog.hubspot.com/marketing", domain: "marketing" },
  // AI / Content
  { id: "ai-anthropic", name: "Anthropic News", url: "https://www.anthropic.com/news", domain: "ai_content" },
  { id: "ai-batch", name: "The Batch (Andrew Ng)", url: "https://www.deeplearning.ai/the-batch/", domain: "ai_content" },
];

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}
function write<T>(key: string, value: T) {
  if (typeof window === "undefined") return;
  localStorage.setItem(key, JSON.stringify(value));
}

export const sourceStore = {
  list: (): Source[] => {
    const cur = read<Source[] | null>(SOURCES_KEY, null);
    if (cur === null) {
      write(SOURCES_KEY, SEED_SOURCES);
      return SEED_SOURCES;
    }
    return cur;
  },
  set: (sources: Source[]) => write(SOURCES_KEY, sources),
};

export const itemStore = {
  list: (): ScrapedItem[] => read<ScrapedItem[]>(ITEMS_KEY, []),
  set: (items: ScrapedItem[]) => write(ITEMS_KEY, items),
};

export const savedStore = {
  list: (): string[] => read<string[]>(SAVED_KEY, []),
  set: (ids: string[]) => write(SAVED_KEY, ids),
  toggle: (id: string) => {
    const cur = savedStore.list();
    const next = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
    savedStore.set(next);
    return next;
  },
};

export const profileStore = {
  get: (): Domain | "all" => read<Domain | "all">(PROFILE_KEY, "all"),
  set: (p: Domain | "all") => write(PROFILE_KEY, p),
};
