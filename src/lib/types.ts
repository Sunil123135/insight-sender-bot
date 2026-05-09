export type Domain = "finance" | "supply_chain" | "marketing" | "ai_content";

export const DOMAIN_LABELS: Record<Domain, string> = {
  finance: "Finance",
  supply_chain: "Supply Chain",
  marketing: "Marketing",
  ai_content: "AI & Content",
};

export interface Source {
  id: string;
  name: string;
  url: string;
  domain: Domain;
}

export interface ScrapedItem {
  id: string;          // hash of url+timestamp
  sourceId: string;
  sourceName: string;
  domain: Domain;
  url: string;         // canonical link to the article (best effort)
  title: string;
  summary: string;     // 2-3 sentence summary
  why: string;         // why it matters for the domain
  score: number;       // 0-10 relevance
  takeaways: string[]; // bullets
  scrapedAt: string;   // ISO
}

export interface BriefPayload {
  generatedAt: string;
  interestProfile: Domain | "all";
  items: Array<{
    title: string;
    url: string;
    source: string;
    domain: Domain;
    summary: string;
    why: string;
    score: number;
    takeaways: string[];
  }>;
}
