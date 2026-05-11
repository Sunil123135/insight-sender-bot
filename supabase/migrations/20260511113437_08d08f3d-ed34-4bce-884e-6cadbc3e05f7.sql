
DROP POLICY IF EXISTS "public read briefs" ON public.briefs;
DROP POLICY IF EXISTS "public read items" ON public.items;
DROP POLICY IF EXISTS "public read config" ON public.schedule_config;
DROP POLICY IF EXISTS "public read sources" ON public.sources;

CREATE POLICY "authenticated read briefs" ON public.briefs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated read items" ON public.items
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated read config" ON public.schedule_config
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated read sources" ON public.sources
  FOR SELECT TO authenticated USING (true);
