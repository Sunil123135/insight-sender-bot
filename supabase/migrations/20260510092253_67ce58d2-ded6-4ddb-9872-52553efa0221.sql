
-- sources to scrape
create table public.sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  url text not null,
  domain text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- scraped & summarized items
create table public.items (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references public.sources(id) on delete cascade,
  source_name text not null,
  domain text not null,
  url text not null,
  title text not null,
  summary text not null,
  why text not null default '',
  whats_new text default '',
  whats_changing text default '',
  whats_coming text default '',
  for_me text default '',
  to_learn text default '',
  monetize text default '',
  takeaways jsonb not null default '[]'::jsonb,
  image_url text,
  score int not null default 5,
  scraped_at timestamptz not null default now(),
  brief_id uuid
);
create index items_brief_idx on public.items(brief_id);
create index items_scraped_idx on public.items(scraped_at desc);

-- brief send history
create table public.briefs (
  id uuid primary key default gen_random_uuid(),
  generated_at timestamptz not null default now(),
  recipient_email text,
  channel text not null,
  item_count int not null default 0,
  status text not null default 'pending',
  detail text
);

-- single-row schedule config
create table public.schedule_config (
  id int primary key default 1,
  recipient_email text not null,
  channel text not null default 'both',
  enabled boolean not null default true,
  cron_utc text not null default '30 1 * * *',
  updated_at timestamptz not null default now(),
  constraint singleton check (id = 1)
);

-- RLS: public read, no public writes (server uses service role)
alter table public.sources enable row level security;
alter table public.items enable row level security;
alter table public.briefs enable row level security;
alter table public.schedule_config enable row level security;

create policy "public read sources" on public.sources for select using (true);
create policy "public read items" on public.items for select using (true);
create policy "public read briefs" on public.briefs for select using (true);
create policy "public read config" on public.schedule_config for select using (true);

-- seed config
insert into public.schedule_config (id, recipient_email, channel)
values (1, 'sunil.lalwani@quidelortho.com', 'both');

-- seed sources (Medium tags + arXiv listings)
insert into public.sources (name, url, domain) values
  ('Medium · Artificial Intelligence', 'https://medium.com/tag/artificial-intelligence', 'ai_content'),
  ('Medium · Large Language Models',  'https://medium.com/tag/large-language-models', 'ai_content'),
  ('Medium · Consciousness',          'https://medium.com/tag/consciousness', 'ai_content'),
  ('Medium · Spirituality',           'https://medium.com/tag/spirituality', 'ai_content'),
  ('Medium · Computer Vision',        'https://medium.com/tag/computer-vision', 'ai_content'),
  ('arXiv · cs.AI recent',            'https://arxiv.org/list/cs.AI/recent', 'ai_content'),
  ('arXiv · cs.CL recent',            'https://arxiv.org/list/cs.CL/recent', 'ai_content'),
  ('arXiv · cs.CV recent',            'https://arxiv.org/list/cs.CV/recent', 'ai_content');
