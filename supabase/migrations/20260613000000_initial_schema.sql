-- =====================================================================
-- Copa Insights — schema inicial
-- =====================================================================

-- ---------------------------------------------------------------------
-- profiles (extensão de auth.users)
-- ---------------------------------------------------------------------
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  nome_completo text not null,
  email text not null,
  telefone text not null,
  perfil text not null default 'participante' check (perfil in ('administrador', 'participante')),
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index profiles_email_key on public.profiles (email);
create unique index profiles_telefone_key on public.profiles (telefone);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

-- Cria automaticamente o profile ao registrar um novo usuário no Supabase Auth
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, nome_completo, email, telefone, perfil)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'nome_completo', ''),
    new.email,
    coalesce(new.raw_user_meta_data ->> 'telefone', ''),
    'participante'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- Mantém profiles.email sincronizado se o usuário trocar o e-mail no Auth
create or replace function public.handle_user_email_update()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if new.email is distinct from old.email then
    update public.profiles set email = new.email where id = new.id;
  end if;
  return new;
end;
$$;

create trigger on_auth_user_email_updated
after update of email on auth.users
for each row execute function public.handle_user_email_update();

-- handle_new_user / handle_user_email_update existem apenas para os
-- triggers de auth.users; não devem ser chamáveis via RPC (PUBLIC/anon/authenticated).
revoke execute on function public.handle_new_user() from anon, authenticated, public;
revoke execute on function public.handle_user_email_update() from anon, authenticated, public;

-- ---------------------------------------------------------------------
-- matches (jogos)
-- ---------------------------------------------------------------------
create table public.matches (
  id bigint generated always as identity primary key,
  selecao_1 text not null,
  selecao_2 text not null,
  data_hora timestamptz not null,
  grupo text,
  etapa text not null check (etapa in (
    'Fase de Grupos', 'Oitavas de Final', 'Quartas de Final',
    'Semifinal', 'Disputa de 3º Lugar', 'Final'
  )),
  status text not null default 'Agendado' check (status in ('Agendado', 'Em andamento', 'Finalizado')),
  gols_selecao_1 int,
  gols_selecao_2 int,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index matches_status_idx on public.matches (status);
create index matches_data_hora_idx on public.matches (data_hora);

create trigger matches_set_updated_at
before update on public.matches
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------
-- predictions (palpites)
-- ---------------------------------------------------------------------
create table public.predictions (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.profiles (id) on delete cascade,
  match_id bigint not null references public.matches (id) on delete cascade,
  gols_selecao_1 int not null check (gols_selecao_1 >= 0),
  gols_selecao_2 int not null check (gols_selecao_2 >= 0),
  pontos int,
  data_aposta timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, match_id)
);

create index predictions_user_id_idx on public.predictions (user_id);
create index predictions_match_id_idx on public.predictions (match_id);

create trigger predictions_set_updated_at
before update on public.predictions
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------
-- audit_log (auditoria)
-- ---------------------------------------------------------------------
create table public.audit_log (
  id bigint generated always as identity primary key,
  user_id uuid references public.profiles (id) on delete set null,
  acao text not null,
  detalhe jsonb,
  created_at timestamptz not null default now()
);

create index audit_log_created_at_idx on public.audit_log (created_at desc);
create index audit_log_user_id_idx on public.audit_log (user_id);

-- ---------------------------------------------------------------------
-- Motor de pontuação
--   Acerto do vencedor (mesmo sinal de saldo de gols, inclui empate) = 1
--   Placar exato = 3 (não acumula com o ponto de vencedor)
--   Errou tudo = 0
-- ---------------------------------------------------------------------
create or replace function public.calculate_points(
  pred_1 int, pred_2 int, real_1 int, real_2 int
) returns int
language sql
immutable
set search_path = ''
as $$
  select case
    when real_1 is null or real_2 is null then null
    when pred_1 = real_1 and pred_2 = real_2 then 3
    when sign(pred_1 - pred_2) = sign(real_1 - real_2) then 1
    else 0
  end;
$$;

-- Recalcula os pontos de todos os palpites de um jogo específico
create or replace function public.recalculate_match_predictions(p_match_id bigint)
returns void
language plpgsql
security invoker
set search_path = ''
as $$
begin
  update public.predictions p
  set pontos = public.calculate_points(
    p.gols_selecao_1, p.gols_selecao_2, m.gols_selecao_1, m.gols_selecao_2
  )
  from public.matches m
  where m.id = p.match_id
    and p.match_id = p_match_id;
end;
$$;

-- Trigger: ao finalizar um jogo (ou corrigir o placar de um já finalizado),
-- recalcula automaticamente a pontuação dos palpites desse jogo (PDR §11)
create or replace function public.matches_after_result_update()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.status = 'Finalizado' then
    perform public.recalculate_match_predictions(new.id);
  end if;
  return new;
end;
$$;

create trigger matches_recalculate_predictions
after update of gols_selecao_1, gols_selecao_2, status on public.matches
for each row
when (new.status = 'Finalizado')
execute function public.matches_after_result_update();

-- RPC para o botão administrativo "Recalcular Ranking" (PDR §14):
-- reaplica a pontuação em todos os palpites de jogos finalizados.
-- security invoker -> respeita RLS (admin tem policy de update em todas as predictions)
create or replace function public.recalculate_all_rankings()
returns void
language plpgsql
security invoker
set search_path = ''
as $$
begin
  update public.predictions p
  set pontos = public.calculate_points(
    p.gols_selecao_1, p.gols_selecao_2, m.gols_selecao_1, m.gols_selecao_2
  )
  from public.matches m
  where m.id = p.match_id;
end;
$$;

-- ---------------------------------------------------------------------
-- Helper de autorização: administrador via app_metadata do JWT
-- (autorização via app_metadata, NUNCA via user_metadata — ver
-- security checklist da skill `supabase`). Encapsular em função evita
-- que o linter "auth_rls_initplan" detecte auth.jwt() bruto dentro das
-- policies e garante reavaliação única por query.
-- ---------------------------------------------------------------------
create or replace function public.is_admin()
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select coalesce((auth.jwt() -> 'app_metadata' ->> 'perfil') = 'administrador', false);
$$;

-- ---------------------------------------------------------------------
-- Views de leitura (dashboards / ranking)
--
-- IMPORTANTE: estas views NÃO usam security_invoker=true de propósito.
-- São agregados entre usuários (ranking geral, distribuição de palpites,
-- acertos por jogo) que TODO participante autenticado deve poder ler
-- (PDR §14/§17), mas a RLS de `predictions` restringe SELECT às próprias
-- linhas do usuário. Rodando como owner (sem security_invoker), a view
-- agrega todos os usuários; o acesso é controlado via GRANT (somente
-- `authenticated`, nunca `anon`) e as views só expõem colunas não
-- sensíveis (sem email/telefone). Isso aparece como ERROR
-- "security_definer_view" no advisor — aceito e documentado por design.
-- ---------------------------------------------------------------------
create view public.v_ranking as
select
  pr.id as user_id,
  pr.nome_completo,
  coalesce(sum(p.pontos), 0) as pontos_total,
  count(*) filter (where p.pontos = 3) as placares_exatos,
  count(*) filter (where p.pontos = 1) as acertos_vencedor,
  rank() over (order by coalesce(sum(p.pontos), 0) desc) as posicao
from public.profiles pr
left join public.predictions p on p.user_id = pr.id
where pr.perfil = 'participante' and pr.ativo
group by pr.id, pr.nome_completo;

create view public.v_match_prediction_distribution as
select
  match_id,
  gols_selecao_1,
  gols_selecao_2,
  count(*) as quantidade
from public.predictions
group by match_id, gols_selecao_1, gols_selecao_2;

create view public.v_match_accuracy as
select
  m.id as match_id,
  m.selecao_1,
  m.selecao_2,
  m.etapa,
  count(p.id) as total_palpites,
  count(*) filter (where p.pontos = 3) as placares_exatos,
  count(*) filter (where p.pontos >= 1) as acertos_vencedor
from public.matches m
left join public.predictions p on p.match_id = m.id
where m.status = 'Finalizado'
group by m.id, m.selecao_1, m.selecao_2, m.etapa;

-- ---------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.matches enable row level security;
alter table public.predictions enable row level security;
alter table public.audit_log enable row level security;

-- profiles: cada usuário vê/edita o próprio perfil; administradores veem/editam todos
create policy profiles_select on public.profiles
for select to authenticated
using ( (select auth.uid()) = id or (select public.is_admin()) );

create policy profiles_update on public.profiles
for update to authenticated
using ( (select auth.uid()) = id or (select public.is_admin()) )
with check ( (select auth.uid()) = id or (select public.is_admin()) );

-- matches: leitura liberada para autenticados; escrita só admin
create policy matches_select_all on public.matches
for select to authenticated
using ( true );

create policy matches_insert_admin on public.matches
for insert to authenticated
with check ( (select public.is_admin()) );

create policy matches_update_admin on public.matches
for update to authenticated
using ( (select public.is_admin()) )
with check ( (select public.is_admin()) );

create policy matches_delete_admin on public.matches
for delete to authenticated
using ( (select public.is_admin()) );

-- predictions: dono gerencia o próprio palpite enquanto o jogo não começou;
-- administradores gerenciam tudo (correções históricas)
create policy predictions_select on public.predictions
for select to authenticated
using ( (select auth.uid()) = user_id or (select public.is_admin()) );

create policy predictions_insert on public.predictions
for insert to authenticated
with check (
  (
    (select auth.uid()) = user_id
    and exists (
      select 1 from public.matches m
      where m.id = match_id and m.data_hora > now()
    )
  )
  or (select public.is_admin())
);

create policy predictions_update on public.predictions
for update to authenticated
using (
  (
    (select auth.uid()) = user_id
    and exists (
      select 1 from public.matches m
      where m.id = match_id and m.data_hora > now()
    )
  )
  or (select public.is_admin())
)
with check ( (select auth.uid()) = user_id or (select public.is_admin()) );

create policy predictions_delete_admin on public.predictions
for delete to authenticated
using ( (select public.is_admin()) );

-- audit_log: somente admin
create policy audit_log_admin_all on public.audit_log
for all to authenticated
using ( (select public.is_admin()) )
with check ( (select public.is_admin()) );

-- ---------------------------------------------------------------------
-- Grants (acesso somente para authenticated; anon não acessa nada)
-- ---------------------------------------------------------------------
grant usage on schema public to authenticated;

grant select, update on public.profiles to authenticated;
grant select on public.matches to authenticated;
grant insert, update, delete on public.matches to authenticated;
grant select, insert, update on public.predictions to authenticated;
grant select, insert on public.audit_log to authenticated;

-- O Supabase concede ALL on tables/views em public para anon/authenticated por
-- default (default privileges). Para views "security definer" como estas, isso
-- vazaria os agregados para usuários não autenticados via Data API — revoga
-- tudo e concede apenas select para authenticated.
revoke all on public.v_ranking, public.v_match_prediction_distribution, public.v_match_accuracy from anon, authenticated, public;
grant select on public.v_ranking, public.v_match_prediction_distribution, public.v_match_accuracy to authenticated;

grant execute on function public.recalculate_all_rankings() to authenticated;
