-- Seed default built-in scraper sources (scraper:// protocol)
insert into public.sources (name, url, domain, active)
select v.name, v.url, v.domain, v.active
from (values
  ('Keep Up Daily (HN + Dev.to + Reddit)', 'scraper://keep-up-daily', 'ai_content', true),
  ('GitHub Trending (webScrapers)', 'scraper://github-trending', 'ai_content', true),
  ('YouTube Metadata (yt-dlp)', 'scraper://youtube-feed', 'ai_content', true),
  ('Trending Tech News', 'scraper://trending-news', 'ai_content', true)
) as v(name, url, domain, active)
where not exists (
  select 1 from public.sources s where s.url = v.url
);
