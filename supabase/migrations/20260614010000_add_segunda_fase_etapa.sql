-- =====================================================================
-- Etapa "Segunda Fase"
--
-- A Copa do Mundo de 2026 (48 seleções) tem uma fase eliminatória extra
-- entre a Fase de Grupos e as Oitavas de Final.
-- =====================================================================

alter table public.matches drop constraint matches_etapa_check;

alter table public.matches add constraint matches_etapa_check check (etapa in (
  'Fase de Grupos', 'Segunda Fase', 'Oitavas de Final', 'Quartas de Final',
  'Semifinal', 'Disputa de 3º Lugar', 'Final'
));
